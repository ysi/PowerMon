#!/opt/homebrew/bin/python3

class cmd:
    influxdbfunction = ""
    usedforPolling = False

    # init method or constructor
    def __init__(self, name, config_call, node, timeout):
        self.name = name
        self.polling = config_call['polling']
        self.node = node
        self.call = config_call['call']
        if 'influxdbfunction' in config_call:
            self.usedforPolling = True
            self.influxdbfunction = config_call['influxdbfunction']
        else:
            self.usedforPolling = False
            self.influxdbfunction = ""

        self.timeout = timeout

    def updateCall(self, call):
        self.call = call

    def __getitem__(self, key): # this allows getting an element (overrided method)
        return self.tn[key]

    def viewCommand(self):
        print(' - Command ' + self.name)
        print('     - polling: ' + str(self.polling))
        print('     - call: ' + self.call)
        print('     - timeout: ' + str(self.timeout))
        print('     - Use for Polling: ' + str(self.usedforPolling))
        print('     - influxdbfunction: ' + self.influxdbfunction)
        print('     - node: ' + self.node)
