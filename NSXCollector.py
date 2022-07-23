#!/opt/homebrew/bin/python3
# coding: utf8
#
# -------------------------------------------------------------------------
# PowerMon                                        
# -------------------------------------------------------------------------
# Utilisation:
# './NSXCollector.py'
#
# -------------------------------------------------------------------------
# |  Version History                                                      |
# -------------------------------------------------------------------------
# version=0.1
# version_date='22/08/2022'
#
# 0.1: Version initiale

import pprint
from lib import edgeconnection
from lib import managerconnection
from lib import tools

class style:
    RED = '\33[31m'
    ORANGE = '\33[33m'
    GREEN = '\33[32m'
    NORMAL = '\033[0m'


print("Welcome to PowerMon")
try:
    # Get IPs Edge and collect NSX Manager Data through API
    # read config file
    config = tools.readYML('./config/config.yml')
    session = managerconnection.ConnectNSX([config['Manager']['login'], config['Manager']['password'], 'AUTH'])
    auth_list = [config['Manager']['login'], config['Manager']['password'], 'AUTH']
    tn_json = managerconnection.GetAPI(session[0], config['Manager']['fqdn'] + ":" + str(config['Manager']['port']),'/api/v1/transport-nodes', auth_list)

    # List of Edge IPs
    List_Edge_IPs = []
    if isinstance(tn_json, dict) and 'results' in tn_json and tn_json['result_count'] > 0: 
        for node in tn_json['results']:
            if node['node_deployment_info']['resource_type'] == 'EdgeNode':
                List_Edge_IPs.append(node['node_deployment_info']['ip_addresses'][0])

    # Get All informations for NSX Manager
    NSXManager_Datas = []
    for api in config['Manager']['api']:
        result = managerconnection.GetAPI(session[0], config['Manager']['fqdn'] + ":" + str(config['Manager']['port']),api, auth_list)
        NSXManager_Datas.append(result)

    # Get All informations for Edge
    Edge_Datas = []
    for edg in List_Edge_IPs:
        edge = edgeconnection.getAllInfos('localhost', 23022)
        Edge_Datas.append(edge)
    
    pprint.pprint(NSXManager_Datas)
    pprint.pprint(Edge_Datas)


    
except Exception as e:
    print(style.RED + e + style.NORMAL)

print(style.GREEN + "Collect terminated" + style.NORMAL)
