#!/opt/homebrew/bin/python3

import requests, urllib3, sys, logging, pprint
from lib import color, connection, tools
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from threading import current_thread
from fabric import Connection, ThreadingGroup


def GetAPIGeneric(url, login, password, timeout=60, debug=False, Component='', description=''):
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
    loginfo = color.style.RED + "==> " + color.style.NORMAL + Component + " - " + description + " - " + color.style.GREEN + "Ok" + color.style.NORMAL
    try:
        resultJSON = {}
        result =  requests.get(url, headers=headers, auth=(login, password), verify=False, timeout=timeout)
        if result.status_code == 200:
            if debug:
                logging.info(loginfo)
            resultJSON = result.json()
        return resultJSON, result.status_code
    
    except requests.exceptions.RequestException as error:
        print(color.style.RED + "ERROR in API call: " + url + color.style.NORMAL)
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
    loginfo = color.style.RED + "==> " + color.style.NORMAL + Component + " - " + description + " - " + color.style.GREEN + "Ok" + color.style.NORMAL
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
        print(color.style.RED + "ERROR in API call: " + url + color.style.NORMAL)
        logging.debug(str(error))
        raise SystemExit(error)

def sendCommand(tn, cd, SSHnodesconnect=None):
    """
    sendCommand(cmd, config, SSHnodesconnect)
    Send a command and return the result
    Parameters
    ----------
    tn (obj): host object
    cd (obj): command object
    SSHnodesconnect (Fabric connection object)
    """
    loginfo = current_thread().name + color.style.RED + " ==> " + color.style.NORMAL + "Sending command on " + tn.ip_mgmt + " - " + cd.call + " - " + color.style.GREEN + "Ok" + color.style.NORMAL
    logdebug = current_thread().name + color.style.RED + " ==> " + color.style.NORMAL + "Sending command on " + tn.ip_mgmt + " - " + cd.call + " - " + color.style.GREEN + "Ok" + color.style.NORMAL
    if cd.type == 'SSH':
        if SSHnodesconnect is None:
            connect = Connection(host=tn.ip_mgmt, user=tn.login, connect_kwargs={'password': tn.password, 'look_for_keys':False})
            output = connect.run(cd.call + ' | json', hide=True, warn=True, timeout=cd.timeout)
            connect.close()
            if output.stderr == '':
                logging.info(loginfo)
                logging.debug(logdebug)
                return tools.formatResultSSH(output.stdout, False)
            else:
                print(color.style.RED + "ERROR: " + color.style.NORMAL + "Command '" + cd.call + "' on "  + tn.ip_mgmt + " is not working" + color.style.NORMAL)
                sys.exit()
        else:
            SSHconnections = []
            for nd in SSHnodesconnect:
                SSHconnections.append(Connection(host=nd.ip_mgmt, user=nd.login, connect_kwargs={'password': nd.password}))
            EdgeGroup = ThreadingGroup.from_connections(SSHconnections)
            output = EdgeGroup.run(cd.call + ' | json', hide=True, warn=True, timeout=cd.timeout)
            results = []
            for cnx, result in output.items():
                loginfo = current_thread().name + color.style.RED + " ==> " + color.style.NORMAL + "Sending '" + result.command + "' command on " +  cnx.host + " - " + color.style.GREEN + "Ok" + color.style.NORMAL
                if result.stderr == '':
                    tmp = {
                        'host': cnx.host,
                        'cmd': cd,
                        'result': tools.formatResultSSH(result.stdout, False)
                    }
                    results.append(tmp)
                    logging.info(loginfo)
                    logging.debug(logdebug)
                else:
                    print(color.style.RED + "ERROR: " + color.style.NORMAL + "Command '" + result.command + "' on "  + cnx.host + " is not working" + color.style.NORMAL)
            
            EdgeGroup.close()
            return results
    
    if cd.type == 'API':
        port = ''
        if str(tn.port) != '':
            port = ':' + str(tn.port)
        url = "https://" + tn.ip_mgmt + port + cd.call
        tn_json, code = connection.GetAPIGeneric(url, tn.login, tn.password, cd.timeout)
        if code == 200:
            logging.info(loginfo)
            logging.debug(logdebug)
            return tn_json
        else:
            print(color.style.RED + "ERROR: " + color.style.NORMAL + "Command '" + cd.call + "' on "  + tn.ip_mgmt + " is not working" + color.style.NORMAL)
            logging.debug(code)
            sys.exit()
