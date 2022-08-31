#!/opt/homebrew/bin/python3
from lib import connection, tools
from lib.nsxinfra import interfaces, commands
import logging

class node:
    call_variable_id = ''
    path = ''
    localservice = ''
    # init method or constructor
    def __init__(self, name, id, type):
        self.name = name
        self.id = id
        self.type = type
        self.interfaces = []


    def viewNode(self):
        print('Informations about ' + self.type + ' node ' + self.name)
        print(' - id: ' + self.id)
        # if self.unique_id is not None: print(' - unique_id: ' + self.unique_id)
        # if self.ip_mgmt is not None: print(' - ip_mgmt: ' + self.ip_mgmt)
        print(' - type: ' + self.type)
        print(' - path: ' + self.path)
        print(' - call_variable_id: ' + self.call_variable_id)
        # print(' - localservice: ' + self.localservice)
        for it in self.interfaces:
            it.viewInterface()

    def getLocalService(self, infra, localservice_call):
        local_json, code = connection.GetAPIGeneric(infra.url_api + localservice_call, infra.login, infra.password)
        if code == 200 and isinstance(local_json, dict) and 'results' in local_json and local_json['result_count'] > 0:
            for lc in local_json['results']:
                return lc['id']
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + localservice_call + tools.color.NORMAL + ' - HTTP error: ' + str(code))

    def findInterface(self, name):
        for it in self.interfaces:
            if it.name == name:
                return it


    def discoverInterfaces(self, infra):
        """
        discover interfaces in a Node
        Args
        ----------
        infra (obj): infra object
        """
        cmd = infra.swagger.searchCommand(exact=True, name=infra.discovercalls['list_tn_interfaces'], scope=infra.federation)
        url = cmd.call.replace('{transportnodeid}', self.id)
        json, code = connection.GetAPIGeneric(infra.url_api + url, infra.login, infra.password)
        if code == 200 and isinstance(json, dict) and 'results' in json and json['result_count'] > 0:
            for it in json['results']:
                if (self.type == 'EdgeNode' and (it['interface_id'] != 'eth0' and it['interface_id'] != 'kni-lrport-0')) or (self.type == 'HostNode' and it['interface_type'] == 'PHYSICAL' and (it['connected_switch_type'] == 'N-VDS' or it['connected_switch_type'] == 'VDS')):
                    interface = interfaces.Interface(it['interface_id'], it['interface_id'],self)
                    interface = interfaces.Interface(it['display_name'], it['id'],self)

                    interface.admin_status = it['admin_status']
                    interface.link_status = it['link_status']
                    interface.mtu = it['mtu']

                    interface.call = commands.cmd('interface_call', url + '/' + interface.id, infra.version )
                    interface.call = commands.cmd('interface_call', call_int + '/' + interface.id, infra.version )

                    infra.calls.append(interface.call)

                    if 'interface_type' in it: interface.interface_type = it['interface_type']
                    if 'interface_uuid' in it: interface.uuid = it['interface_uuid']
                    if 'connected_switch_type' in it: interface.connected_switch_type = it['connected_switch_type']
                    if interface not in self.interfaces:
                        logging.info(tools.color.RED + "-- ==> " + tools.color.NORMAL + "Found interface " + it['interface_id'] + " in " + self.name)
                        self.interfaces.append(interface)

        elif json['result_count'] == 0:
            logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "No Interfaces found on " + self.id)

        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + url + tools.color.NORMAL + ' - HTTP error: ' + str(code))


class router(node):
    localservice = ''
    ha_mode = ''
    failover_mode = ''

    def __init__(self, type):
        self.type = type

class transportnode(node):
    unique_id = ""
    ip_mgmt = ""

    def __init__(self, type):
        self.type = type
