#!/opt/homebrew/bin/python3
from lib import tools
from lib.nsxinfra import transportnodes, commands, infra
import sys, logging

def discovery(config):
    """
    discover all components in NSX
    Return a list of nodes object and the NSX session

    Args
    ----------
    config : yaml config dictionnay
    """
    try:
        # Connect to NSX Manager
        if config['Component']['Manager']['port'] is None or config['Component']['Manager']['port'] == '':
            url = 'https://' + config['Component']['Manager']['fqdn']
        else:
            url = 'https://' + config['Component']['Manager']['fqdn'] + ":" + str(config['Component']['Manager']['port'])
        # Create infrastructure object
        nsxinfra = infra.nsx_infra(config['General']['Name_Infra'].replace(' ', ''), url, config['General']['api_timeout'], config['Component']['Manager']['login'], config['Component']['Manager']['password'], config['General']['Federation'])
        # Get all panels config        
        nsxinfra.configpanels = tools.readPanelsConfig(config['General']['configpanel_path'])
        # Grab all API/REST commands of the NSX
        nsxinfra.swagger = commands.Swagger(nsxinfra, config['General']['manager_commands'], config['General']['policy_commands'])
        # Create Swagger Command file
        nsxinfra.swagger.createCommandsFile()
        nsxinfra.discovercalls = config['Discovering']
        logging.info(tools.color.RED + "==> " + tools.color.NORMAL + "Connecting to NSX Manager " + tools.color.GREEN + url + tools.color.NORMAL + " and Getting all informations")
        nsxinfra.getGenInformations()
        nsxinfra.addTransportZone()
        nsxinfra.addCluster()
        # nsxinfra.addNodes()
        # sys.exit()

        nsxinfra.addTN()
        for k, v in nsxinfra.discovercalls.items():
            if k == 'list_t0' or k == 'list_t1': nsxinfra.addRouters(k)
        

        nsxinfra.addSegments()

        print(tools.color.RED + "==> " + tools.color.NORMAL + "Found " + str(len(nsxinfra.cluster.members)) + " NSX Manager(s)")
        print(tools.color.RED + "==> " + tools.color.NORMAL + "Found " + str(len(transportnodes.getComponentbyType('EdgeNode',nsxinfra.nodes))) + " Edge(s)")
        print(tools.color.RED + "==> " + tools.color.NORMAL + "Found " + str(len(transportnodes.getComponentbyType('HostNode',nsxinfra.nodes))) + " Host(s)")
        nb_router = []
        print(tools.color.RED + "==> " + tools.color.NORMAL + "Found " + str(len([ nb_router for rtr in nsxinfra.routers if rtr.type == 'Tier0'])) + " T0 Router(s)")
        print(tools.color.RED + "==> " + tools.color.NORMAL + "Found " + str(len([ nb_router for rtr in nsxinfra.routers if rtr.type == 'Tier1'])) + " T1 Router(s)")
        print(tools.color.RED + "==> " + tools.color.NORMAL + "Found " + str(len(nsxinfra.segments)) + " Segment(s)")
        return nsxinfra
    except Exception as error:
        print(tools.color.RED + "ERROR - discovery: " + tools.color.NORMAL + str(error))
        print(tools.color.RED + "ERROR - discovery: Can't connect to " + config['Component']['Manager']['fqdn'] + tools.color.NORMAL + ' - ' + str(error))
        sys.exit()

def getCommandListbyPooling(CommandList):
    List_Result = []
    intervalList = []
    # create list of interval
    for cmd in CommandList:
        if cmd.polling not in intervalList:
            intervalList.append(cmd.polling)

    for interval in intervalList:
        List_tmp = []
        for cmd in CommandList:
            if cmd.polling == interval:
                List_tmp.append(cmd)

        List_Result.append(List_tmp)

    return List_Result