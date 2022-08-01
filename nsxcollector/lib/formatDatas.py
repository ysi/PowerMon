#!/opt/homebrew/bin/python3
import pprint

def processCPU(host, json, Writing=False):
    # Format result of call api/v1/systemhealth/appliances/process/status
    Tab_result = []
    if isinstance(json, dict) and 'results' in json and json['result_count'] > 0: 
        for rs in json["results"]:
            for pc in rs['top_process_by_cpu_list']:
                cpu = "Process,host=" + host + ",process=" + pc['user'] + " cpu_usage=" + str(pc['cpu_usage']) + ",memory_usage=" + str(pc['memory_usage'])
                Tab_result.append(cpu)

    return Tab_result


def processINT(host, json, Writing=False):
    # Format 'get logical-routers', 'get logical-routers ID interfaces stats'
    # if Writing at True - return a ID for another call
    Tab_result = []
    if not Writing:
        for item in json:
            if isinstance(item, dict) and 'type' in item and 'uuid' in item > 0 and 'ROUTER' in item['type']:
                Tab_result.append(item['uuid'])
        return Tab_result
    else:
        if 'SERVICE_ROUTER_TIER0' in json:
            for port in json['SERVICE_ROUTER_TIER0']['ports']:
                if port['ptype'] == 'uplink':
                    uplink = "Router,host=" + host + ",router=" + json['SERVICE_ROUTER_TIER0']['name'] + ",uplink=" + port['name'] + " rx=" + str(port['stats']['rx_bytes']) + ",rx_drops=" + str(port['stats']['rx_drops']) + ",tx=" + str(port['stats']['tx_bytes']) + ",tx_drops=" + str(port['stats']['tx_drops'])
                    Tab_result.append(uplink)
            return Tab_result


def panelEdgeCPU(Edge, influxdbuid,dictenv):
    """
    panelEdgeCPU(Edge)
    Create a panel for a component

    Args
    ----------
    edge: transport node object
    influxdbuid: influxdb uid
    dictenv: dictionary of environment variables
    """
    # construct infludb query
    query = "from(bucket: \"" +  dictenv['INFLUXDB_DB'] + "\")\n \
            |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  \
            |> filter(fn: (r) => r[\"_measurement\"] == \"Edge\")\n  \
            |> filter(fn: (r) => r[\"host\"] == \"" + Edge.ip_mgmt + "\")\n  \
            |> filter(fn: (r) => r[\"uplink\"] == \"tier0-interface-40-40-40-2\")\n  \
            |> filter(fn: (r) => r[\"_field\"] == \"rx\" or r[\"_field\"] == \"tx\")\n  \
            |> filter(fn: (r) => r[\"uplink\"] == \"tier0-interface-40-40-40-2\")\n  \
            |> aggregateWindow(every: v.windowPeriod, fn: last, createEmpty: false)\n  \
            |> yield(name: \"last\")\n"
    panel_dict = {
        'type': "timeseries",
        'title': "Panel Title",
        'targets': [
          {
            'refId': "A",
            'datasource': {
              "type": "influxdb",
              "uid": influxdbuid
            },
            'query': query
          }
        ]
    }

    return panel_dict


def panelManagerProcess(host, influxdbuid,infludbname, result):
    """
    panelEdgeCPU(Edge)
    Create a panel for a component

    Args
    ----------
    host: transport node object
    influxdbuid: influxdb uid
    infludbname: influxdb name
    result: json of command result
    """
    # Loop inside the result:
    List_Panel = []
    if result['result_count'] >= 1:
        for item in result['results']:
            for pc in item['top_process_by_cpu_list']:
                # construct infludb query
                query = "from(bucket: \"" +  infludbname + "\")\n \
                        |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  \
                        |> filter(fn: (r) => r[\"_measurement\"] == \"Process\")\n  \
                        |> filter(fn: (r) => r[\"_field\"] == \"cpu_usage\") \
                        |> filter(fn: (r) => r[\"host\"] == \"" + host + "\")\n  \
                        |> filter(fn: (r) => r[\"process\"] == \"" + pc['user'] + "\")\n  \
                        |> aggregateWindow(every: v.windowPeriod, fn: last, createEmpty: false)\n  \
                        |> yield(name: \"last\")\n"

                panel_dict = {
                        'type': "gauge",
                        'title': "Process CPU: " + pc['user'],
                        'targets': [
                          {
                            'refId': "A",
                            'datasource': {
                              "type": "influxdb",
                              "uid": influxdbuid
                            },
                            'query': query
                          }
                        ]
                    }
                List_Panel.append(panel_dict)

    return List_Panel