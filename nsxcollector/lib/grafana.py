#!/opt/homebrew/bin/python3
from lib import connection, color
from lib.formatDatas import Edge_Int_Panel, Manager_CPU_Process_Panel, Edge_CPU_Panel, Manager_Cluster_Panel, Edge_Int_Data
import sys, logging


class grafana:
    datasource_uid = ''
    datasource_bucket = ''
    folders = []
    dashboards = []
    type = ""
    name = ""
    def __init__(self, host, port, login, password):
        self.name = 'PowerMon'
        self.host = host
        self.port = port
        self.login = login
        self.password = password

    def addFolder(self, folder):
        self.folders.append(folder)

    def addDashboard(self, db):
        self.dashboards.append(db)

    def getDashboard(self, name):
        for db in self.dashboards:
            if name == db.name:
                return db

    def getFolderUID(self, name):
        # return folder UID by the name
        for fd in self.folders:
            if fd.name == name:
                return fd.uid

    def initDataSource(self, influxdb_name, influxdb_bucket):
        """
        initialize the datasource name and UID
        """
        url = "http://" + self.host + ":" + self.port + '/api/datasources/name/' + influxdb_name
        response, code = connection.GetAPIGeneric(url, self.login, self.password)
        if code != 200:
            print(color.style.RED + "==> ERROR: " + color.style.NORMAL + "Grafana - Datasource " + influxdb_name + " not found")
            sys.exit()
        else:
            self.datasource_uid = response['uid']
            self.datasource_bucket = influxdb_bucket


    def applyFolder(self, folderuid, foldername):
        """
        applyFolder(dictenv)
        apply in grafana a folder by request API
        Args
        ----------
        dictenv : .env dictionary
        """
        body = {
            "uid": folderuid,
            "title": foldername
        }
        url = "http://" + self.host + ":" + self.port + '/api/folders'
        result, code = connection.GetAPIGeneric("http://" + self.host + ":" + self.port + '/api/folders/' + folderuid, self.login, self.password)
        if code != 200:
            connection.PostAPIGeneric(url, self.login, self.password, body, True, 'Grafana', 'Create folder ' + self.name)
        else:
            print(color.style.RED + "==> " + color.style.NORMAL + "Grafana - Folder " + self.name + " already existing")


    def applyDashboard(self, folderuid, dboject):
        """
        applyDashboard(dictenv, )
        Apply dashboard object in Grafana by REST/API
        Args
        ----------
        dictenv : .env dictionary
        """
        grafanaurl = "http://" + self.host + ":" + self.port
        url = grafanaurl + '/api/dashboards/db'
        # construct Panel json
        list_panel = []
        for pn in dboject.panels:
            list_panel.append(pn.json_file)
            # list_panel.append(pn.createDictPanel())
        body = {
                "dashboard": {
                "title": dboject.name,
                "panels": list_panel,
                "uid": dboject.uid,
                "tags": [ "powermon" ],
                "timezone": "browser",
                "schemaVersion": 16,
                "version": 0,
                "refresh": "25s"
                },
                "folderUid": folderuid,
                "message": "Created by PowerMon",
                "overwrite": False
        }
        resul, code = connection.GetAPIGeneric(grafanaurl + '/api/dashboards/uid/' + dboject.uid, self.login, self.password)
        if code != 200:
            connection.PostAPIGeneric(url, self.login, self.password, body, True, 'Grafana', 'Create Dashboard ' + dboject.name)
        else:
            print(color.style.RED + "==> " + color.style.NORMAL + "Grafana - Dashboard " + dboject.name + " already existing")
        
        return dboject.uid


    # Object Class for Grafana Folder
    class folder:
        dashboard = ''
        def __init__(self, name, uid):
            self.uid = uid
            self.name = name


    # Object Class for Grafana Dashboard
    class dashboard:
        uid = ''
        panels = []
        # init method or constructor
        def __init__(self, name, folder, type):
            self.name = name
            self.uid = name.replace(' ', '')
            self.folder = folder
            self.panels = []
            self.type = type

        def addPanel(self, panel):
            self.panels.append(panel)



        class panel:
            uid = ''
            json_file = {}
            targets = []
            transformations = []
            fieldConfig = {}
            gridPos = {}
            options = {}
            # init method or constructor
            def __init__(self, title, influxdbuid, infludbname,type):
                self.title = title
                self.type = type
                self.influxdbuid = influxdbuid
                self.infludbname = infludbname
                self.targets = []
                self.fieldConfig = {}
                self.gridPos = {}
                self.options = {}

            def addTarget(self, id, query):
                target = {
                    'refId': id,
                    'datasource': {
                      "type": "influxdb",
                      "uid": self.influxdbuid
                    },
                    'query': query
                }
                self.targets.append(target)

            def createDictPanel(self):
                dictpanel = {
                    'type': self.type,
                    'title': self.title,
                    'options': self.options,
                    'targets': self.targets,
                    'transformations': self.transformations,
                    'fieldConfig': self.fieldConfig,
                    'gridPos': self.gridPos
                }
                return dictpanel


def createGrafanaEnv(args, config, dictenv, ListTN):
    """
    createGrafanaEnv(config, dictenv, ListTN)
    Create the grafana environnement: Folder, Dashboards, Panels

    Args
    ----------
    config (dict): config dictionary
    dictenv (dict): .env dictionary
    ListTN (list): List of Transport Node Object
    """
    # init grafana object
    if args.standalone:
        host = "localhost"
    else:
        host = dictenv['GRAFANA_NAME']
    gf = grafana(host, dictenv['GRAFANA_PORT'], dictenv['GRAFANA_ADMIN_USER'], dictenv['GRAFANA_ADMIN_PASSWORD'])
    # Create Folder
    folder_uid = config['General']['Name_Infra'].replace(' ', '')
    folder = gf.folder(config['General']['Name_Infra'], folder_uid)
    gf.addFolder(folder)
    # Get DataSource ID
    for fd in gf.folders:
        gf.applyFolder(fd.uid, fd.name)
    # get datasource name and uid for InfluxDB
    gf.initDataSource(dictenv['INFLUXDB_DOCKER_CONTAINER_NAME'], dictenv['INFLUXDB_DB'])
    # Add Dashboard for Overlay Stuff
    db_overlay = gf.dashboard('Overlay',gf.getFolderUID(config['General']['Name_Infra']), 'Overlay')
    gf.addDashboard(db_overlay)
    # Add Dashboard for Overlay Stuff
    db_security = gf.dashboard('Security',gf.getFolderUID(config['General']['Name_Infra']), 'Security')
    gf.addDashboard(db_security)    
    # Create Dashboard for each type of component
    for tn in ListTN:
        if len(tn.cmd) > 0:
            # Check if dashboard doesn't exist un grafana
            dash_exist = False
            for dash in gf.dashboards:
                if dash.type == tn.type:
                    dash_exist = True
            # Create Dashboard Object for NSX Manager
            if tn.type == 'Manager': 
                if not dash_exist:
                    dash = gf.dashboard('NSX Managers',gf.getFolderUID(config['General']['Name_Infra']), tn.type)
                    gf.addDashboard(dash)
                    tn.gf_dashboard = dash
                else:
                    tn.gf_dashboard = gf.getDashboard('NSX Managers')
            # Create Dashboard Object for NSX Edge
            if tn.type == 'EdgeNode':
                if not dash_exist:
                    dash =  gf.dashboard('Edge Nodes',gf.getFolderUID(config['General']['Name_Infra']), tn.type)
                    gf.addDashboard(dash)
                    tn.gf_dashboard = dash
                else:
                    tn.gf_dashboard = gf.getDashboard('Edge Nodes')
            # Create Dashboard Object for ESXi
            if tn.type == 'HostNode':
                if not dash_exist:
                    dash = gf.dashboard('Hosts',gf.getFolderUID(config['General']['Name_Infra']), tn.type)
                    gf.addDashboard(dash)
                    tn.gf_dashboard = dash
                else:
                    tn.gf_dashboard = gf.getDashboard('Hosts')


    # create panel for each TN
    for tn in ListTN:
        if tn.gf_dashboard is not None:
            # Loop inside all dashboards
            for db in gf.dashboards:
                if db == tn.gf_dashboard:
                    # Loop in all commands
                    for cmd in tn.cmd:
                        result = {}
                        # dual command process
                        if isinstance(cmd, list):
                            # get the first result of the command
                            for cd in cmd:
                                result = result | connection.sendCommand(tn, cd)

                            function_name = globals()[cmd[0].panel_function]
                            dash = function_name(tn, db, gf, result)

                        # one command process
                        else:
                            result = connection.sendCommand(tn, cmd)
                            # Call format function of a call
                            function_name = globals()[cmd.panel_function]
                            dash = function_name(tn, db, gf, result)

    # Apply all Dashboards
    for db in gf.dashboards:
        gf.applyDashboard(gf.getFolderUID(config['General']['Name_Infra']), db)
    
