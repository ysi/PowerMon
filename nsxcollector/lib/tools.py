#!/opt/homebrew/bin/python3

import yaml, sys, json, logging, jinja2, pprint
from lib import color
from dotenv.main import dotenv_values
from jinja2 import PackageLoader

def renderPanel(panelname, parameters):
    tmp = panelname.replace(" ","-")
    panelname = tmp.lower()
    template_file = panelname + ".j2"
    try:
        templateLoader = jinja2.FileSystemLoader(searchpath="./grafana")
        templateEnv = jinja2.Environment(loader=templateLoader, trim_blocks=True, lstrip_blocks=True)
        template = templateEnv.get_template(template_file)
        paneljson = template.render(parameters)  # this is where to put args to the template renderer
        json_render = json.loads(paneljson)
        return json_render
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        print(color.style.RED + "ERROR: " + color.style.NORMAL + "Error templating ")
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
            if len(YAML_DICT['Thread']) < 3:
                print(color.style.RED + YAML_CFG_FILE + ": error - missing information in section: Thread" + color.style.NORMAL)
                sys.exit(1)
            if len(YAML_DICT['Component']) == 0:
                print(color.style.RED + YAML_CFG_FILE + ": error - no components in section: Component" + color.style.NORMAL)
                sys.exit(1)
            # Check if YAML file is good.
            for key, value in YAML_DICT.items():
                # Check Thread Section
                if key == 'Thread':
                    if value['type'] == '' or value['nb_thread'] == '' or value['polling'] == '':
                        print(color.style.RED + YAML_CFG_FILE + ": error - empty value in section: " + key + color.style.NORMAL)
                        sys.exit(1)

                # Check Component Section
                if key == 'Component':
                    for tp, node in YAML_DICT['Component'].items():
                        # Check Manager info
                        if tp == 'Manager' and (node['fqdn'] == '' or node['fqdn'] is None or node['login'] == '' or node['login'] is None or node['password'] == '' or node['password'] is None or node['type'] == '' or node['type'] is None):
                            print(color.style.RED + YAML_CFG_FILE + ": error - empty value in section: " + tp + color.style.NORMAL)
                            sys.exit(1)
                        if tp == 'Edge' and (node['login'] == '' or node['login'] is None or node['password'] == '' or node['password'] is None or node['type'] == '' or node['type'] is None):
                            print(color.style.RED + YAML_CFG_FILE + ": error - empty value in section: "  + tp + color.style.NORMAL)
                            sys.exit(1)
                        if tp == 'Host' and (node['login'] == '' or node['login'] is None or node['password'] == '' or node['password'] is None or node['type'] == '' or node['type'] is None):
                            print(color.style.RED + YAML_CFG_FILE + ": error - empty value in section: "  + tp + color.style.NORMAL)
                            sys.exit(1)
            return YAML_DICT
    except Exception as e:
        print(color.style.RED + YAML_CFG_FILE + ": error to read YAML config file" + color.style.NORMAL)
        sys.exit(1)


def formatResultSSH(output, all=True):

    if all:
        for r in output:
            connection = output[r]
            # run function return a string with \n. Need to erase \n from the string and convert it on a real json
            result = json.loads(connection.stdout.replace('\n', ''))
            return result

    else:
        result = json.loads(output.replace('\n', ''))
        return result

def readENV():
    # Load .env file
    envjson = dotenv_values('../.env')
    return envjson