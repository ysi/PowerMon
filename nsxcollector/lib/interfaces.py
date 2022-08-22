#!/opt/homebrew/bin/python3

class Interface:
    uuid = ""
    admin_status = ""
    link_status = ""
    mtu = ""
    interface_type = ""
    connected_switch_type = ""
    call = ""
    type = ""
    resource_type = ""
    node_name = ""
    node_type = ""
    
    def __init__(self, name):
        self.name = name

    def viewInterface(self):
        print(' - Interface ' + self.name)
        print('     - uuid: ' + self.uuid)
        print('     - admin_status: ' + self.admin_status)
        print('     - link_status: ' + self.link_status)
        print('     - mtu: ' + str(self.mtu))
        print('     - interface_type: ' + self.interface_type)
        print('     - connected_switch_type: ' + self.connected_switch_type)
        print('     - type: ' + self.type)
        print('     - ressource_type: ' + self.resource_type)
        print('     - node_name: ' + self.node_name)
        print('     - node_type: ' + self.node_type)
        self.call.viewCommand()
