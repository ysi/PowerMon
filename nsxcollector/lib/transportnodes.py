#!/opt/homebrew/bin/python3

class TN:
    ip_mgmt = ""
    vip = ""
    uuid = ""
    type = ""
    login = ""
    password = ""
    port = ""
    auth = ""
    cmd = []
    gf_dashboard = None
    list_intervall_cmd = []
    # init method or constructor
    def __init__(self, fqdn):
        self.fqdn = fqdn
        self.port = ""
        self.list_intervall_cmd = []
        self.cmd = []

    def __eq__(self, other) : 
        return self.__dict__ == other.__dict__

    def addCmd(self, cd):
        self.cmd.append(cd)

def getListTypeComponent(List):
    type_list = []
    for tn in List:
        if tn.type not in type_list:
            type_list.append(tn.type)
    
    return type_list

def getComponentbyType(type, List):
    List_Component = []
    for item in List:
        if item.type == type:
            List_Component.append(item)
    return List_Component

def getEdge(List):
    List_Edge = []
    for item in List:
        if item.type == 'EdgeNode':
            List_Edge.append(item)
    return List_Edge

def getHost(List):
    List_Host = []
    for item in List:
        if item.type == 'HostNode':
            List_Host.append(item)
    return List_Host