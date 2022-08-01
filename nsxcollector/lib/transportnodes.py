#!/opt/homebrew/bin/python3

class TN:
    ip_mgmt = ""
    type = ""
    login = ""
    password = ""
    port = ""
    auth = ""
    cmd = []
    # init method or constructor
    def __init__(self, name):
        self.name = name

    def __eq__(self, other) : 
        return self.__dict__ == other.__dict__
        
    def addCmd(self, cd):
        self.cmd.append(cd)


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
