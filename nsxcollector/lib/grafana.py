#!/opt/homebrew/bin/python3
from lib import connection, color
from lib.panels import simplePanel
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

    def testGrafana(self):
        """
        Connectivity test for Grafana
        """
        influxurl = "http://" + self.host + ":" + self.port
        code = 0
        while code != 200:
            print(color.style.RED + "==> " + color.style.NORMAL + "Trying to connect to Grafana: " + influxurl + color.style.NORMAL)
            result, code = connection.GetAPIGeneric(influxurl + '/api/folders', self.login, self.password)
            if code != 200:
                print(color.style.RED + "ERROR: " + color.style.NORMAL + "Error when connecting to Grafana: trying again")
        
        print(color.style.RED + "==> " + color.style.NORMAL + "Connection to Grafana: "  + color.style.GREEN + "Established" + color.style.NORMAL)


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
        apply in grafana a folder by request API
        Args
        ----------
        folderuid (str)
        foldername (str)
        """
        body = {
            "uid": folderuid,
            "title": foldername
        }
        url = "http://" + self.host + ":" + self.port + '/api/folders'
        result, code = connection.GetAPIGeneric("http://" + self.host + ":" + self.port + '/api/folders/' + folderuid, self.login, self.password)
        if code != 200:
            connection.PostAPIGeneric(url, self.login, self.password, body, True, 'Grafana', 'Create folder ' + foldername)
        else:
            print(color.style.RED + "==> " + color.style.NORMAL + "Grafana - Folder " + foldername + " already existing")


    def applyDashboard(self, folderuid, dboject):
        """
        Apply dashboard object in Grafana by REST/API
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
        def __init__(self, name, folder):
            self.name = name
            self.uid = name.replace(' ', '')
            self.folder = folder
            self.panels = []

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
            def __init__(self, title, type):
                self.title = title
                self.type = type
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


def createGrafanaEnv(args, config, gf, InDB, infra):
    """
    createGrafanaEnv(config, dictenv, ListTN)
    Create the grafana environnement: Folder, Dashboards, Panels

    Args
    ----------
    args: agruments from command line
    config (dict): config dictionary
    gf (obj): grafana object
    InDB (obj): InfluxDB object
    infra (obj): Infrastructure Object
    """
    # init grafana object
    if args.standalone:
        host = "localhost"
    else:
        host = gf.name
    # Create Folder
    folder_uid = config['General']['Name_Infra'].replace(' ', '')
    folder = gf.folder(config['General']['Name_Infra'], folder_uid)
    gf.addFolder(folder)
    # Get DataSource ID
    for fd in gf.folders:
        gf.applyFolder(fd.uid, fd.name)
    # get datasource name and uid for InfluxDB
    gf.initDataSource(InDB.name, InDB.bucket)
    # Create Dashboards from config file
    for db in config['Grafana']['Dashboards']:
        dash = gf.dashboard(db['name'],gf.getFolderUID(config['General']['Name_Infra']))
        gf.addDashboard(dash)
        for pn in db['panels']:
            function_name = globals()[pn['panelfunction']]
            dash = function_name(pn['name'], pn['type'], infra, dash, gf)

    # Apply all Dashboards
    for db in gf.dashboards:
        gf.applyDashboard(gf.getFolderUID(config['General']['Name_Infra']), db)
    