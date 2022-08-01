#!/opt/homebrew/bin/python3

class cmd:

    panels = []
    # init method or constructor
    def __init__(self, name, type, interval, call, panel_function, format_function, TN):
        self.name = name
        self.type = type
        self.interval = interval
        self.call = call
        self.panel_function = panel_function
        self.format_function = format_function
        self.tn = TN

    def __eq__(self, other) : 
        return self.__dict__ == other.__dict__

def intervalListCmd(list, interval):
    # create a list of commands based on interval value
    listitem = []
    for item in list:
        if item.interval == interval:
            listitem.append(item)

    return listitem

def getListInterval(list):
    # create a list of interval
    interval_list = []
    for item in list:
        if item.interval not in interval_list:
            interval_list.append(item.interval)
    
    return interval_list


def createCommandList(config, ListTN):
    Commands_List = []
    for key, value in config.items():
        # Loop in commands
        for cd in value['commands']:
            tn_obj = []
            for tn in ListTN:
                if tn.type == value['type']:
                    tn_obj.append(tn)

            Commands_List.append(cmd(cd['name'], cd['type'], cd['interval'], cd['call'], cd['panelfunction'], cd['datafunction'], tn_obj))
    return Commands_List