#!/opt/homebrew/bin/python3

import requests, urllib3
from lib import color
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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

    print(color.style.NORMAL + "API call to " + color.style.GREEN + fqdn + color.style.NORMAL)
    print(color.style.NORMAL + "Call: " + color.style.GREEN + url + color.style.NORMAL)

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
