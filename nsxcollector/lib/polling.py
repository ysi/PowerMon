
#!/opt/homebrew/bin/python3
# coding: utf8

from lib import tools, connection, influxdb
import sys, copy

def collectData(infra, elementlist,inDB):
    """
    Collect data from a list of cmd and write into influxdb
    """
    # Test what kind of threading
    for item in elementlist:
        result_json, code = connection.GetAPIGeneric(infra.url_api + item.call, infra.cluster.members[0].login, infra.cluster.members[0].password)
        if code == 200:
            inDB.influxWrite(item, result_json)
        else:
            print(tools.color.RED + "ERROR HTTP ==> " + str(code) + tools.color.NORMAL + " : error accessing to " + infra.url_api + item.call)


def createCmdPolling(cmd, cmd_panel, node=None, list_param=[]):
    if len(list_param) > 0: 
        values = list_param
        call = cmd.replaceIDs_call(list_param)
    else: 
        call = cmd.call
        values = []
    # Get information of commands from yaml panel config
    if 'suffix' in cmd_panel:
        suffix = cmd_panel['suffix']
    else: suffix = ""
    # Create a copy of swagger cmd
    polling_cmd = copy.deepcopy(cmd)
    polling_cmd.polling = cmd_panel['polling']
    polling_cmd.call = call + suffix
    polling_cmd.parameters_values = values
    # Create Influxdb queries
    polling_cmd.influx_queries = influxdb.createQueries(cmd_panel, polling_cmd, node)
    return polling_cmd


def PollingListCmds(infra):
    # Create polling list of commands, based on panels config, and infra
    # Loop through panels
    List_Polling_Cmds = []
    for panel in infra.configpanels:
        # Loop through all commands for a panel
        for cmd_panel in panel['polling']:
            # Get the the command
            cmd = infra.swagger.searchCommand(exact=True, name=cmd_panel['call'])

            # If more than one commmand, take the Policy one
            if isinstance(cmd, list) and len(cmd) > 1: cmd = [ i for i in cmd if i.type_command=='Policy'][0]
            elif isinstance(cmd, list) and len(cmd) == 0:
                print(tools.color.RED + "ERROR - Can't find " + cmd_panel['call'] + tools.color.NORMAL + ' in the swagger. Please check the name in Swaggercommands.csv file.')
                sys.exit()

            if 'components' in cmd_panel and isinstance(cmd_panel['components'], list):
                # found component in the panel config
                for node in cmd_panel['components']:
                    find_node = infra.findComponent(node['name'])
                    # component is specified and found in infra object
                    if find_node is not None:
                        # Want specific interfaces
                        if len(node['interfaces']) > 0:
                            for it in node['interfaces']:
                                it_polling = find_node.findInterface(it)
                                if it_polling is not None:
                                    List_Polling_Cmds.append( createCmdPolling(cmd, cmd_panel, find_node, [find_node.name, it_polling.id]))
                        # Want all interfaces
                        else:
                            for it in find_node.interfaces:
                                List_Polling_Cmds.append( createCmdPolling(cmd, cmd_panel, find_node, [find_node.name, it_polling.id] ))

                    # no component found in object
                    else:
                        print(tools.color.RED + "ERROR - Can't find " + node['name'] + tools.color.NORMAL + ' in discover Infra. Please check the name in your Panel YAML File.')
            # no component precised - meaning NSX Manager or want all components if parameters
            else:
                if len(cmd.parameters) > 0:
                    for node in infra.nodes:
                        if node.call_variable_id in cmd.parameters:
                            if 'Tier' in node.type and '{localserviceid}' in cmd.parameters:
                                List_Polling_Cmds.append( createCmdPolling(cmd, cmd_panel, node, [node.id, node.localservice], ) )

                else:
                    List_Polling_Cmds.append( createCmdPolling(cmd, cmd_panel, infra.cluster) )

    return List_Polling_Cmds  
