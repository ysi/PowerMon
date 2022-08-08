#!/opt/homebrew/bin/python3
from lib import connection, color, transportnodes, commands
import sys

def discovery(config):
    """
    discovery(config)
    function to discover all components in NSX
    Return a list of nodes object and the NSX session

    Args
    ----------
    config : yaml config dictionnay
    """
    discover_url = '/api/v1/transport-nodes'
    cluster_url = '/api/v1/cluster/status'

    # Create a list of Commands
    ListAllCmds = []
    # Loop inside Component in config file
    for key, node in config['Component'].items():
        if node['commands'] is None or len(node['commands']) == 0: break
        for cmdnode in node['commands']:
            cmd = commands.cmd(cmdnode['name'], cmdnode['type'], node['type'], cmdnode['polling'], cmdnode['call'], cmdnode['panelfunction'], cmdnode['datafunction'])
            
            if cmd not in ListAllCmds:
                ListAllCmds.append(cmd)
    # Get IPs Edge and collect NSX Manager Data through API
    # Connect to NSX and Get Transport Nodes
    try:
        # List of Edge IPs
        if config['Component']['Manager']['port'] is None or config['Component']['Manager']['port'] == '':
            url = config['Component']['Manager']['fqdn']
        else:
            url = config['Component']['Manager']['fqdn'] + ":" + str(config['Component']['Manager']['port'])

        print(color.style.RED + "==> " + color.style.NORMAL + "Connecting to NSX Manager " + color.style.GREEN + url + color.style.NORMAL + " and Getting Edge IPs")
        discover_json, code = connection.GetAPIGeneric('https://' + url + discover_url, config['Component']['Manager']['login'], config['Component']['Manager']['password'], False)
        cluster_json, code = connection.GetAPIGeneric('https://' + url + cluster_url, config['Component']['Manager']['login'], config['Component']['Manager']['password'], False)
        List_Nodes = []
        # NSX Manager Cluster
        if isinstance(cluster_json, dict):
            for member in cluster_json['detailed_cluster_status']['groups'][0]['members']:
                nsx_manager = transportnodes.TN(member['member_fqdn'])
                nsx_manager.ip_mgmt = member['member_ip']
                nsx_manager.uuid = member['member_uuid']
                nsx_manager.vip = config['Component']['Manager']['fqdn']
                nsx_manager.type = 'Manager'
                nsx_manager.login = config['Component']['Manager']['login']
                nsx_manager.password = config['Component']['Manager']['password']
                nsx_manager.port = config['Component']['Manager']['port']
                # Add Command in list of command for each component
                for key, value in config['Component'].items():
                    if nsx_manager.type == value['type']:
                        for cd in value['commands']:
                            List_Cmd = []
                            if len(cd['call']) > 1:
                                for i in cd['call']:
                                    if cd['polling'] not in nsx_manager.list_intervall_cmd: nsx_manager.list_intervall_cmd.append(cd['polling'])
                                    List_Cmd.append(commands.cmd(cd['name'], cd['type'], nsx_manager.type, cd['polling'], i, cd['panelfunction'], cd['datafunction']))
                                nsx_manager.cmd.append(List_Cmd)
                            else:
                                if cd['polling'] not in nsx_manager.list_intervall_cmd: nsx_manager.list_intervall_cmd.append(cd['polling'])
                                nsx_manager.cmd.append(commands.cmd(cd['name'], cd['type'], nsx_manager.type, cd['polling'], cd['call'][0], cd['panelfunction'], cd['datafunction']))

                # Add node in object command
                for cd in ListAllCmds:
                    if cd.nodetype == 'Manager':
                        cd.tn.append(nsx_manager)
                
                List_Nodes.append(nsx_manager)

        # NSX Edge Treatment
        if isinstance(discover_json, dict) and 'results' in discover_json and discover_json['result_count'] > 0:
            for node in discover_json['results']:
                tn = transportnodes.TN(node['display_name'])
                tn.ip_mgmt = node['node_deployment_info']['ip_addresses'][0]
                tn.type = node['node_deployment_info']['resource_type']
                tn.cmd = []
                # Add command
                for key, value in config['Component'].items():
                    if tn.type == value['type']:
                        for cd in value['commands']:
                            List_Cmd = []
                            if len(cd['call']) > 1:
                                for i in cd['call']:
                                    if cd['polling'] not in tn.list_intervall_cmd: tn.list_intervall_cmd.append(cd['polling'])
                                    List_Cmd.append(commands.cmd(cd['name'], cd['type'], tn.type, cd['polling'], i, cd['panelfunction'], cd['datafunction']))

                                tn.cmd.append(List_Cmd)
                            else:
                                if cd['polling'] not in tn.list_intervall_cmd: tn.list_intervall_cmd.append(cd['polling'])
                                tn.cmd.append(commands.cmd(cd['name'], cd['type'], tn.type, cd['polling'], cd['call'], cd['panelfunction'], cd['datafunction']))

                if node['node_deployment_info']['resource_type'] == 'EdgeNode':
                    tn.login = config['Component']['Edge']['login']
                    tn.password = config['Component']['Edge']['password']
                if node['node_deployment_info']['resource_type'] == 'HostNode':
                    tn.login = config['Component']['Host']['login']
                    tn.password = config['Component']['Host']['password']

                # Add node in object command
                for cd in ListAllCmds:
                    if cd.nodetype == tn.type:
                        cd.tn.append(nsx_manager)
                
                List_Nodes.append(tn)

        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(transportnodes.getComponentbyType('Manager',List_Nodes))) + " NSX Manager")
        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(transportnodes.getComponentbyType('EdgeNode',List_Nodes))) + " Edges")
        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(transportnodes.getComponentbyType('HostNode',List_Nodes))) + " Hosts")
        return List_Nodes, ListAllCmds
    except Exception as error:
        print(color.style.RED + "ERROR - discovery: " + color.style.NORMAL + str(error))
        print(color.style.RED + "ERROR - discovery: Can't connect to " + config['Component']['Manager']['fqdn'] + color.style.NORMAL + ' - ' + str(error))
        sys.exit()
