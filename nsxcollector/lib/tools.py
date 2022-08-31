#!/opt/homebrew/bin/python3

import yaml, sys, json, logging, jinja2, os
from dotenv.main import dotenv_values
from .influxdb import influxdb

class color:
    RED = '\33[31m'
    ORANGE = '\33[33m'
    GREEN = '\33[32m'
    NORMAL = '\033[0m'


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
        print(color.RED + "ERROR: " + color.NORMAL + "Error templating ")
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
                print(color.RED + YAML_CFG_FILE + ": error - no components in section: Component" + color.NORMAL)
                sys.exit(1)
            # Check if YAML file is good.
            for key, value in YAML_DICT.items():
                # Check Component Section
                if key == 'Component':
                    for tp, node in YAML_DICT['Component'].items():
                        # Check Manager info
                        if tp == 'Manager' and (node['fqdn'] == '' or node['fqdn'] is None or node['login'] == '' or node['login'] is None or node['password'] == '' or node['password'] is None or node['type'] == '' or node['type'] is None):
                            print(color.RED + YAML_CFG_FILE + ": error - empty value in section: " + tp + color.NORMAL)
                            sys.exit(1)
                        if tp == 'Edge' and (node['login'] == '' or node['login'] is None or node['password'] == '' or node['password'] is None or node['type'] == '' or node['type'] is None):
                            print(color.RED + YAML_CFG_FILE + ": error - empty value in section: "  + tp + color.NORMAL)
                            sys.exit(1)
                        if tp == 'Host' and (node['login'] == '' or node['login'] is None or node['password'] == '' or node['password'] is None or node['type'] == '' or node['type'] is None):
                            print(color.RED + YAML_CFG_FILE + ": error - empty value in section: "  + tp + color.NORMAL)
                            sys.exit(1)
            return YAML_DICT
    except Exception as e:
        print(color.RED + YAML_CFG_FILE + ": error to read YAML config file" + color.NORMAL)
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
            print(color.RED + "ERROR: error to read .env file" + color.NORMAL)
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

def readPanelsConfig(panelconfig_path):
    # Read all yml and j2 file and construct a dict for each panels
    # this dict will be on infra object
    list_content_folder = os.listdir(panelconfig_path) # returns list
    List_config_panel = []
    for item in list_content_folder:
        config_panel = { 'name': item } 
        if os.path.isdir(panelconfig_path + '/' + item):
            # one panel config
            list_panel_folder_content = os.listdir(panelconfig_path + '/' + item)
            for file in list_panel_folder_content:
                if file.endswith('.j2'): 
                    config_panel['j2_path'] = panelconfig_path + '/' + item + '/' + file
                if file.endswith('.yml') or file.endswith('.yaml'):
                    config_panel['yml_path'] = panelconfig_path + '/' + item + '/' + file
                    with open(config_panel['yml_path'], 'r') as ymlfile:
                        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
                        for k, v in cfg.items():
                            config_panel[k] = v
            
        List_config_panel.append(config_panel)
    
    return List_config_panel
