#!/opt/homebrew/bin/python3
from lib import interfaces, connection, color, commands
import logging

class TN:
    ip_mgmt = ""
    type = ""
    interfaces = []
    call = ""
    tn_status_call = ""
    # init method or constructor
    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.interfaces = []

    def __eq__(self, other) : 
        return self.__dict__ == other.__dict__
    
    def getIntCommandsPolling(self):
        Tab_result = []
        for it in self.interfaces:
            if it.call.usedforPolling: Tab_result.append(it)
        return Tab_result

    def viewTN(self):
        print('Informations for ' + self.name)
        print(' - uuid: ' + self.uuid)
        print(' - ip_mgmt: ' + self.ip_mgmt)
        print(' - type: ' + self.type)
        for it in self.interfaces:
            it.viewInterface()
        self.call.viewCommand()
        self.tn_status_call.viewCommand()
        

    def discoverInterfaces(self, call_node, call_int, manager_url, login, password, timeout):
        """
        discover interfaces in a Node
        Args
        ----------
        call_node (str): call api for a specific node
        call_int (dict): config of api callfor a interface of a node
        login, password, timeout
        """
        url = call_node.replace('TNID', self.uuid)
        tn_int_json, code = connection.GetAPIGeneric(manager_url + url, login, password)
        if code == 200:
            if isinstance(tn_int_json, dict) and 'results' in tn_int_json and tn_int_json['result_count'] > 0:
                for it in tn_int_json['results']:
                    if (self.type == 'EdgeNode' and (it['interface_id'] != 'eth0' and it['interface_id'] != 'kni-lrport-0')) or (self.type == 'HostNode' and it['interface_type'] == 'PHYSICAL' and (it['connected_switch_type'] == 'N-VDS' or it['connected_switch_type'] == 'VDS')):
                        interface = interfaces.Interface(it['interface_id'])
                        interface.admin_status = it['admin_status']
                        interface.link_status = it['link_status']
                        interface.mtu = it['mtu']
                        call_int['call'] = call_int['call'].replace('TNID', self.uuid).replace('INTID', it['interface_id'])
                        interface.call = commands.cmd('int_stats_call',call_int, self, timeout)

                        if 'interface_type' in it: interface.interface_type = it['interface_type']
                        if 'interface_uuid' in it: interface.uuid = it['interface_uuid']
                        if 'connected_switch_type' in it: interface.connected_switch_type = it['connected_switch_type']
                        if interface not in self.interfaces:
                            logging.info(color.style.RED + "-- ==> " + color.style.NORMAL + "Found interface " + it['interface_id'] + " in " + self.name)
                            self.interfaces.append(interface)

            

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
