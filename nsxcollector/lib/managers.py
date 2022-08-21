#!/opt/homebrew/bin/python3

class Cluster:
    members = []
    online_nodes = []
    offline_nodes = []
    status = ""
    calls = []

    def __init__(self, id, ip_mgmt):
        self.id = id
        self.ip_mgmt = ip_mgmt
        self.calls = []

    def viewCluster(self):
        print('Information for NSX Cluster: ' + self.id)
        print(' - status: ' + self.status)
        for nsx in self.members:
            nsx.viewManager()
        for call in self.calls:
            call.viewCommand()

class Manager:
    ip_mgmt = ""
    vip = ""
    uuid = ""
    login = ""
    password = ""
    port = ""
    auth = ""

    # init method or constructor
    def __init__(self, fqdn):
        self.fqdn = fqdn

    def viewManager(self):
        print('Information for Manager: ' + self.fqdn)
        print(' - ip_mgmt: ' + self.ip_mgmt)
        print(' - vip: ' + self.vip)
        print(' - uuid: ' + self.uuid)
        print(' - login: ' + self.login)
        print(' - password: ' + self.password)
        print(' - port: ' + self.port)
        print(' - auth: ' + self.auth)
