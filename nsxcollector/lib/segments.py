#!/opt/homebrew/bin/python3
from lib import interfaces, connection, color
import logging

class Segment:
    type = ''
    admin_state = ''
    vlan_ids = []
    admin_state = ''
    connectivity = ''
    call = ''

    def __init__(self, name, id, unique_id):
        self.name = name
        self.id = id
        self.unique_id = unique_id
    
    def viewSegment(self):
        print('Information about Segment ' + self.name)
        print(' - id: ' + self.id)
        print(' - unique_id ' + self.unique_id)
        print(' - type: ' + self.type)
        print(' - vlans ' + ', '.join(self.vlan_ids))
        print(' - admin_state: ' + self.admin_state)
        print(' - connectivity: ' + self.connectivity)
        print(' - call: ')
        self.call.viewCommand()

