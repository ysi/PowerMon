#!/opt/homebrew/bin/python3

import yaml
import sys

class style:
    RED = '\33[31m'
    ORANGE = '\33[33m'
    GREEN = '\33[32m'
    NORMAL = '\033[0m'

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
        print(style.RED + YAML_CFG_FILE + " not found in directory" + style.NORMAL)
        print(style.ORANGE + e + style.NORMAL)
        sys.exit(1)


