#!/opt/homebrew/bin/python3
import lib, csv, copy

class Swagger:
    def __init__(self, infra, manager_commands, policy_commands):
        # Get and read json API
        print(lib.tools.color.RED + "==> " + lib.tools.color.NORMAL + " Grab all Manager commands - please wait")
        manager_url = infra.url_api + manager_commands
        json_manager, code_manager = lib.connection.GetAPIGeneric(manager_url, infra.login, infra.password)
        print(lib.tools.color.RED + "==> " + lib.tools.color.NORMAL + " Grab all Policy commands - please wait")
        policy_url = infra.url_api + policy_commands
        json_policy, code_policy = lib.connection.GetAPIGeneric(policy_url, infra.login, infra.password)
        json_list = [json_policy, json_manager]
        self.commands = []
        self.parameters = []
        if code_manager == 200 and code_policy == 200:
            for idx, json in enumerate(json_list):
                List_CMD = []
                self.version = json['info']['version']
                infra.version = self.version
                self.title = json['info']['title']
                for k, v in json['paths'].items():
                    if 'get' in v:
                        cd = cmd(v['get']['operationId'], json['basePath'] + k, json['info']['version'])
                        # replace fucking redundant IDs in original swagger by only one
                        # For enforcement, Tier 1, Tier 0, local-service, ns-group, segment-id, userid
                        cd.parameters = self.replaceNameVariable(cd)
                        cd.call = cd.replaceIDs_call(cd.parameters)

                        cd.basepath = json['basePath']
                        if cd.basepath == '/policy/api/v1': cd.type_command = 'Policy'
                        else: cd.type_command = 'Manager'
                        if '{' in k: cd.withparameter = True
                        if 'tags' in v['get']: cd.tags = cd.tags + v['get']['tags']

                        # add parameters in Swagger list of parameters
                        for par in cd.parameters:
                            if par not in self.parameters: self.parameters.append(par)
                        cd.timeout = infra.api_timeout
                        cd.summary = v['get']['summary']
                        if 'global-infra' in k.split('/'): cd.scope = "Global"
                        else: cd.scope = "Infra"

                        self.commands.append(cd)
                        List_CMD.append(cd)

                if idx == 0:
                    print(lib.tools.color.RED + "==> " + lib.tools.color.NORMAL + " Found " + str(len(List_CMD)) + " Policy commands")
                else:
                    print(lib.tools.color.RED + "==> " + lib.tools.color.NORMAL + " Found " + str(len(List_CMD)) + " Manager commands")
                    print(lib.tools.color.RED + "==> NSX Version: " + lib.tools.color.NORMAL + json['info']['version'])
        
        else:
            print(lib.tools.color.RED + "ERROR - Can't access and grab JSON commands file" +  + lib.tools.color.NORMAL)
            print(lib.tools.color.RED + "ERROR - Policy url: " + lib.tools.color.NORMAL + policy_url + ' - HTTP error: ' + str(code_policy))
            print(lib.tools.color.RED + "ERROR - Manager url: " + lib.tools.color.NORMAL + manager_url + ' - HTTP error: ' + str(code_manager))

        print(lib.tools.color.RED + "==> " + lib.tools.color.NORMAL + " Total Commands Found " + str(len(self.commands)))


    def createCommandsFile(self):
        # Create a CSV file with all commands in the swagger
        print(lib.tools.color.RED + "==> " + lib.tools.color.NORMAL + "Create Swaggercommands.csv commands file")
        with open('Swaggercommands.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['name','type','scope','parameters','call', 'summary'])
            for cmd in self.commands:
                writer.writerow([cmd.name,cmd.type_command,cmd.scope,', '.join(cmd.parameters), cmd.call, cmd.summary])
        

    def replaceNameVariable(self, cd):
        # replace fucking redundant IDs in original swagger by only one
        # For enforcement, Tier 1, Tier 0, local-service, ns-group, segment-id, userid
        Result = [] 
        tmp = cd.searchIDs()
        for par in tmp:
            if 'services' in par: par = par.replace('services', 'service')
            if 'segments' in par: par = par.replace('segments', 'segment')
            if 'name' in par: par = par.replace('name', 'id')
            par = par.replace('-', '')
            Result.append(par)
        return Result


    def viewAllParameters(self):
        for par in sorted(self.parameters): print(par)
        print(lib.tools.color.RED + "==> " + lib.tools.color.NORMAL + " Found " + str(len(self.parameters)) + " parameters")


    def viewAllCommands(self):
        for cmd in self.commands:
            cmd.viewCommand()

    def viewListCommands(self, list):
        for cmd in list:
            cmd.viewCommand()


    def searchCommand(self, exact, **kwargs):
        """
        Search in all Commands. 
        Args
        ----------
        search in all parameters of a commands
        ex: scope, tags, withparameter ...
        """
        List_tmp = []
        List_result = self.commands
        for k, v in kwargs.items():
            List_tmp = []
            for cmd in List_result:
                # search a tag in the list of all tags of a command
                if isinstance(v, list) and len(v) < len(getattr(cmd, k)):
                    for item in v:
                        if item in getattr(cmd, k): List_tmp.append(cmd)
                elif k == 'call' or k == 'name' or 'k' == 'type_command':
                    if not exact and v in getattr(cmd, k): List_tmp.append(cmd)
                    elif exact and v == getattr(cmd, k): List_tmp.append(cmd)
                else:
                    if getattr(cmd, k) == v:
                        List_tmp.append(cmd)
            List_result = List_tmp
        
        if len(List_result) == 1: return List_result[0]
        else: return List_result


class cmd:
    result = None
    polling = ""
    timeout = ""
    summary = ""
    type = ""
    type_command = ""
    basepath = ""
    influx_queries = []
    parameters_values = []

    # init method or constructor
    def __init__(self, name, call, version, tags=[]):
        self.name = name
        self.call = call
        self.version = version
        self.withparameter = False
        self.tags = tags
        self.parameters = []
        self.scope = ""

    def searchIDs(self):
        # search IDs in a call
        ListIDs = []
        for item in self.call.split('/'):
            if '{' in item:
                ListIDs.append(item) 
        return ListIDs

    def replaceIDs_call(self, listIDs):
        # replace variable by correct ID in a command
        # send a string of call modified
        cmd = self.call
        List_variables = []
        temp = self.call.split('/')
        for i in temp:
            if '{' in i:
                List_variables.append(i)
        
        for idx, id in enumerate(listIDs):
            cmd = cmd.replace(List_variables[idx], id)
        
        return cmd


    def viewCommand(self):
        print(' - Command ' + self.name)
        print('     - call: ' + self.call)
        print('     - version: ' + str(self.version))
        print('     - type: ' + str(self.type))
        print('     - type_command: ' + str(self.type_command))
        print('     - basepath: ' + str(self.basepath))
        print('     - withparameter: ' + str(self.withparameter))
        print('     - scope: ' + str(self.scope))
        print('     - polling: ' + str(self.polling))
        print('     - timeout: ' + str(self.timeout))
        print('     - tags: ' + ', '.join(self.tags))
        print('     - parameters: ' + ', '.join(self.parameters))
        print('     - summary: ' + self.summary)
        print('     - influx_queries: ' + ', '.join(self.influx_queries))
