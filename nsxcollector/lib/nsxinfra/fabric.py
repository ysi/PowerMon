#!/opt/homebrew/bin/python3

class Cluster:
    members = []
    online_nodes = []
    offline_nodes = []
    status = ""
    call = ""

    def __init__(self, id):
        self.id = id
        self.calls = []
        self.object_type = 'cluster'

    def viewCluster(self):
        print('Information for NSX Cluster: ' + self.id)
        print(' - object_type: ' + self.object_type)
        print(' - status: ' + self.status)
        for nsx in self.members:
            nsx.viewManager()
        self.call.viewCommand()

class Manager:
    ip_mgmt = ""
    vip = ""
    uuid = ""
    auth = ""

    # init method or constructor
    def __init__(self, fqdn):
        self.fqdn = fqdn
        self.object_type = 'manager'

    def viewManager(self):
        print('Information for Manager: ' + self.fqdn)
        print(' - object_type: ' + self.object_type)
        print(' - ip_mgmt: ' + self.ip_mgmt)
        print(' - vip: ' + self.vip)
        print(' - uuid: ' + self.uuid)
        print(' - auth: ' + self.auth)

class Transport_Zone:
    type = ""
    path = ""
    id = ""

    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.object_type = ('transport_zone')

    def viewTZ(self):
        print('Information for TZ: ' + self.name)
        print(' - id: ' + self.id)
        print(' - type: ' + self.type)
        print(' - path: ' + self.path)
