#!/opt/homebrew/bin/python3
from lib import connection, tools
from lib.nsxinfra import interfaces, commands
import logging

class TN:
    ip_mgmt = ""
    type = ""
    interfaces = []
    call = ""
    calls = []
    call_variable_id = ''
    # init method or constructor
    def __init__(self, name, uuid, type):
        self.name = name
        self.id = uuid
        self.type = type
        self.object_type = type.lower()
        self.interfaces = []
    
    def getIntCommandsPolling(self):
        Tab_result = []
        for it in self.interfaces:
            if it.call.usedforPolling: Tab_result.append(it.call)
        return Tab_result

    def viewTN(self):
        print('Informations for ' + self.name)
        print(' - id: ' + self.id)
        print(' - ip_mgmt: ' + self.ip_mgmt)
        print(' - type: ' + self.type)
        self.call.viewCommand()
        for it in self.interfaces:
            it.viewInterface()
        self.call.viewCommand()
        

    def findInterface(self, name):
        for it in self.interfaces:
            if it.name == name:
                return it
        return None

    def discoverInterfaces(self, infra):
        """
        discover interfaces in a Node
        Args
        ----------
        infra (obj): infra object
        """
        cmd = infra.swagger.searchCommand(exact=True, name=infra.discovercalls['list_tn_interfaces'], scope=infra.federation)
        url = cmd.call.replace('{transportnodeid}', self.id)
        tn_int_json, code = connection.GetAPIGeneric(infra.url_api + url, infra.login, infra.password)
        if code == 200 and isinstance(tn_int_json, dict) and 'results' in tn_int_json and tn_int_json['result_count'] > 0:
            for it in tn_int_json['results']:
                if (self.type == 'EdgeNode' and (it['interface_id'] != 'eth0' and it['interface_id'] != 'kni-lrport-0')) or (self.type == 'HostNode' and it['interface_type'] == 'PHYSICAL' and (it['connected_switch_type'] == 'N-VDS' or it['connected_switch_type'] == 'VDS')):
                    interface = interfaces.Interface(it['interface_id'], it['interface_id'],self)
                    interface.admin_status = it['admin_status']
                    interface.link_status = it['link_status']
                    interface.mtu = it['mtu']
                    interface.call = commands.cmd('interface_call', url + '/' + interface.id, infra.version )
                    infra.calls.append(interface.call)

                    if 'interface_type' in it: interface.interface_type = it['interface_type']
                    if 'interface_uuid' in it: interface.uuid = it['interface_uuid']
                    if 'connected_switch_type' in it: interface.connected_switch_type = it['connected_switch_type']
                    if interface not in self.interfaces:
                        logging.info(tools.color.RED + "-- ==> " + tools.color.NORMAL + "Found interface " + it['interface_id'] + " in " + self.name)
                        self.interfaces.append(interface)
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + url + tools.color.NORMAL + ' - HTTP error: ' + str(code))
            

def getComponentbyType(type, List):
    """
    getComponentbyType(type, List)
    return a list of component by type

    Args
    ----------
    type (str): type of component wanted
    List (list): list of component
    """
    List_Component = []
    for item in List:
        if item.type == type:
            List_Component.append(item)
    return List_Component
