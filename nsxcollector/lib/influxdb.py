#!/opt/homebrew/bin/python3

from influxdb_client import InfluxDBClient, Bucket
from influxdb_client.client.write_api import SYNCHRONOUS
from lib import color
import sys, logging
from lib.formatDatas import Edge_Int_Data, Manager_CPU_Process_Data, Manager_Cluster_Data, Edge_CPU_Data


def influxConnection(dictenv, args):
    """
    influxConnection(dictenv , args)
    Connecting test to influxDB

    Args
    ----------
    dictenv (dict): environment object
    args (obj): agrument object
    """
    if args.standalone:
        host = "localhost"
    else:
        host = dictenv['INFLUXDB_NAME']

    influxurl = "http://" + host + ":" + dictenv['INFLUXDB_PORT']
    influxtoken = dictenv['INFLUXDB_TOKEN']
    influxorg = dictenv['INFLUXDB_ORG']
    influxbucket = dictenv['INFLUXDB_DB']

    # Connect to InfluxDB
    try:
        client = InfluxDBClient(url=influxurl, token=influxtoken, org=influxorg)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        # Test list Bucket to check if Influxdb is up and running
        buckets_api = client.buckets_api()
        buckets_api.find_buckets()
        log = color.style.RED + "==> " + color.style.NORMAL + "Connecting to InfluxDB - " + color.style.GREEN + "Ok" + color.style.NORMAL
        logging.info(log)
        logging.debug(log)
        return (write_api, influxbucket, influxorg)
    except:
        print(color.style.RED + "ERROR: " + color.style.NORMAL + "Error when connecting to InfluxDB: exiting")
        sys.exit()

def influxWrite(tn, cmd, json, influxflow, bucket, org):
    """
    influxWrite(tn , cmd, result, influxflow, bucket, org)
    Format and write result of a json to influxdb

    Args
    ----------
    tn : ip of TN
    cmd : Commands Object
    json: result of the command
    influxflow: influx api
    bucket :bucket to write in Influxdb
    org : org in influxdb
    """
    logging.debug("Format Data for writing in Inflxdb")
    logging.info("Format Data for writing in Inflxdb")
    function_name = globals()[cmd.format_function]
    format_data = function_name(tn, json)
    try:
        logging.debug("Writing Data on Influxdb: " + ', '.join(format_data))
        logging.info("Writing Data on Influxdb: " + ', '.join(format_data))
        influxflow.write(bucket, org, format_data)
    except Exception as esx:
        print(color.style.RED + "ERROR: " + color.style.NORMAL + "Error while writing to InfluxDB")
        logging.info(esx)
