#!/opt/homebrew/bin/python3
from lib import connection, tools
from lib.nsxinfra import commands, interfaces
import logging

class Router:
    type_path = ''
    ha_mode = ''
    failover_mode = ''
    path = ''
    call = ''
    call_variable_id = ''
    calls = []
    localservice = ''
    interfaces = []
    
    def __init__(self, name, id, unique_id, type):
        self.name = name
        self.id = id
        self.unique_id = unique_id
        self.type = type
        self.object_type = type
        if self.type == 'Tier1': 
            self.type_path = 'tier-1s'
        if self.type == 'Tier0':
            self.type_path = 'tier-0s'
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
        print(' - path: ' + self.path)
        print(' - ha_mode: ' + self.ha_mode)
        print(' - failover_mode: ' + self.failover_mode)
        print(' - call_variable_id: ' + self.call_variable_id)
        self.call.viewCommand()
        for cmd in self.calls:
            cmd.viewCommand()
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

    def findInterface(self, name):
        for it in self.interfaces:
            if it.name == name:
                return it


    def discoverInterfaces(self, infra, call_int):
        """
        discover interfaces in a Router
        Args
        ----------
        infra (obj): infra object
        call_int (str): string of the api call for an interface
        """
        rtr_int_json, code = connection.GetAPIGeneric(infra.url_api + call_int, infra.login, infra.password)
        if code == 200 and isinstance(rtr_int_json, dict) and 'results' in rtr_int_json and rtr_int_json['result_count'] > 0:
            for it in rtr_int_json['results']:
                # copy_call = {}
                interface = interfaces.Interface(it['display_name'], it['id'],self)
                interface.type = it['type']
                interface.resource_type = it['resource_type']
                interface.unique_id = it['unique_id']
                interface.call = commands.cmd('interface_call', call_int + '/' + interface.id, infra.version )
                infra.calls.append(interface.call)

                if interface not in self.interfaces:
                    logging.info(tools.color.RED + "-- ==> " + tools.color.NORMAL + "Found interface " + it['display_name'] + " in " + self.name)
                    self.interfaces.append(interface)
        elif rtr_int_json['result_count'] == 0:
            logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "No Interfaces found on " + self.id)
        else:
            print(tools.color.RED + "ERROR - Discovery: Can't access to " + call_int + tools.color.NORMAL + ' - HTTP error: ' + str(code))