#!/opt/homebrew/bin/python3
from lib import connection, color, tools
from lib.formatDatas import panelManagerProcess
from fabric import Connection
import sys, pprint


class grafana:
    datasource_uid = ''
    folders = []
    dashboards = []
    def __init__(self, name):
        self.name = name

    def createFolder(self, folder_name, uid):
        self.folders.append(folder(folder_name, uid))

    def createDashboard(self, name, folder_uid):
        db = dashboard(name, folder_uid)
        self.folders.append(db)
        return db

    def getFolderUID(self, name):
        # return folder UID by the name
        for fd in self.folders:
            if fd.name == name:
                return fd.uid

    def getInfluxDataSourceUID(self, dictenv):
        """
        Get the UID of the influxDB Datasource
        """
        grafanaport = dictenv['GRAFANA_PORT']
        grafanaurl = "http://" + dictenv['GRAFANA_NAME'] + ":" + grafanaport
        grafanalogin = dictenv['GRAFANA_ADMIN_USER']
        grafanapassword = dictenv['GRAFANA_ADMIN_PASSWORD']

        url = grafanaurl + '/api/datasources/name/' + dictenv['INFLUXDB_DOCKER_CONTAINER_NAME']
        response, code = connection.GetAPIGeneric(url, grafanalogin, grafanapassword, False)
        if code != 200:
            print(color.style.RED + "==> ERROR: " + color.style.NORMAL + "Grafana - Datasource " + dictenv['INFLUXDB_DOCKER_CONTAINER_NAME'] + " not found")
            sys.exit()
        else:
            self.datasource_uid = response['uid']

# Object Class for Grafana Dashboard
class dashboard:
    uid = ''
    panels = []
    # init method or constructor
    def __init__(self, name, folder):
        self.name = name
        self.folder = folder

    def addPanel(self, panel):
        self.panels.append(panel)

    def applyDashboard(self, dictenv, panels):
        """
        applyDashboard(dictenv, folder, panels)
        Apply dashboard object in Grafana by REST/API

        Args
        ----------
        dictenv : .env dictionary
        folder: folder uid
        panels: list of panels in dashboard
        """
        grafanaport = dictenv['GRAFANA_PORT']
        grafanaurl = "http://" + dictenv['GRAFANA_NAME'] + ":" + grafanaport
        grafanalogin = dictenv['GRAFANA_ADMIN_USER']
        grafanapassword = dictenv['GRAFANA_ADMIN_PASSWORD']
        url = grafanaurl + '/api/dashboards/db'
        self.uid = self.name.replace(' ', '')
        body = {
                "dashboard": {
                "title": self.name,
                "panels": panels,
                "uid": self.uid,
                "tags": [ "powermon" ],
                "timezone": "browser",
                "schemaVersion": 16,
                "version": 0,
                "refresh": "25s"
                },
                "folderUid": self.folder,
                "message": "Created by PowerMon",
                "overwrite": False
        }
        resul, code = connection.GetAPIGeneric(grafanaurl + '/api/dashboards/uid/' + self.uid, grafanalogin, grafanapassword, False)
        if code != 200:
            connection.PostAPIGeneric(url, grafanalogin, grafanapassword, body, True, 'Grafana', 'Create Dashboard ' + self.name)
        else:
            print(color.style.RED + "==> " + color.style.NORMAL + "Grafana - Dashboard " + self.name + " already existing")
        
        return self.uid


# Object Class for Grafana Folder
class folder:
    dashboard = ''
    def __init__(self, name, uid):
        self.uid = uid
        self.name = name

    def applyFolder(self, dictenv):
        """
        applyFolder(dictenv)
        apply in grafana a folder by request API

        Args
        ----------
        dictenv : .env dictionary
        """
        body = {
            "uid": self.uid,
            "title": self.name
        }
        grafanaport = dictenv['GRAFANA_PORT']
        grafanaurl = "http://" + dictenv['GRAFANA_NAME'] + ":" + grafanaport
        grafanalogin = dictenv['GRAFANA_ADMIN_USER']
        grafanapassword = dictenv['GRAFANA_ADMIN_PASSWORD']
        url = grafanaurl + '/api/folders'

        result, code = connection.GetAPIGeneric(url + '/' + self.uid, grafanalogin, grafanapassword, False)
        if code != 200:
            connection.PostAPIGeneric(url, grafanalogin, grafanapassword, body, True, 'Grafana', 'Create folder ' + self.name)
        else:
            print(color.style.RED + "==> " + color.style.NORMAL + "Grafana - Folder " + self.name + " already existing")


# Object Class for Grafana Panel
class panel:
    def __init__(self, title):
        self.title = title


def createGrafanaEnv(config, dictenv, ListTN, Commands_List):
    """
    createGrafanaEnv(dictenv, ListTN)
    Create the grafana environnement: Folder and Dashboards

    Args
    ----------
    dictenv : .env dictionary
    ListTN : List of Transport Node Object
    """

    # init grafana object
    gf = grafana('PowerMon')
    # Create Folder
    gf.createFolder(dictenv['COMPOSE_PROJECT_NAME'], 'PowerMonPowerMon')
    for fd in gf.folders:
        fd.applyFolder(dictenv)
    gf.getInfluxDataSourceUID(dictenv)

    # Create list of type of equipment
    Component = []
    for TN in ListTN:
        if TN.type == 'HostNode' and 'ESXi hosts' not in Component: Component.append('ESXi hosts')
        if TN.type == 'EdgeNode' and 'NSX Edges' not in Component: Component.append('NSX Edges')
        if TN.type == 'Manager' and 'NSX Managers' not in Component: Component.append('NSX Managers')

    # First create panel for each commands
    panels =[]
    for tn in ListTN:
        if tn.type == 'Manager' and 'NSX Managers' not in Component: 
            Component.append('NSX Managers')
            # Create panels for each commands and each Component
        if tn.type == 'Manager':
            panels = createPanel(tn.cmd, gf.datasource_uid, dictenv['INFLUXDB_DB'], config)
    
    # Create Dasboard for each type of component
    fd_uid = gf.getFolderUID(dictenv['COMPOSE_PROJECT_NAME'])
    for cp in Component:
        db = gf.createDashboard(cp,fd_uid)
        db.applyDashboard(dictenv, panels)



def createPanel(Commands_List, influxdbuid, infludbname, config):
    # Test all commands and create panel
    for cmd in Commands_List:
        for tn in cmd.tn:
            if cmd.type == 'SSH':
                connect = Connection(host=tn.ip_mgmt, user=tn.login, connect_kwargs={'password': tn.password})
                output = connect.run(cmd.call[0] + ' | json', hide=True, warn=True)
                if output.stderr == '':
                    print(color.style.RED + "==> " + color.style.NORMAL + "Testing command: " + cmd.call[0] + " - " + color.style.GREEN + "Ok" + color.style.NORMAL)
                    result_tmp = tools.formatResultSSH(output.stdout, False)
                    # pprint.pprint(result_tmp)
                else:
                    print(color.style.RED + "ERROR: " + color.style.NORMAL + "Command " + cmd.call[0] + " in "  + tn.ip_mgmt + " is not working" + color.style.NORMAL)
                    sys.exit()
            if cmd.type == 'API':
                port = ''
                if str(config['Manager']['port']) != '':
                    port = ':' + str(config['Manager']['port'])
                url = "https://" + config['Manager']['fqdn'] + port + cmd.call[0]
                tn_json, code = connection.GetAPIGeneric(url, config['Manager']['login'], config['Manager']['password'], False)
                if code == 200:
                    print(color.style.RED + "==> " + color.style.NORMAL + "Testing command: " + cmd.call[0] + " - " + color.style.GREEN + "Ok" + color.style.NORMAL)
                    # Call format function of a call
                    function_name = globals()[cmd.panel_function]
                    # print(cmd.panel_function, function_name)
                    format_data = function_name(cmd.tn[0].ip_mgmt, influxdbuid, infludbname, tn_json)
                    # print(format_data)
                    return format_data
                else:
                    print(color.style.RED + "ERROR: " + color.style.NORMAL + "Command " + cmd.call[0] + " in "  + tn.ip_mgmt + " is not working" + color.style.NORMAL)
                    sys.exit()
