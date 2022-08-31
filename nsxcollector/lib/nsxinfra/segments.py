#!/opt/homebrew/bin/python3

class Segment:
    type = ''
    admin_state = ''
    vlan_ids = []
    admin_state = ''
    connectivity = ''
    call = ''
    call_variable_id = ''
    tz_path = ''

    def __init__(self, name, id, unique_id):
        self.name = name
        self.id = id
        self.unique_id = unique_id
        self.object_type = 'segment'
    
    def viewSegment(self):
        print('Information about Segment ' + self.name)
        print(' - object_type: ' + self.object_type)
        print(' - id: ' + self.id)
        print(' - unique_id ' + self.unique_id)
        print(' - type: ' + self.type)
        print(' - vlans ' + ', '.join(self.vlan_ids))
        print(' - admin_state: ' + self.admin_state)
        print(' - connectivity: ' + self.connectivity)
        print(' - tz_path: ' + self.tz_path)
        print(' - call_variable_id: ' + self.call_variable_id)
        self.call.viewCommand()

    def getTypeSegment(self, infra):
        for tz in infra.tz:
            if tz.path == self.tz_path:
                return tz.type

