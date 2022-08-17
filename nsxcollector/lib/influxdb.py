#!/opt/homebrew/bin/python3

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from lib import color
import sys, logging
from lib.formatDatas import Edge_Int_Data, Manager_CPU_Process_Data, Manager_Cluster_Data, Edge_CPU_Data

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

        Args
        ----------
        dictenv (dict): environment object
        args (obj): agrument object
        """
        influxurl = "http://" + self.host + ":" + self.port
        # Connect to InfluxDB
        result = None
        while result is None:
            print(color.style.RED + "==> " + color.style.NORMAL + " Trying to connect to InfluxDB: " + influxurl + color.style.NORMAL)
            try:
                log = color.style.RED + "==> " + color.style.NORMAL + "Connecting to InfluxDB: " + influxurl + " - " + color.style.GREEN + "Ok" + color.style.NORMAL
                client = InfluxDBClient(url=influxurl, token=self.token, org=self.org)
                self.api = client.write_api(write_options=SYNCHRONOUS)
                # Test list Bucket to check if Influxdb is up and running
                buckets_api = client.buckets_api()
                result = buckets_api.find_buckets()
                logging.info(log)
            except Exception as esx:
                logging.debug(esx)
                print(color.style.RED + "ERROR: " + color.style.NORMAL + "Error when connecting to InfluxDB: trying again")

    def influxWrite(self, tn, cmd, json):
        """
        influxWrite(tn , cmd, result)
        Format and write result of a json to influxdb

        Args
        ----------
        tn : ip of TN
        cmd : Commands Object
        json: result of the command
        """
        logging.debug("Format Data for writing in Inflxdb")
        logging.info("Format Data for writing in Inflxdb")
        function_name = globals()[cmd.format_function]
        format_data = function_name(tn, json)
        try:
            logging.debug("Writing Data on Influxdb: " + ', '.join(format_data))
            logging.info("Writing Data on Influxdb: " + ', '.join(format_data))
            self.api.write(self.bucket, self.org, format_data)
        except Exception as esx:
            print(color.style.RED + "ERROR: " + color.style.NORMAL + "Error while writing to InfluxDB")
            logging.info(esx)
