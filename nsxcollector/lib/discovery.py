#!/opt/homebrew/bin/python3
from lib import connection, color, transportnodes, commands, managers, routers, segments, tools
import sys, logging


class nsx_infra:
    def __init__(self, name, url_api):
        self.name = name
        self.url_api = url_api
        self.cluster = None
        self.managers = []
        self.nodes = []
        self.segments = []
        self.t0_routers = []
        self.t1_routers = []

    def viewInfra(self):
        self.cluster.viewCluster()
        for node in self.nodes:
            node.viewTN()
        for sg in self.segments:
            sg.viewSegment()
        for t0 in self.t0_routers:
            t0.viewRouter()
        for t1 in self.t1_routers:
            t1.viewRouter()

    def getCommandsPolling(self):
        Tab_Result = []
        # get command in Cluster
        for call in self.cluster.calls:
            if call.usedforPolling: Tab_Result.append(call)
        # get commands in all nodes
        for node in self.nodes:
            Tab_Result = Tab_Result + node.getIntCommandsPolling()
        # get commands in all segments
        for seg in self.segments:
            if seg.call.usedforPolling: Tab_Result.append(call)
        # get commands in all T0 routers
        for t0 in self.t0_routers:
            Tab_Result = Tab_Result + t0.getIntCommandsPolling()
        # get commands in all T1 routers
        for t1 in self.t1_routers:
            Tab_Result = Tab_Result + t1.getIntCommandsPolling()
        
        return Tab_Result

def discovery(config):
    """
    discover all components in NSX
    Return a list of nodes object and the NSX session

    Args
    ----------
    config : yaml config dictionnay
    """
    try:
        # Connect to NSX Manager
        if config['Component']['Manager']['port'] is None or config['Component']['Manager']['port'] == '':
            url = 'https://' + config['Component']['Manager']['fqdn']
        else:
            url = 'https://' + config['Component']['Manager']['fqdn'] + ":" + str(config['Component']['Manager']['port'])
        # Create infrastructure object
        infra = nsx_infra(config['General']['Name_Infra'].replace(' ', ''), url)
        logging.info(color.style.RED + "==> " + color.style.NORMAL + "Connecting to NSX Manager " + color.style.GREEN + url + color.style.NORMAL + " and Getting Edge IPs")
        # NSX Manager Cluster
        cluster_json, code = connection.GetAPIGeneric(url + config['Monitoring_calls']['nsx_cluster_status']['call'], config['Component']['Manager']['login'], config['Component']['Manager']['password'])
        if code == 200 and isinstance(cluster_json, dict):
            nsx_cluster = managers.Cluster(cluster_json['cluster_id'], config['Component']['Manager']['fqdn'])
            cluster_cmd = commands.cmd('nsx_cluster_status_call',config['Monitoring_calls']['nsx_cluster_status'], nsx_cluster, config['General']['api_timeout'])
            nsx_cluster.calls.append(cluster_cmd)
            backup_cmd = commands.cmd('nsx_cluster_backup_call',config['Monitoring_calls']['nsx_cluster_backup'], nsx_cluster, config['General']['api_timeout'])
            nsx_cluster.calls.append(backup_cmd)

            for member in cluster_json['detailed_cluster_status']['groups'][0]['members']:
                nsx_manager = managers.Manager(member['member_fqdn'])
                nsx_manager.ip_mgmt = member['member_ip']
                nsx_manager.uuid = member['member_uuid']
                nsx_manager.vip = config['Component']['Manager']['fqdn']
                nsx_manager.login = config['Component']['Manager']['login']
                nsx_manager.password = config['Component']['Manager']['password']
                nsx_manager.port = config['Component']['Manager']['port']
                nsx_cluster.members.append(nsx_manager)
                infra.cluster = nsx_cluster
        
        # NSX Edge and Host Treatment
        tn_json, code = connection.GetAPIGeneric(url + config['Monitoring_calls']['transport_nodes']['call'], config['Component']['Manager']['login'], config['Component']['Manager']['password'])
        if code == 200 and isinstance(tn_json, dict) and 'results' in tn_json and tn_json['result_count'] > 0:
            for node in tn_json['results']:
                logging.info(color.style.RED + "==> " + color.style.NORMAL + "Found Transport Node " + node['display_name'])
                tn = transportnodes.TN(node['display_name'], node['node_id'])
                config_call = config['Monitoring_calls']['transport_nodes']
                config_call['call'] = config_call['call'] + '/' + node['node_id']
                tn.ip_mgmt = node['node_deployment_info']['ip_addresses'][0]
                tn.type = node['node_deployment_info']['resource_type']
                tn_int_call = config['Monitoring_calls']['tn_interfaces']['call'].replace('TNID', tn.uuid)
                TN_config = {
                    'call': config['Monitoring_calls']['tn_status']['call'].replace('TNID', node['node_id']),
                    'polling': config['Monitoring_calls']['tn_interfaces']['polling']
                }
                tn.call = commands.cmd('tn_status_call',TN_config, tn, config['General']['api_timeout'])
                int_stats = dict(config['Monitoring_calls']['tn_interfaces_stats'])

                tn.discoverInterfaces(tn_int_call, int_stats,url,config['Component']['Manager']['login'], config['Component']['Manager']['password'], config['General']['api_timeout'])
                tn.tn_status_call = commands.cmd('tn_status_call',TN_config, tn, config['General']['api_timeout'])
                infra.nodes.append(tn)

        # T0 discovery
        t0_json, code, result = connection.GetAPIGeneric(url + config['Monitoring_calls']['t0']['call'], config['Component']['Manager']['login'], config['Component']['Manager']['password'], True)
        if code == 200 and isinstance(t0_json, dict) and 'results' in t0_json and t0_json['result_count'] > 0:
            for t0 in t0_json['results']:
                logging.info(color.style.RED + "==> " + color.style.NORMAL + "Found T0 " + t0['display_name'])
                rtrT0 = routers.Router(t0['display_name'], t0['id'], t0['unique_id'])
                rtrT0.type = t0['resource_type']
                rtrT0.ha_mode = t0['ha_mode']
                rtrT0.failover_mode = t0['failover_mode']
                rtrT0_config = {
                    'call': config['Monitoring_calls']['t0']['call'].replace('RTRID', rtrT0.id),
                    'polling': config['Monitoring_calls']['t0_interfaces']['polling']
                }
                int_stats = dict(config['Monitoring_calls']['t0_interfaces_stats'])
                rtrT0.call = commands.cmd('t0_call',rtrT0_config, rtrT0, config['General']['api_timeout'])
                rtrT0.getLocalService(url,config['Monitoring_calls']['t0_localservice']['call'],config['Component']['Manager']['login'], config['Component']['Manager']['password'])
                rtrT0.discoverInterfaces(config['Monitoring_calls']['t0_interfaces']['call'], int_stats,url,config['Component']['Manager']['login'], config['Component']['Manager']['password'], config['General']['api_timeout'])
                infra.t0_routers.append(rtrT0)

        # T1 discovery
        t1_json, code = connection.GetAPIGeneric(url + config['Monitoring_calls']['t1']['call'], config['Component']['Manager']['login'], config['Component']['Manager']['password'])
        if code == 200 and isinstance(t1_json, dict) and 'results' in t1_json and t1_json['result_count'] > 0:
            for t1 in t1_json['results']:
                logging.info(color.style.RED + "==> " + color.style.NORMAL + "Found T1 " + t1['display_name'])
                rtrT1 = routers.Router(t1['display_name'], t1['id'], t1['unique_id'])
                rtrT1.ha_mode = t1['ha_mode']
                rtrT1.type = t1['resource_type']
                rtrT1.failover_mode = t1['failover_mode']
                rtrT1_config = {
                    'call': config['Monitoring_calls']['t1']['call'].replace('RTRID', rtrT0.id),
                    'polling': config['Monitoring_calls']['t1_interfaces']['polling']
                }
                int_stats = dict(config['Monitoring_calls']['t0_interfaces_stats'])
                rtrT1.call = commands.cmd('t1_call',rtrT1_config, rtrT1, config['General']['api_timeout'])
                rtrT1.getLocalService(url,config['Monitoring_calls']['t1_localservice']['call'],config['Component']['Manager']['login'], config['Component']['Manager']['password'])
                rtrT1.discoverInterfaces(config['Monitoring_calls']['t1_interfaces']['call'], int_stats,url,config['Component']['Manager']['login'], config['Component']['Manager']['password'], config['General']['api_timeout'])
                infra.t1_routers.append(rtrT1)

        # Segments discovery
        segment_json, code = connection.GetAPIGeneric(url + config['Monitoring_calls']['segments']['call'], config['Component']['Manager']['login'], config['Component']['Manager']['password'])
        if code == 200 and isinstance(segment_json, dict) and 'results' in segment_json and segment_json['result_count'] > 0:
            for seg in segment_json['results']:
                logging.info(color.style.RED + "==> " + color.style.NORMAL + "Found Segment " + seg['display_name'])
                SG = segments.Segment(seg['display_name'], seg['id'], seg['unique_id'])
                SG.connectivity = seg['advanced_config']['connectivity']
                SG.admin_state = seg['admin_state']
                SG_config = config['Monitoring_calls']['segments']
                SG_config['call'] = SG_config['call'] + '/' + seg['display_name']
                SG.type = seg['type']
                if 'vlan_ids' in seg:
                    SG.vlan_ids = seg['vlan_ids']
                SG.call = commands.cmd('segment_call',SG_config, SG, config['General']['api_timeout'])
                infra.segments.append(SG)


        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(infra.cluster.members)) + " NSX Manager(s)")
        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(transportnodes.getComponentbyType('EdgeNode',infra.nodes))) + " Edge(s)")
        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(transportnodes.getComponentbyType('HostNode',infra.nodes))) + " Host(s)")
        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(infra.t0_routers)) + " T0 Router(s)")
        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(infra.t1_routers)) + " T1 Router(s)")
        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(infra.segments)) + " Segment(s)")
        return infra
    except Exception as error:
        print(color.style.RED + "ERROR - discovery: " + color.style.NORMAL + str(error))
        print(color.style.RED + "ERROR - discovery: Can't connect to " + config['Component']['Manager']['fqdn'] + color.style.NORMAL + ' - ' + str(error))
        sys.exit()

def getCommandListbyPooling(CommandList):
    List_Result = []
    intervalList = []
    # create list of interval
    for cmd in CommandList:
        if cmd.polling not in intervalList:
            intervalList.append(cmd.polling)

    for interval in intervalList:
        List_tmp = []
        for cmd in CommandList:
            if cmd.polling == interval:
                List_tmp.append(cmd)

        List_Result.append(List_tmp)

    return List_Result