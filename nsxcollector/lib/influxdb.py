#!/opt/homebrew/bin/python3

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from lib import color
import logging
from threading import current_thread

class influxdb:
    api = None
    def __init__(self, host, port, org, token, bucket, name):
        self.host = host
        self.port = port
        self.org = org
        self.token = token
        self.bucket = bucket
        self.name = name

    def influxConnection(self):
        """
        influxConnection()
        Connecting test to influxDB
        """
        influxurl = "http://" + self.host + ":" + self.port
        # Connect to InfluxDB
        result = None
        while result is None:
            print(color.style.RED + "==> " + color.style.NORMAL + " Trying to connect to InfluxDB: " + influxurl + color.style.NORMAL)
            try:
                client = InfluxDBClient(url=influxurl, token=self.token, org=self.org)
                self.api = client.write_api(write_options=SYNCHRONOUS)
                # Test list Bucket to check if Influxdb is up and running
                buckets_api = client.buckets_api()
                result = buckets_api.find_buckets()
            except Exception as esx:
                logging.debug(esx)
                print(color.style.RED + "ERROR: " + color.style.NORMAL + "Error when connecting to InfluxDB: trying again")

        print(color.style.RED + "==> " + color.style.NORMAL + "Connection to InfluxDB: "  + color.style.GREEN + "Established" + color.style.NORMAL)

    def influxWrite(self, cmd, json):
        """
        Format and write result of a json to influxdb

        Args
        ----------
        cmd : Commands Object
        json: result of the command
        """
        function_name = globals()[cmd.influxdbfunction]
        format_data = function_name(cmd.node, json)
        try:
            logging.debug(current_thread().name + ": Writing Data on Influxdb: " + ', '.join(format_data))
            logging.info(current_thread().name + ": Writing Data on Influxdb: " + ', '.join(format_data))
            self.api.write(self.bucket, self.org, format_data)
        except Exception as esx:
            print(color.style.RED + "ERROR: " + color.style.NORMAL + "Error while writing to InfluxDB")
            logging.info(esx)


def cluster_status_data(nsx_object, json):
    # Format result of call api /api/v1/cluster/status
    Tab_result = []
    # Value for Control Cluster STATUS
    if isinstance(json, dict) and 'control_cluster_status' in json:
        status = "CC-Status,cluster="+nsx_object.id+" status=\""+ json["control_cluster_status"]["status"]+"\""
        Tab_result.append(status)
    # Value for Management Cluster STATUS & Management Cluster Number nodes UP
    if isinstance(json, dict) and 'mgmt_cluster_status' in json:
        status = "MC-Status,cluster="+nsx_object.id+" status=\""+ json["mgmt_cluster_status"]["status"]+"\""
        Tab_result.append(status)
        nodes_up = "MC-Nodes,cluster="+nsx_object.id+" UP="+ str(len(json["mgmt_cluster_status"]["online_nodes"])) + ",DOWN="+str(len(json["mgmt_cluster_status"]["offline_nodes"]))
        Tab_result.append(nodes_up)
    # Value for Backup enabled
    if isinstance(json, dict) and 'backup_enabled' in json:
        status = "BKP-Config,host="+nsx_object.id+" enabled="+str(json["backup_enabled"])
        Tab_result.append(status)
    # Value for Backup scheduled
    if isinstance(json, dict) and 'backup_schedule' in json:
        status = "BKP-Config,host="+nsx_object.id+" schedule=\""+json["backup_schedule"]["resource_type"]+"\""
        Tab_result.append(status)
    # Value for Last backup
    if isinstance(json, dict) and 'cluster_backup_statuses' in json and len(json["cluster_backup_statuses"])>0:
        status = "BKP-LastStatus,host="+nsx_object.id+" status="+str(json["cluster_backup_statuses"][0]["success"])
        Tab_result.append(status)
    else:
        status = "BKP-LastStatus,host="+nsx_object.id+" status=False"
        Tab_result.append(status)
    # Process
    if isinstance(json, dict) and 'detailed_cluster_status' in json:
        for group in json['detailed_cluster_status']['groups']:
            for member in group['members']:
                status = group['group_type'] + ",host=" + member['member_ip'] + " STATE=\""+ group['group_status'] +"\""
                Tab_result.append(status)
    
    return Tab_result


def t0_int_stats_data(nsx_object, json):
    # get router name
    return ["Bandwidth," + nsx_object.node_type + "=" + nsx_object.node_name + ",interface=" + nsx_object.name + " rx=" + str(json['per_node_statistics'][0]['rx']['total_bytes']) + ",tx=" + str(json['per_node_statistics'][0]['tx']['total_bytes'])]


def tn_int_stats_data(nsx_object, json):
    return ["Bandwidth," + nsx_object.node_type + "=" + nsx_object.node_name + ",interface=" + json['interface_id'] + " rx=" + str(json['rx_bytes']) + ",tx=" + str(json['tx_bytes'])]

def t0_bgp_data(nsx_object, json):
    print(json)
    return []
