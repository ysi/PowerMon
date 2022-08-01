#!/opt/homebrew/bin/python3
from lib import connection, color, tools
from lib.formatDatas import panelManagerProcess
from fabric import Connection
import sys, pprint

def createGrafanaEnv(config, dictenv, ListTN, Commands_List):
    """
    createGrafanaEnv(dictenv, ListTN)
    Create the grafana environnement: Folder and Dashboards

    Args
    ----------
    dictenv : .env dictionary
    ListTN : List of Transport Node Object
    """
    # Create Folder
    folder = createFolder(dictenv, dictenv['COMPOSE_PROJECT_NAME'])
    influxdbuid = getInfluxDataSourceUID(dictenv)

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
            panels = createPanel(tn.cmd, influxdbuid, dictenv['INFLUXDB_DB'], config)
    # Create Dasboard for each type of component
    for cp in Component:
        createGrafanaDashboard(dictenv, cp, folder, panels)



def createFolder(dictenv, folder):
    """
    createFolder(dictenv, folder)
    Create a grafana folder

    Args
    ----------
    dictenv : .env dictionary
    folder : name of the folder
    """
    grafanaport = dictenv['GRAFANA_PORT']
    grafanaurl = "http://" + dictenv['GRAFANA_NAME'] + ":" + grafanaport
    grafanalogin = dictenv['GRAFANA_ADMIN_USER']
    grafanapassword = dictenv['GRAFANA_ADMIN_PASSWORD']
    url = grafanaurl + '/api/folders'
    uid = 'PowerMonPowerMon'
    body = {
        "uid": uid,
        "title": folder
    }
    result, code = connection.GetAPIGeneric(url + '/' + uid, grafanalogin, grafanapassword, False)
    if code != 200:
        connection.PostAPIGeneric(url, grafanalogin, grafanapassword, body, True, 'Grafana', 'Create folder ' + folder)
    else:
        print(color.style.RED + "==> " + color.style.NORMAL + "Grafana - Folder " + folder + " already existing")

    return uid


def createGrafanaDashboard(dictenv, name, folderuid, panels):
    """
    createGrafanaDashboard(dictenv, name, folderuid)
    Create a dashboard inside a folder

    Args
    ----------
    dictenv : .env dictionary
    name : name of the dashboard
    folderuid : UID of the folder
    panels: list of panels in dashboard
    """
    grafanaport = dictenv['GRAFANA_PORT']
    grafanaurl = "http://" + dictenv['GRAFANA_NAME'] + ":" + grafanaport
    grafanalogin = dictenv['GRAFANA_ADMIN_USER']
    grafanapassword = dictenv['GRAFANA_ADMIN_PASSWORD']
    url = grafanaurl + '/api/dashboards/db'
    uid = name.replace(' ', '')
    body = {
            "dashboard": {
              "title": name,
              "panels": panels,
              "uid": uid,
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
    resul, code = connection.GetAPIGeneric(grafanaurl + '/api/dashboards/uid/' + uid, grafanalogin, grafanapassword, False)
    if code != 200:
        connection.PostAPIGeneric(url, grafanalogin, grafanapassword, body, True, 'Grafana', 'Create Dashboard ' + name)
    else:
        print(color.style.RED + "==> " + color.style.NORMAL + "Grafana - Dashboard " + name + " already existing")
    
    return uid


def getInfluxDataSourceUID(dictenv):
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
        return response['uid']


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
