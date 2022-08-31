#!/opt/homebrew/bin/python3
from lib import tools, connection
from lib.nsxinfra import fabric, commands, segments, node
import logging

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
        self.calls = []
        self.swagger = None
        self.commandfile = ""


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
            node.viewNode()
        for sg in self.segments:
            sg.viewSegment()

    def viewInfraCommands(self):
        for i in self.calls:
            i.viewCommand()

    def findComponent(self, name):
        for node in self.nodes:
            if node.name == name:
                return node
        
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
        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Getting Nodes")
        for k, cmdname in self.discovercalls.items():
            if k == 'list_t0' or k == 'list_t1' or k == 'list_tn':
                typenode = k.split('_')[1]
                int_cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls[k + '_interfaces'], scope=self.federation)
                
                nodecmd = self.swagger.searchCommand(exact=True, name=cmdname, scope=self.federation)
                json, code = connection.GetAPIGeneric(self.url_api + nodecmd.call, self.login, self.password)
                if code == 200 and isinstance(json, dict) and 'results' in json and json['result_count'] > 0:
                    for nd in json['results']:
                        if typenode == 'tn': 
                            typeobj = nd['node_deployment_info']['resource_type']
                            nodeObj = node.transportnode(nd['display_name'],nd['id'],typeobj)
                            nodeObj.node_id = nd['node_id']
                            nodeObj.ip_mgmt = nd['node_deployment_info']['ip_addresses'][0]
                            nodeObj.call_variable_id = "{transportnodeid}"
                            url = int_cmd.call.replace(nodeObj.call_variable_id, nodeObj.id)

                        elif typenode == 't1': 
                            nodeObj = node.router(nd['display_name'],nd['id'],nd['resource_type'])
                            nodeObj.call_variable_id = '{tier1id}'
                            ls_cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls['list_' + typenode + '_localservice'], scope=self.federation)
                            nodeObj.localservice = nodeObj.getLocalService(self, ls_cmd.call.replace(nodeObj.call_variable_id, nodeObj.id))
                            url = int_cmd.call.replace(nodeObj.call_variable_id, nodeObj.id).replace('{localeserviceid}', nodeObj.localservice)

                        else:
                            nodeObj = node.router(nd['display_name'],nd['id'],nd['resource_type'])
                            nodeObj.call_variable_id = '{tier0id}'
                            ls_cmd = self.swagger.searchCommand(exact=True, name=self.discovercalls['list_' + typenode + '_localservice'], scope=self.federation)
                            nodeObj.localservice = nodeObj.getLocalService(self, ls_cmd.call.replace(nodeObj.call_variable_id, nodeObj.id))
                            url = int_cmd.call.replace(nodeObj.call_variable_id, nodeObj.id).replace('{localeserviceid}', nodeObj.localservice)

                        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Found Node " + nodeObj.type + ' - ' + nd['display_name'])
                        
                        nodeObj.discoverInterfaces(self, url)
                        self.nodes.append(nodeObj)

                else:
                    print(tools.color.RED + "ERROR - Discovery: Can't access to " + nodecmd.call + tools.color.NORMAL + ' - HTTP error: ' + str(code))


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

