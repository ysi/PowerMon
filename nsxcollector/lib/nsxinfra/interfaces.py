#!/opt/homebrew/bin/python3

class Interface:
    unique_id = ""
    admin_status = ""
    link_status = ""
    mtu = ""
    interface_type = ""
    connected_switch_type = ""
    call = ""
    call_variable_id = ''
    type = ""
    mode = {}
    resource_type = ""
    
    def __init__(self, name, id, parent_obj):
        self.name = name
        self.id = id
        self.object_type = 'interface'
        self.parent_object = parent_obj

    def viewInterface(self):
        print(' - Interface ' + self.name)
        print('     - object_type: ' + self.object_type)
        print('     - id: ' + self.id)
        print('     - unique_id: ' + self.unique_id)
        print('     - admin_status: ' + self.admin_status)
        print('     - link_status: ' + self.link_status)
        print('     - mtu: ' + str(self.mtu))
        print('     - interface_type: ' + self.interface_type)
        print('     - connected_switch_type: ' + self.connected_switch_type)
        print('     - type: ' + self.type)
        print('     - ressource_type: ' + self.resource_type)
        print('     - node_name: ' + self.parent_object.name)
        print('     - node_type: ' + self.parent_object.type)
        print('     - call_variable_id: ' + self.call_variable_id)
        self.call.viewCommand()
