#!/opt/homebrew/bin/python3

import yaml, sys, json, os, pprint
from lib import color
from dotenv.main import dotenv_values


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
            return YAML_DICT
    except Exception as e:
        print(color.style.RED + YAML_CFG_FILE + " not found in directory" + color.style.NORMAL)
        print(color.style.ORANGE + e + color.style.NORMAL)
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