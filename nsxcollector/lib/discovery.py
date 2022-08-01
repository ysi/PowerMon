#!/opt/homebrew/bin/python3
from lib import connection, color, transportnodes

def discovery(config):
    """
    discovery(config)
    function to discover all components in NSX
    Return a list of nodes object and the NSX session

    Args
    ----------
    config : yaml config dictionnay
    """
    url = '/api/v1/transport-nodes'
    # Get IPs Edge and collect NSX Manager Data through API
    # Connect to NSX and Get Transport Nodes
    session = connection.ConnectNSX([config['Manager']['login'], config['Manager']['password'], 'AUTH'])
    auth_list = [config['Manager']['login'], config['Manager']['password'], 'AUTH']
    tn_json = connection.GetAPI(session[0], config['Manager']['fqdn'] + ":" + str(config['Manager']['port']), url, auth_list)
    # List of Edge IPs
    print(color.style.RED + "==> " + color.style.NORMAL + "Connecting to NSX Manager " + color.style.GREEN + config['Manager']['fqdn'] + color.style.NORMAL + " and Getting Edge IPs")
    List_Nodes = []
    nsx_manager = transportnodes.TN(config['Manager']['fqdn'])
    nsx_manager.ip_mgmt = config['Manager']['fqdn']
    nsx_manager.type = 'Manager'
    nsx_manager.login = config['Manager']['login']
    nsx_manager.password = config['Manager']['password']
    nsx_manager.auth = auth_list
    nsx_manager.port = config['Manager']['port']
    nsx_manager.cmd = []
    List_Nodes.append(nsx_manager)
    if isinstance(tn_json, dict) and 'results' in tn_json and tn_json['result_count'] > 0: 
        for node in tn_json['results']:
            tn = transportnodes.TN(node['display_name'])
            tn.ip_mgmt = node['node_deployment_info']['ip_addresses'][0]
            tn.type = node['node_deployment_info']['resource_type']
            tn.cmd = []
            if node['node_deployment_info']['resource_type'] == 'EdgeNode':
                tn.login = config['Edge']['login']
                tn.password = config['Edge']['password']
            if node['node_deployment_info']['resource_type'] == 'HostNode':
                tn.login = config['Host']['login']
                tn.password = config['Host']['password']

            List_Nodes.append(tn)

    print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(transportnodes.getEdge(List_Nodes))) + " Edges")
    print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(transportnodes.getHost(List_Nodes))) + " Hosts")
    return List_Nodes, session
