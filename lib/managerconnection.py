#!/opt/homebrew/bin/python3

import pprint, requests, urllib3
from lib import sshcommand
from lib import tools
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class style:
    RED = '\33[31m'
    ORANGE = '\33[33m'
    GREEN = '\33[32m'
    NORMAL = '\033[0m'

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

    print(style.NORMAL + "API call to " + style.GREEN + fqdn + style.NORMAL)
    print(style.NORMAL + "Call: " + style.GREEN + url + style.NORMAL)

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


# def getEdgeIPs():
#     """
#     getEdgeIPs()
#     Get IPs of all Edge Nodes in NSX
#     Returns
#     ----------
#     List of IPs
#     """
#     Edges = []
#     # read config file
#     config = tools.readYML('./config/config.yml')

#     # Connect to Manager
#     sshconnect = sshcommand.connect(config['Manager']['fqdn'],config['Manager']['port'],config['Manager']['login'],config['Manager']['password'])
#     # Get list of Nodes
#     result = sshcommand.exec(sshconnect, 'get nodes', 'nsx')
#     for item in result:
#         # Take only nodes of type edge
#         if item['node_type_label'] == 'edg':
#             # Grab IP of each edge
#             edge_list = sshcommand.exec(sshconnect, 'get transport-node ' + item['uuid'] + ' status' , 'nsx')
#             for edg in edge_list:
#                 Edges.append(edg['Remote-Address'].split(':')[0])
                
#     return Edges



# def getAllInfos():
#     """
#     getAllInfos()
#     Get all informations based on list a commands in yaml config files
#     Returns
#     ----------
#     List of results
#     """
#     TotalResult = []

#     # read config file
#     config = tools.readYML('./config/config.yml')

#     # Connect to Manager
#     sshconnect = sshcommand.connect(config['Manager']['fqdn'],config['Manager']['port'],config['Manager']['login'],config['Manager']['password'])
#     # Loop in all commands
#     for item in config['Manager']['commands']:
#         result = sshcommand.exec(sshconnect, item, 'nsx')
#         TotalResult.append(result)
    
#     sshcommand.disconnect(sshconnect)
#     return TotalResult   
