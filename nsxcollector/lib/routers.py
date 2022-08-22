#!/opt/homebrew/bin/python3
from lib import interfaces, connection, color, commands
import logging

class Router:
    type = ''
    ha_mode = ''
    failover_mode = ''
    call = ''
    localservice = ''
    interfaces = []
    
    def __init__(self, name, id, unique_id):
        self.name = name
        self.id = id
        self.unique_id = unique_id
        self.interfaces = []

    def getIntCommandsPolling(self):
        Tab_result = []
        for it in self.interfaces:
            if it.call.usedforPolling: Tab_result.append(it.call)
        
        return Tab_result

    def viewRouter(self):
        print('Informations about ' + self.type + ' router ' + self.name)
        print(' - id: ' + self.id)
        print(' - unique_id: ' + self.unique_id)
        print(' - type: ' + self.type)
        print(' - ha_mode: ' + self.ha_mode)
        print(' - failover_mode: ' + self.failover_mode)
        self.call.viewCommand()
        print(' - localservice: ' + self.localservice)
        for it in self.interfaces:
            it.viewInterface()

    def getLocalService(self,manager_url, call, login, password):
        url = call.replace('RTRID', self.name)
        local_json, code = connection.GetAPIGeneric(manager_url + url, login, password)
        if code == 200 and isinstance(local_json, dict) and 'results' in local_json and local_json['result_count'] > 0:
            for lc in local_json['results']:
                self.localservice = lc['id']

    def discoverInterfaces(self, call_router, call_int, manager_url, login, password, timeout):
        """
        discover interfaces in a Router
        Args
        ----------
        call_node (str): call api for a specific Router
        call_int (dict): config of api callfor a interface of a router
        login, password, timeout
        """
        url = call_router.replace('RTRID', self.name).replace('LSID', self.localservice)
        rtr_int_json, code = connection.GetAPIGeneric(manager_url + url, login, password)
        if code == 200 and isinstance(rtr_int_json, dict) and 'results' in rtr_int_json and rtr_int_json['result_count'] > 0:
            for it in rtr_int_json['results']:
                interface = interfaces.Interface(it['display_name'])
                interface.type = it['type']
                interface.resource_type = it['resource_type']
                interface.uuid = it['unique_id']
                call_int['call'] = call_int['call'].replace('RTRID', self.id).replace('INTID', it['id']).replace('LSID', self.localservice)
                interface.call = commands.cmd('int_stats_call',call_int, interface, timeout)

                if interface not in self.interfaces:
                    logging.info(color.style.RED + "-- ==> " + color.style.NORMAL + "Found interface " + it['id'] + " in " + self.name)
                    self.interfaces.append(interface)