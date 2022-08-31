#!/opt/homebrew/bin/python3

import requests, urllib3, logging
from lib import tools
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def GetAPIGeneric(url, login, password, jsonformat=False, timeout=60, debug=False, Component='', description=''):
    """
    GetAPIGeneric(url, login, password)
    Realize a get in REST/API depending if wants a Json reponse
    Basic authentication
    Parameters
    ----------
    Component (str): component for ouput
    description (str): description
    url (str): URL of the request without protocol and IP/FQDN
    login (str): login
    password (str): password
    """
    headers={
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }
    loginfo = tools.color.RED + "==> " + tools.color.NORMAL + Component + " - " + description + " - " + tools.color.GREEN + "Ok" + tools.color.NORMAL
    try:
        resultJSON = {}
        result =  requests.get(url, headers=headers, auth=(login, password), verify=False, timeout=timeout)
        if result.status_code == 200:
            if debug:
                logging.info(loginfo)
            resultJSON = result.json()
        if jsonformat:
            return resultJSON, result.status_code, result
        else:
            return resultJSON, result.status_code

    
    except requests.exceptions.RequestException as error:
        print(tools.color.RED + "ERROR in API call: " + url + tools.color.NORMAL)
        logging.debug(str(error))
        raise SystemExit(error)

def PostAPIGeneric(url, login, password, body, debug=False, Component='', description=''):
    """
    PostAPIGeneric(protocol, fqdn, url, login, password, body)
    Realize a POST in REST/API depending if wants a Json reponse
    Basic authentication
    Parameters
    ----------
    Component (str): component for ouput
    description (str): description
    url (str): URL of the request without protocol and IP/FQDN
    login (str): login
    password (str): password
    body (dict): body of the request
    """
    headers={
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }
    loginfo = tools.color.RED + "==> " + tools.color.NORMAL + Component + " - " + description + " - " + tools.color.GREEN + "Ok" + tools.color.NORMAL
    try:
        result =  requests.post(url, json=body, headers=headers, auth=(login, password), verify=False)
        if result.status_code == 200:
            if debug:
                logging.info(loginfo)
            resultJSON = result.json()
            return resultJSON
        else:
            logging.debug(result.status_code)
            return result.status_code
    
    except requests.exceptions.RequestException as error:
        print(tools.color.RED + "ERROR in API call: " + url + tools.color.NORMAL)
        logging.debug(str(error))
        raise SystemExit(error)
