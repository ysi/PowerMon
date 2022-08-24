#!/opt/homebrew/bin/python3

import yaml, sys, json, logging, jinja2, os
import lib
from dotenv.main import dotenv_values
from .influxdb import influxdb


def json_extract(obj, key):
    """Recursively fetch values from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values

def renderPanel(templatename, parameters):
    """
    Render panel from template j2 file
    Parameters
    ----------
    templatename (str): Name of the panel
    parameters Name of YAML file
    """
    template_file = templatename + ".j2"
    try:
        templateLoader = jinja2.FileSystemLoader(searchpath="./grafana")
        templateEnv = jinja2.Environment(loader=templateLoader, trim_blocks=True, lstrip_blocks=True)
        template = templateEnv.get_template(template_file)
        paneljson = template.render(parameters)  # this is where to put args to the template renderer
        json_render = json.loads(paneljson)
        logging.debug(json_render)
        return json_render
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        print(lib.color.style.RED + "ERROR: " + lib.color.style.NORMAL + "Error templating ")
        sys.exit()


def readYML(YAML_CFG_FILE):
    """
    readYML(YAML_CFG_FILE)
    Read a YAML File and return Dictionnary
    Returns
    ----------
    Dictionnary of Yaml information
    Parameters
    ----------
    YAML_CFG_FILE : Str
        Name of YAML file
    """
    # Open and treatment of a YAML config file
    try:
        with open(YAML_CFG_FILE, 'r') as ymlfile:
            YAML_DICT = yaml.load(ymlfile, Loader=yaml.FullLoader)
            if len(YAML_DICT['Component']) == 0:
                print(lib.color.style.RED + YAML_CFG_FILE + ": error - no components in section: Component" + lib.color.style.NORMAL)
                sys.exit(1)
            # Check if YAML file is good.
            for key, value in YAML_DICT.items():
                # Check Component Section
                if key == 'Component':
                    for tp, node in YAML_DICT['Component'].items():
                        # Check Manager info
                        if tp == 'Manager' and (node['fqdn'] == '' or node['fqdn'] is None or node['login'] == '' or node['login'] is None or node['password'] == '' or node['password'] is None or node['type'] == '' or node['type'] is None):
                            print(lib.color.style.RED + YAML_CFG_FILE + ": error - empty value in section: " + tp + lib.color.style.NORMAL)
                            sys.exit(1)
                        if tp == 'Edge' and (node['login'] == '' or node['login'] is None or node['password'] == '' or node['password'] is None or node['type'] == '' or node['type'] is None):
                            print(lib.color.style.RED + YAML_CFG_FILE + ": error - empty value in section: "  + tp + lib.color.style.NORMAL)
                            sys.exit(1)
                        if tp == 'Host' and (node['login'] == '' or node['login'] is None or node['password'] == '' or node['password'] is None or node['type'] == '' or node['type'] is None):
                            print(lib.color.style.RED + YAML_CFG_FILE + ": error - empty value in section: "  + tp + lib.color.style.NORMAL)
                            sys.exit(1)
            return YAML_DICT
    except Exception as e:
        print(lib.color.style.RED + YAML_CFG_FILE + ": error to read YAML config file" + lib.color.style.NORMAL)
        sys.exit(1)


def readENV(args):
    """
    Read the environment file
    Returns
    ----------
    a dictionary of the environement file
    """
    if args.standalone:
        try:
            envjson = dotenv_values("../.env")
            return envjson
        except:
            print(lib.color.style.RED + "ERROR: error to read .env file" + lib.color.style.NORMAL)
    else:
        envjson = {
            'INFLUXDB_DOCKER_CONTAINER_NAME': os.getenv('INFLUXDB_DOCKER_CONTAINER_NAME'),
            'INFLUXDB_NAME':os.getenv('INFLUXDB_NAME'),
            'INFLUXDB_PORT':os.getenv('INFLUXDB_PORT'),
            'INFLUXDB_DB':os.getenv('INFLUXDB_DB'),
            'INFLUXDB_ADMIN_USER':os.getenv('INFLUXDB_ADMIN_USER'),
            'INFLUXDB_ADMIN_PASSWORD':os.getenv('INFLUXDB_ADMIN_PASSWORD'),
            'INFLUXDB_ORG':os.getenv('INFLUXDB_ORG'),
            'INFLUXDB_TOKEN':os.getenv('INFLUXDB_TOKEN'),
            'GRAFANA_DOCKER_CONTAINER_NAME':os.getenv('GRAFANA_DOCKER_CONTAINER_NAME'),
            'GRAFANA_ADMIN_USER':os.getenv('GRAFANA_ADMIN_USER'),
            'GRAFANA_ADMIN_PASSWORD':os.getenv('GRAFANA_ADMIN_PASSWORD'),
            'GRAFANA_NAME':os.getenv('GRAFANA_NAME'),
            'GRAFANA_PORT':os.getenv('GRAFANA_PORT'),
        }
        return envjson

    # Load .env file

def copyConfigCall(configcall, TNID_str="", TNID="", LSID_str="", LSID="", INTID_str="", INTID=""):
    call = configcall['call'].replace(TNID_str, TNID).replace(LSID_str, LSID).replace(INTID_str, INTID)
    copycall = {
        'call': call,
        'polling': configcall['polling'],
    }
    # Add key only if it's present
    if 'influxdbfunction' in configcall:
        copycall['influxdbfunction'] = configcall['influxdbfunction']  
    return copycall

def get_recursively(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.items():

        if key == field:
            fields_found.append({key: value})

        elif isinstance(value, dict):
            results = get_recursively(value, field)
            for result in results:
                fields_found.append({key: result})

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = get_recursively(item, field)
                    for another_result in more_results:
                        fields_found.append({key: another_result})

    return fields_found