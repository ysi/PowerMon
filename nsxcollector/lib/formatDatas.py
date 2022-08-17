#!/opt/homebrew/bin/python3
import logging
from lib import tools

def Manager_CPU_Process_Data(host, json):
    # Format result of call api /v1/systemhealth/appliances/process/status
    Tab_result = []
    if json['result_count'] >= 1:
      for item in json['results']:
        for pc in item['top_process_by_cpu_list']:
            cpu = "Process,host=" + host + ",process=" + pc['user'] + " cpu_usage=" + str(pc['cpu_usage']) + ",memory_usage=" + str(pc['memory_usage'])
            Tab_result.append(cpu)

    return Tab_result

def Manager_Cluster_Data(host, json):
    # Format result of call api /api/v1/cluster/status
    Tab_result = []
    # Value for Control Cluster STATUS
    if isinstance(json, dict) and 'control_cluster_status' in json:
        status = "CC-Status,host="+host+" status=\""+ json["control_cluster_status"]["status"]+"\""
        Tab_result.append(status)
    # Value for Management Cluster STATUS & Management Cluster Number nodes UP
    if isinstance(json, dict) and 'mgmt_cluster_status' in json:
        status = "MC-Status,host="+host+" status=\""+ json["mgmt_cluster_status"]["status"]+"\""
        Tab_result.append(status)
        nodes_up = "MC-Nodes,host="+host+" UP="+ str(len(json["mgmt_cluster_status"]["online_nodes"])) + ",DOWN="+str(len(json["mgmt_cluster_status"]["offline_nodes"]))
        Tab_result.append(nodes_up)
    # Value for Backup enabled
    if isinstance(json, dict) and 'backup_enabled' in json:
        status = "BKP-Config,host="+host+" enabled="+str(json["backup_enabled"])
        Tab_result.append(status)
    # Value for Backup scheduled
    if isinstance(json, dict) and 'backup_schedule' in json:
        status = "BKP-Config,host="+host+" schedule=\""+json["backup_schedule"]["resource_type"]+"\""
        Tab_result.append(status)
    # Value for Last backup
    if isinstance(json, dict) and 'cluster_backup_statuses' in json and len(json["cluster_backup_statuses"])>0:
        status = "BKP-LastStatus,host="+host+" status="+str(json["cluster_backup_statuses"][0]["success"])
        Tab_result.append(status)
    else:
        status = "BKP-LastStatus,host="+host+" status=False"
        Tab_result.append(status)

    # Manager Services Treatment
    # Loop

    if isinstance(json, dict) and 'detailed_cluster_status' in json:
        for group in json['detailed_cluster_status']['groups']:
            status = group['group_type'] + ",host=" + host + " STATE=\""+ group['group_status'] +"\""
            Tab_result.append(status)

    return Tab_result

def Edge_Int_Data(host, json, Writing=False):
    # Format 'get logical-routers', 'get logical-routers ID interfaces stats'
    # if Writing at True - return a ID for another call
    Tab_result = []
    if not Writing:
        for item in json:
            if isinstance(item, dict) and 'type' in item and 'SERVICE_ROUTER_TIER0' in item['type']:
                Tab_result.append(item['uuid'])
        return Tab_result
    else:
        if 'SERVICE_ROUTER_TIER0' in json:
            for port in json['SERVICE_ROUTER_TIER0']['ports']:
                if port['ptype'] == 'uplink':
                    uplink = "Router,host=" + host + ",router=" + json['SERVICE_ROUTER_TIER0']['name'] + ",uplink=" + port['name'] + " rx=" + str(port['stats']['rx_bytes']) + ",rx_drops=" + str(port['stats']['rx_drops']) + ",tx=" + str(port['stats']['tx_bytes']) + ",tx_drops=" + str(port['stats']['tx_drops'])
                    Tab_result.append(uplink)
            return Tab_result


def Edge_CPU_Data(host, json):
    # Format 'get get cpu-stats'
    # if Writing at True - return a ID for another call
    Tab_result = ["Router,host=" + host + " cpu_usage=" + json['summary'][7].split(':')[1].replace(" ", "")]
    return Tab_result

def Edge_CPU_Panel(node, dashboard, grafana, result_json):
    logging.debug(node)


def Manager_Cluster_Panel(node, dashboard, grafana, result_json):
    """
    Manager_Cluster_Panel(node, dashboard, grafana, result_json)
    Create a panel for Manager_Cluster_Panel
    """
    # Panel Manager Status
    panel = dashboard.panel("NSX Manager Status", grafana.datasource_uid, grafana.datasource_bucket, 'stat')
    panel_parameters = {
        "name": "NSX Manager Status",
        "type": 'stat',
        "datasource_uid": grafana.datasource_uid,
        "datasource_bucket": grafana.datasource_bucket,
        "node_ip": node.ip_mgmt,
    } 
    panel.json_file = tools.renderPanel("NSX Manager Status", panel_parameters)
    dashboard.addPanel(panel)

    # Panel NSX Cluster services Status
    panel = dashboard.panel("NSX Services Status", grafana.datasource_uid, grafana.datasource_bucket, 'table')
    panel_parameters = {
        "name": "NSX Services Status",
        "type": 'table',
        "datasource_uid": grafana.datasource_uid,
        "datasource_bucket": grafana.datasource_bucket,
        "node_ip": node.ip_mgmt,
    } 
    panel.json_file = tools.renderPanel("NSX Services Status", panel_parameters)
    dashboard.addPanel(panel)
    return dashboard


def Manager_CPU_Process_Panel(node, dashboard, grafana, result_json):

    panel = dashboard.panel("Process CPU", grafana.datasource_uid, grafana.datasource_bucket, 'gauge')
    if result_json['result_count'] >= 1:
      for item in result_json['results']:
        i = 0
        list_process = []
        list_query = []
        for pc in item['top_process_by_cpu_list']:
            list_process.append(pc['user'].title())
            query_param = {
                "node_ip": node.ip_mgmt,
                "process": pc['user'],
                "label": pc['user'].title()
            }
            list_query.append(query_param)

        panel_parameters = {
            "name": "NSX Process Status",
            "type": 'gauge',
            "datasource_uid": grafana.datasource_uid,
            "datasource_bucket": grafana.datasource_bucket,
            "query": list_query,
            "list_process": list_process
        } 

        panel.json_file = tools.renderPanel("Process CPU", panel_parameters)
        dashboard.addPanel(panel)
        return dashboard

def Edge_Int_Panel(node, dashboard, grafana, result_json):

    if 'SERVICE_ROUTER_TIER0' in result_json:
        for port in result_json['SERVICE_ROUTER_TIER0']['ports']:
            if port['ptype'] == 'uplink':
                uplink_name = port['name']
                # construct infludb query
                query = "from(bucket: \"" +  grafana.datasource_bucket + "\")\n \
                        |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  \
                        |> filter(fn: (r) => r[\"_measurement\"] == \"Router\")\n  \
                        |> filter(fn: (r) => r[\"_field\"] == \"rx\" or r[\"_field\"] == \"tx\")\n  \
                        |> filter(fn: (r) => r[\"host\"] == \"" + node.ip_mgmt + "\")\n  \
                        |> filter(fn: (r) => r[\"router\"] == \"" + result_json['SERVICE_ROUTER_TIER0']['name'] + "\")\n  \
                        |> filter(fn: (r) => r[\"uplink\"] == \"" + port['name'] + "\")\n  \
                        |> aggregateWindow(every: v.windowPeriod, fn: last, createEmpty: false)\n  \
                        |> yield(name: \"last\")\n"
                panel = dashboard.panel("Edge: " + node.ip_mgmt + " - " + uplink_name, grafana.datasource_uid, grafana.datasource_bucket, 'timeseries')
                panel.addTarget("A", query)
                dashboard.addPanel(panel)

    return dashboard
