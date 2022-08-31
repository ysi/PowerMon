#!/opt/homebrew/bin/python3
from lib import tools, connection
from lib.nsxinfra import fabric, commands, transportnodes, segments, routers, node
import logging, sys, copy

class nsx_infra:
    def __init__(self, name, url_api, api_timeout, login, password, federation):
        self.name = name
        self.configpanels = ""
        self.url_api = url_api
        self.api_timeout = api_timeout
        self.login = login
        self.password = password
        self.version = ""
        self.site = ""
        self.domain = ""
        if federation:
            self.federation = "Global"
        else:
            self.federation = 'Infra'
        self.enforcement = ""
        self.discovercalls = []
        self.cluster = None
        self.nodes = []
        self.segments = []
        self.tz = []
        self.routers = []
        self.calls = []
        self.swagger = None
        self.commandfile = ""
        # For testing
        self.testnodes = []


    def viewInfra(self):
        print('Infra:')
        print(' - name: ' + self.name)
        print(' - url_api: ' + self.url_api)
        print(' - api_timeout: ' + str(self.api_timeout))
        print(' - login: ' + self.login)
        print(' - password: ' + self.password)
        print(' - site: ' + self.site)
        print(' - federation: ' + self.federation)
        print(' - enforcement: ' + self.enforcement)
        print(' - domain: ' + self.domain)
        print(' - configpanels: ' + self.configpanels)
        print(' - commandfile: ' + self.commandfile)

    def viewALLInfra(self):
        self.viewInfra()
        self.cluster.viewCluster()
        for node in self.nodes:
            node.viewTN()
        for rtr in self.routers:
            rtr.viewRouter()
        for sg in self.segments:
            sg.viewSegment()

    def viewInfraCommands(self):
        for i in self.calls:
            i.viewCommand()

    def findComponent(self, name):
        for node in self.nodes:
            if node.name == name:
                return node

        for rtr in self.routers:
            if rtr.name == name:
                return rtr
        
        return None


    def getGenInformations(self):
        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Getting general informations")
        for k, cmd in self.discovercalls.items():
            # Get general call
            if 'gen' in k:
                swagger_cmd = self.swagger.searchCommand(exact=True, name=cmd, scope=self.federation)
                if 'list_gen_enforcement' in k: url = swagger_cmd.call.replace("{siteid}", self.site)
                else: url = swagger_cmd.call
                json, code = connection.GetAPIGeneric(self.url_api + url, self.login, self.password)
                if code == 200 and isinstance(json, dict) and 'results' in json and json['result_count'] > 0:
                    if json['result_count'] == 1:
                        if 'domain' in k: self.domain = json['results'][0]['id']
                        if 'enforcement' in k: self.enforcement = json['results'][0]['id']
                        if 'site' in k: self.site = json['results'][0]['id']
                else:
                    print(tools.color.RED + "ERROR - Discovery: Can't access to " + url + tools.color.NORMAL + ' - HTTP error: ' + str(code))



    def addTransportZone(self):
        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Getting Transport Zones")
        cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls['list_tz'], scope=self.federation)
        url = cmd.call.replace('{siteid}', self.site).replace('{enforcementpointid}', self.enforcement)
        json, code = connection.GetAPIGeneric(self.url_api + url, self.login, self.password)
        if code == 200 and isinstance(json, dict) and 'results' in json and json['result_count'] > 0:
            for tz in json['results']:
                TZObject = fabric.Transport_Zone(tz['display_name'], tz['tz_type'])
                logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Found Transport Zone: " + TZObject.name)
                TZObject.id = tz['id']
                TZObject.path = tz['path']
                self.tz.append(TZObject)
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + url + tools.color.NORMAL + ' - HTTP error: ' + str(code))


    def addCluster(self):
        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Getting NSX Cluster")
        # NSX Manager Cluster
        cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls['read_cluster'], scope=self.federation)
        cluster_json, code = connection.GetAPIGeneric(self.url_api + cmd.call, self.login, self.password)
        if code == 200 and isinstance(cluster_json, dict):
            nsx_cluster = fabric.Cluster(cluster_json['cluster_id'])
            nsx_cluster.call = commands.cmd('cluster_status', self.discovercalls['read_cluster'], self.version, tags=['Polling'])
            self.calls.append(nsx_cluster.call)
            logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Found Cluster " + nsx_cluster.id)
            for member in cluster_json['detailed_cluster_status']['groups'][0]['members']:
                nsx_manager = fabric.Manager(member['member_fqdn'])
                nsx_manager.ip_mgmt = member['member_ip']
                nsx_manager.uuid = member['member_uuid']
                nsx_cluster.members.append(nsx_manager)
            
            self.cluster = nsx_cluster
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + cmd.call + tools.color.NORMAL + ' - HTTP error: ' + str(code))


    def addNodes(self):
        for k, cmdname in self.discovercalls.items():
            if k == 'list_t0' or k == 'list_t1' or k == 'list_tn':
                typenode = k.split('_')[1]
                cmd = self.swagger.searchCommand(exact=True, name=cmdname, scope=self.federation)
                print(cmd.__dict__)
                json, code = connection.GetAPIGeneric(self.url_api + cmd.call, self.login, self.password)
                if code == 200 and isinstance(json, dict) and 'results' in json and json['result_count'] > 0:
                    for nd in json['results']:
                        if typenode == 'tn': 
                            typeobj = nd['node_deployment_info']['resource_type']
                            id = nd['node_id']
                            ip_mgmt = nd['node_deployment_info']['ip_addresses'][0]
                        elif typenode == 't1': 
                            typeobj = nd['resource_type']
                            id = nd['id']
                            call_variable_id = '{tier1id}'
                        else:
                            typeobj = nd['resource_type']
                            id = nd['id']
                            call_variable_id = '{tier0id}'
                        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Found Node " + id + ' - ' + nd['display_name'])
                        nodeObj = node.node(nd['display_name'],id,typeobj)
                        nodeObj.call_variable_id = call_variable_id
                        nodeObj.viewNode()

    def addTN(self):
        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Getting Transport Nodes")
        # NSX Edge and Host Treatment
        cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls['list_tn'], scope=self.federation)
        tn_json, code = connection.GetAPIGeneric(self.url_api + cmd.call, self.login, self.password)
        if code == 200 and isinstance(tn_json, dict) and 'results' in tn_json and tn_json['result_count'] > 0:
            for node in tn_json['results']:
                logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Found Transport Node " + node['display_name'])
                tn = transportnodes.TN(node['display_name'], node['node_id'], node['node_deployment_info']['resource_type'])
                tn.ip_mgmt = node['node_deployment_info']['ip_addresses'][0]
                tn.call = commands.cmd('tn_status_call', cmd.call + '/' + tn.id, self.version, tags=['Polling'])
                self.calls.append(tn.call)
                tn.discoverInterfaces(self)
                self.nodes.append(tn)
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + cmd.call + tools.color.NORMAL + ' - HTTP error: ' + str(code))

    def addRouters(self, typeRTR):
        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Getting Routers (T0/T1)")
        # Router T0/T1 discovery
        cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls[typeRTR], scope=self.federation)
        json, code = connection.GetAPIGeneric(self.url_api + cmd.call, self.login, self.password)
        if code == 200 and isinstance(json, dict) and 'results' in json and json['result_count'] > 0:
            for rtr in json['results']:
                logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Found " + rtr['resource_type'] + " - " + rtr['display_name'])
                RTRObject = routers.Router(rtr['display_name'], rtr['id'], rtr['unique_id'], rtr['resource_type'])
                if RTRObject.type == 'Tier0': RTRObject.ha_mode = rtr['ha_mode']
                RTRObject.failover_mode = rtr['failover_mode']
                RTRObject.path = rtr['path']
                RTRObject.call = commands.cmd(typeRTR + '_status', cmd.call + '/' + RTRObject.id, self.version)
                self.calls.append(RTRObject.call)
                ls_cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls[typeRTR + '_localservice'], scope=self.federation)
                int_cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls[typeRTR + '_interface'], scope=self.federation)

                if RTRObject.type == 'Tier0': RTRObject.call_variable_id = '{tier0id}'
                else: RTRObject.call_variable_id = '{tier1id}'
                RTRObject.localservice = RTRObject.getLocalService(self, ls_cmd.call.replace(RTRObject.call_variable_id, RTRObject.id))
                # Add interfaces
                RTRObject.discoverInterfaces(self, int_cmd.call.replace(RTRObject.call_variable_id, RTRObject.id).replace('{localeserviceid}', RTRObject.localservice))
                # Get localservice
                self.routers.append(RTRObject)
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + cmd.call + tools.color.NORMAL + ' - HTTP error: ' + str(code))

    def addSegments(self):
        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Getting Segments")
        # Segments discovery
        cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls['list_segments'], scope=self.federation)
        json, code = connection.GetAPIGeneric(self.url_api + cmd.call, self.login, self.password)
        if code == 200 and isinstance(json, dict) and 'results' in json and json['result_count'] > 0:
            for seg in json['results']:
                logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Found Segment " + seg['display_name'])
                SG = segments.Segment(seg['display_name'], seg['id'], seg['unique_id'])
                SG.connectivity = seg['advanced_config']['connectivity']
                SG.admin_state = seg['admin_state']
                SG.tz_path = seg['transport_zone_path']
                SG.type = SG.getTypeSegment(self)
                if 'vlan_ids' in seg:
                    SG.vlan_ids = seg['vlan_ids']
                SG.call = commands.cmd('segment_call', self.discovercalls['list_segments'] + '/' + SG.id, self.version)
                self.calls.append(SG.call)
                self.segments.append(SG)
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + cmd.call + tools.color.NORMAL + ' - HTTP error: ' + str(code))

