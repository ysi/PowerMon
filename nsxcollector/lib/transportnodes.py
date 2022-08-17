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
    timeout = ""
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
