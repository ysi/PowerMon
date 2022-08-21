#!/opt/homebrew/bin/python3

class Interface:
    uuid = ""
    rx = ""
    tx = ""
    rx_drop = ""
    tx_drop = ""
    admin_status = ""
    link_status = ""
    mtu = ""
    interface_type = ""
    connected_switch_type = ""
    call = ""
    type = ""
    resource_type = ""
    
    def __init__(self, name):
        self.name = name

    def viewInterface(self):
        print(' - Interface ' + self.name)
        print('     - uuid: ' + self.uuid)
        print('     - rx: ' + self.rx)
        print('     - tx: ' + self.tx)
        print('     - rx_drop: ' + self.rx_drop)
        print('     - tx_drop: ' + self.tx_drop)
        print('     - admin_status: ' + self.admin_status)
        print('     - link_status: ' + self.link_status)
        print('     - mtu: ' + str(self.mtu))
        print('     - interface_type: ' + self.interface_type)
        print('     - connected_switch_type: ' + self.connected_switch_type)
        print('     - type: ' + self.type)
        print('     - ressource_type: ' + self.resource_type)
        self.call.viewCommand()
