#!/opt/homebrew/bin/python3

import requests, urllib3, sys, logging
from lib import color, connection, influxdb, tools
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from threading import current_thread
from lib.formatDatas import Edge_Int_Data, Manager_CPU_Process_Data, Manager_Cluster_Data
from fabric import Connection


def poolAPI(cmd, flagwrite, influxapi=()):
    print(current_thread().name + ": On " + color.style.GREEN + cmd.tn[0].ip_mgmt + color.style.NORMAL + " - Call " + color.style.GREEN + ', '.join(cmd.call) + color.style.NORMAL)


def getAPIData(cmd, flagwrite, influxapi=()):
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
    if cmd.tn[0].type == 'Manager' and cmd.tn[0].port != '':
        host_url  = cmd.tn[0].vip + ":" + cmd.tn[0].port
    else:
        host_url = cmd.tn[0].vip
    # Get Data from a API call

    logging.debug(cmd.call)
    for call in cmd.call:
        print(current_thread().name + ": On " + color.style.GREEN + cmd.tn[0].ip_mgmt + color.style.NORMAL + " - Call " + color.style.GREEN + ', '.join(cmd.call) + color.style.NORMAL)
        result, code = GetAPIGeneric('https://' + host_url + call, cmd.tn[0].login, cmd.tn[0].password, False)
        if code > 200:
            print(current_thread().name + color.style.RED + "ERROR in call + " + call + color.style.NORMAL + " - error " + result)
        elif flagwrite:
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

def sendCommand(tn, cd, config):
    """
    sendCommand(cmd, config)
    Send a command and return the result
    Parameters
    ----------
    tn (obj): host object
    cd (obj): command object
    config (dict): yaml configuration file
    """
    if cd.type == 'SSH':
        connect = Connection(host=tn.ip_mgmt, user=tn.login, connect_kwargs={'password': tn.password})
        output = connect.run(cd.call + ' | json', hide=True, warn=True)
        if output.stderr == '':
            print(color.style.RED + "==> " + color.style.NORMAL + "Testing command on " + tn.ip_mgmt + " - " + cd.call + " - " + color.style.GREEN + "Ok" + color.style.NORMAL)
            result_json = tools.formatResultSSH(output.stdout, False)
            return result_json
        else:
            print(color.style.RED + "ERROR: " + color.style.NORMAL + "Command " + cd.call + " in "  + tn.ip_mgmt + " is not working" + color.style.NORMAL)
            sys.exit()
    if cd.type == 'API':
        port = ''
        if str(config['Component']['Manager']['port']) != '':
            port = ':' + str(config['Component']['Manager']['port'])
        url = "https://" + config['Component']['Manager']['fqdn'] + port + cd.call
        tn_json, code = connection.GetAPIGeneric(url, config['Component']['Manager']['login'], config['Component']['Manager']['password'], False)
        if code == 200:
            print(color.style.RED + "==> " + color.style.NORMAL + "Testing command on " + tn.ip_mgmt + " - " + cd.call + " - " + color.style.GREEN + "Ok" + color.style.NORMAL)
            return tn_json
        else:
            print(color.style.RED + "ERROR: " + color.style.NORMAL + "Command " + cd.call + " in "  + tn.ip_mgmt + " is not working" + color.style.NORMAL)
            sys.exit()


def sendSSHCommand(edge, cmd, precommand=False, writedb=False):
    """
    getSSHData(list)
    Get Data from a SSH command

    Args
    ----------
    edge : edge or group of NSX Edge Fabric connection
    cmd : list or object cmd in yaml file
    fcname : name of the function for format treatment
    flagwrite: boolean to enable or not to write in influxdb
    influxapi : list of the connection with influxdb
    """            
    # Check if there is more than one edge
    if isinstance(edge, list):
        for ed in edge:
            print(current_thread().name + ": Sent on " + color.style.GREEN + ed.host + color.style.NORMAL + " - ssh commands " + color.style.GREEN + cmd + color.style.NORMAL)
            output = ed.run(cmd.call + ' | json', hide=True, warn=True)
            return(tools.formatResultSSH(output.stdout, False))

    else:
        print(current_thread().name + ": Sent on " + color.style.GREEN + edge + color.style.NORMAL + " - ssh commands " + color.style.GREEN + cmd + color.style.NORMAL)
        output = edge.run(cmd.call + ' | json', hide=True, warn=True)
        return(tools.formatResultSSH(output.stdout, False))




# def ConnectNSX(auth_list):
#     """
#     ConnectNSX(list)
#     Connection function to NSX. Can be by certifcates or by authentication.

#     Returns
#     ----------
#     list with session object and connector object    
#     Args
#     ----------
#     auth : list
#         list must contain login/cert - password/key - Tag (AUTH or CERT)
#     """
#     if auth_list[2] == 'AUTH':
#         session = requests.session()
#         session.verify = False
#         return [session,None]
#     elif auth_list[2] == 'CERT':
#         session = requests.session()
#         session.verify = False
#         session.cert = (auth_list[0], auth_list[1])
#         return [session,None]
#     else:
#         print("Issue on authentication")
#         exit(1)


# def GetAPI(session,fqdn, url, auth_list):
#     """
#     GetAPI(session, url, auth_list, reponse_type)
#     Realize a get in REST/API depending if wants a Json reponse, with authentication with certification or login
#     Parameters
#     ----------
#     session : object
#         session obejct created by ConnectNSX
#     url : str
#         URL of the request without protocol and IP/FQDN
#     auth_list : list
#         list with authentication parameters (login/cert, password/key, AUTH or CERT)
#     cursor : str
#         cursor REST/API in case of pagination
#     result_list : list
#         for recursive purpose for pagination
#     """
#     try:
#         if auth_list[2] == 'AUTH':
#             result =  session.get('https://' + fqdn + url, auth=(auth_list[0], auth_list[1]), verify=session.verify)

#         if auth_list[2] == 'CERT':
#             result =  requests.get('https://' + fqdn + url, headers={'Content-type': 'application/json'}, cert=(auth_list[0], auth_list[1]), verify=session.verify)

#         if result.status_code == 200:
#             resultJSON = result.json()
#             if 'result_count' in resultJSON: count = resultJSON['result_count']

#             return resultJSON

#         else: 
#             return result.status_code
    
#     except requests.exceptions.RequestException as error:
#         print(color.style.RED + "ERROR in API call: " + url + color.style.NORMAL + " : " + str(error))
#         raise SystemExit(error)


