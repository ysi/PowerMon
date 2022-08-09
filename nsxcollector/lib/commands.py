#!/opt/homebrew/bin/python3

class cmd:
    tn = []
    panels = []
    # init method or constructor
    def __init__(self, name, type, nodetype, polling, call, timeout, panel_function, format_function):
        self.name = name
        self.type = type
        self.nodetype = nodetype
        self.polling = polling
        self.call = call
        self.timeout = timeout
        self.panel_function = panel_function
        self.format_function = format_function
        self.tn = []
        self.panels = []

    def updateCall(self, call):
        self.call = call

    def __getitem__(self, key): # this allows getting an element (overrided method)
        return self.tn[key]

def listName(list):
    listname = []
    for item in list:
        listname.append(item.name)
    return listname

def listCall(list):
    listcall = []
    for item in list:
        listcall.append(item.call)

    return listcall