#!/opt/homebrew/bin/python3
from lib import connection, tools
import logging

class node:
    call_variable_id = ''
    path = ''
    # init method or constructor
    def __init__(self, name, id, type):
        self.name = name
        self.id = id
        self.type = type
        self.interfaces = []



    def findInterface(self, name):
        for it in self.interfaces:
            if it.name == name:
                return it



class router(node):
    localservice = ''
    ha_mode = ''
    failover_mode = ''

    def viewNode(self):
        print('Informations about ' + self.type + ' node ' + self.name)
        print(' - id: ' + self.id)
        print(' - type: ' + self.type)
        print(' - call_variable_id: ' + self.call_variable_id)
        print(' - localservice: ' + self.localservice)
        for it in self.interfaces:
            it.viewInterface()


    def getLocalService(self, infra, localservice_call):
        local_json, code = connection.GetAPIGeneric(infra.url_api + localservice_call, infra.login, infra.password)
        if code == 200 and isinstance(local_json, dict) and 'results' in local_json and local_json['result_count'] > 0:
            for lc in local_json['results']:
                return lc['id']
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + localservice_call + tools.color.NORMAL + ' - HTTP error: ' + str(code))


    def discoverInterfaces(self, infra, url):
        """
        discover interfaces in a Router
        Args
        ----------
        infra (obj): infra object
        call_int (str): string of the api call for an interface
        """
        rtr_int_json, code = connection.GetAPIGeneric(infra.url_api + url, infra.login, infra.password)
        if code == 200 and isinstance(rtr_int_json, dict) and 'results' in rtr_int_json and rtr_int_json['result_count'] > 0:
            for it in rtr_int_json['results']:
                # copy_call = {}
                interface = Interface(it['display_name'], it['id'],self)
                interface.type = it['type']
                interface.resource_type = it['resource_type']
                interface.unique_id = it['unique_id']
                interface.call_variable_id = "{interfaceid}"
                if interface not in self.interfaces:
                    logging.info(tools.color.RED + "-- ==> " + tools.color.NORMAL + "Found interface " + it['display_name'] + " in " + self.name)
                    self.interfaces.append(interface)
        elif rtr_int_json['result_count'] == 0:
            logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "No Interfaces found on " + self.id)
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + url + tools.color.NORMAL + ' - HTTP error: ' + str(code))



class transportnode(node):
    node_id = ""
    ip_mgmt = ""

    def viewNode(self):
        print('Informations about ' + self.type + ' node ' + self.name)
        print(' - id: ' + self.id)
        print(' - unique_id: ' + self.node_id)
        print(' - ip_mgmt: ' + self.ip_mgmt)
        print(' - type: ' + self.type)
        print(' - call_variable_id: ' + self.call_variable_id)
        for it in self.interfaces:
            it.viewInterface()

    def discoverInterfaces(self, infra, url):
        """
        discover interfaces in a Node
        Args
        ----------
        infra (obj): infra object
        """
        tn_int_json, code = connection.GetAPIGeneric(infra.url_api + url, infra.login, infra.password)
        if code == 200 and isinstance(tn_int_json, dict) and 'results' in tn_int_json and tn_int_json['result_count'] > 0:
            for it in tn_int_json['results']:
                if (self.type == 'EdgeNode' and (it['interface_id'] != 'eth0' and it['interface_id'] != 'kni-lrport-0')) or (self.type == 'HostNode' and it['interface_type'] == 'PHYSICAL' and (it['connected_switch_type'] == 'N-VDS' or it['connected_switch_type'] == 'VDS')):
                    interface = Interface(it['interface_id'], it['interface_id'],self)
                    interface.admin_status = it['admin_status']
                    interface.link_status = it['link_status']
                    interface.mtu = it['mtu']
                    interface.call_variable_id = "{interfaceid}"
                    if 'interface_type' in it: interface.interface_type = it['interface_type']
                    if 'interface_uuid' in it: interface.uuid = it['interface_uuid']
                    if 'connected_switch_type' in it: interface.connected_switch_type = it['connected_switch_type']
                    if interface not in self.interfaces:
                        logging.info(tools.color.RED + "-- ==> " + tools.color.NORMAL + "Found interface " + it['interface_id'] + " in " + self.name)
                        self.interfaces.append(interface)
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + url + tools.color.NORMAL + ' - HTTP error: ' + str(code))
            


class Interface:
    unique_id = ""
    admin_status = ""
    link_status = ""
    mtu = ""
    interface_type = ""
    connected_switch_type = ""
    call = ""
    call_variable_id = ''
    type = ""
    mode = {}
    resource_type = ""
    
    def __init__(self, name, id, parent_obj):
        self.name = name
        self.id = id
        self.object_type = 'interface'
        self.parent_object = parent_obj

    def viewInterface(self):
        print(' - Interface ' + self.name)
        print('     - object_type: ' + self.object_type)
        print('     - id: ' + self.id)
        print('     - unique_id: ' + self.unique_id)
        print('     - admin_status: ' + self.admin_status)
        print('     - link_status: ' + self.link_status)
        print('     - mtu: ' + str(self.mtu))
        print('     - interface_type: ' + self.interface_type)
        print('     - connected_switch_type: ' + self.connected_switch_type)
        print('     - type: ' + self.type)
        print('     - ressource_type: ' + self.resource_type)
        print('     - node_name: ' + self.parent_object.name)
        print('     - node_type: ' + self.parent_object.type)
        print('     - call_variable_id: ' + self.call_variable_id)
        print('     - call: ' + self.call)
