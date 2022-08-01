#!/opt/homebrew/bin/python3

import requests, urllib3, json, pprint
from lib import color, connection, influxdb, tools
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from threading import current_thread
from lib.formatDatas import processCPU, processINT


def getAPIData(session, cmd, flagwrite, influxapi=()):
    """
    getAPIData(list)
    Get Data from a API call

    Args
    ----------
    session : session NSX
    auth : list with NSX/edge credentials
    cmd : url of API request
    influxapi : list of the connection with influxdb
    flagwrite: boolean to enable or not to write in influxdb
    """
    print(current_thread().name + ": On " + color.style.GREEN + cmd.tn[0].ip_mgmt + color.style.NORMAL + " - Call " + color.style.GREEN + ', '.join(cmd.call) + color.style.NORMAL)
    # Get Data from a API call
    for call in cmd.call:
        result = connection.GetAPI(session[0], cmd.tn[0].ip_mgmt + ":" + str(cmd.tn[0].port),call, cmd.tn[0].auth)
        if isinstance(result, int):
            print(current_thread().name + color.style.RED + "ERROR in call + " + call + color.style.NORMAL + " - error " + result)
        elif(flagwrite):
            # Call format function of a call
            function_name = globals()[cmd.format_function]
            format_data = function_name(cmd.tn[0].ip_mgmt, result)
            influxdb.influxWrite(influxapi[0],influxapi[1], influxapi[2], format_data )


def getSSHData(EdgeGroup, cmd, influxapi=()):
    """
    getSSHData(list)
    Get Data from a SSH command

    Args
    ----------
    EdgeGroupgeGroup : group of NSX Edge
    cmd : list or object cmd in yaml file
    fcname : name of the function for format treatment
    flagwrite: boolean to enable or not to write in influxdb
    influxapi : list of the connection with influxdb
    """            
    # Check if there is more than one command
    if len(cmd.call) > 1:
        for ed in EdgeGroup:
            print(current_thread().name + ": Sent on " + color.style.GREEN + ed.host + color.style.NORMAL + " - ssh commands " + color.style.GREEN + cmd.call[0] + color.style.NORMAL)
            
            output = ed.run(cmd.call[0] + ' | json', hide=True, warn=True)
            result_tmp = tools.formatResultSSH(output.stdout, False)

            for i in result_tmp:
                final_cmd = cmd.call[1].replace('ID', i['uuid'])
                print(current_thread().name + ": Sent on " + color.style.GREEN + ed.host + color.style.NORMAL + " - ssh commands " + color.style.GREEN + final_cmd + color.style.NORMAL)

                final_output = ed.run(final_cmd + ' | json', hide=True)
                final_result = tools.formatResultSSH(final_output.stdout, False)
                function_name = globals()[cmd.format_function]
                format_data = function_name(ed.host, final_result, True)
                influxdb.influxWrite(influxapi[0],influxapi[1], influxapi[2], format_data )


    # only one command
    else:
        for ed in EdgeGroup:
            print(current_thread().name + ": Sent on " + color.style.GREEN + ed.host + color.style.NORMAL + " - ssh commands " + color.style.GREEN + cmd.call[0] + color.style.NORMAL)
            output = EdgeGroup.run(cmd.call[0] + ' | json', hide=True)
            result_tmp = tools.formatResultSSH(output)


def ConnectNSX(auth_list):
    """
    ConnectNSX(list)
    Connection function to NSX. Can be by certifcates or by authentication.

    Returns
    ----------
    list with session object and connector object    
    Args
    ----------
    auth : list
        list must contain login/cert - password/key - Tag (AUTH or CERT)
    """
    if auth_list[2] == 'AUTH':
        session = requests.session()
        session.verify = False
        return [session,None]
    elif auth_list[2] == 'CERT':
        session = requests.session()
        session.verify = False
        session.cert = (auth_list[0], auth_list[1])
        return [session,None]
    else:
        print("Issue on authentication")
        exit(1)


def GetAPI(session,fqdn, url, auth_list):
    """
    GetAPI(session, url, auth_list, reponse_type)
    Realize a get in REST/API depending if wants a Json reponse, with authentication with certification or login
    Parameters
    ----------
    session : object
        session obejct created by ConnectNSX
    url : str
        URL of the request without protocol and IP/FQDN
    auth_list : list
        list with authentication parameters (login/cert, password/key, AUTH or CERT)
    cursor : str
        cursor REST/API in case of pagination
    result_list : list
        for recursive purpose for pagination
    """
    try:
        if auth_list[2] == 'AUTH':
            result =  session.get('https://' + fqdn + url, auth=(auth_list[0], auth_list[1]), verify=session.verify)

        if auth_list[2] == 'CERT':
            result =  requests.get('https://' + fqdn + url, headers={'Content-type': 'application/json'}, cert=(auth_list[0], auth_list[1]), verify=session.verify)

        if result.status_code == 200:
            resultJSON = result.json()
            if 'result_count' in resultJSON: count = resultJSON['result_count']

            return resultJSON

        else: 
            return result.status_code
    
    except requests.exceptions.RequestException as error:
        print(color.style.RED + "ERROR in API call: " + url + color.style.NORMAL + " : " + str(error))
        raise SystemExit(error)

def GetAPIGeneric(url, login, password, debug=True, Component='', description=''):
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
    try:
        resultJSON = {}
        result =  requests.get(url, headers=headers, auth=(login, password), verify=False)
        if result.status_code == 200:
            if debug:
                print(color.style.RED + "==> " + color.style.NORMAL + Component + " - " + description + " - " + color.style.GREEN + "Ok" + color.style.NORMAL)
            resultJSON = result.json()
        return resultJSON, result.status_code
    
    except requests.exceptions.RequestException as error:
        print(color.style.RED + "ERROR in API call: " + url + color.style.NORMAL + " : " + str(error))
        raise SystemExit(error)

def PostAPIGeneric(url, login, password, body, debug=True, Component='', description=''):
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
    try:
        result =  requests.post(url, json=body, headers=headers, auth=(login, password), verify=False)
        if result.status_code == 200:
            if debug:
                print(color.style.RED + "==> " + color.style.NORMAL + Component + " - " + description + " - " + color.style.GREEN + "Ok" + color.style.NORMAL)
            resultJSON = result.json()
            return resultJSON
        else: 
            return result.status_code
    
    except requests.exceptions.RequestException as error:
        print(color.style.RED + "ERROR in API call: " + url + color.style.NORMAL + " : " + str(error))
        raise SystemExit(error)
