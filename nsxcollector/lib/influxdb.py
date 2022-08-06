#!/opt/homebrew/bin/python3

from influxdb_client import InfluxDBClient, Bucket
from influxdb_client.client.write_api import SYNCHRONOUS
from lib import color
import sys, logging

def influxConnection(dictenv):
    logger = logging.getLogger()
    if logger.isEnabledFor(logging.DEBUG):
        influxurl = "http://localhost:" + dictenv['INFLUXDB_PORT']
    else:
        influxurl = "http://" + dictenv['INFLUXDB_NAME'] + ":" + dictenv['INFLUXDB_PORT']
    
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
        print(color.style.RED + "==> " + color.style.NORMAL + "Connecting to InfluxDB - " + color.style.GREEN + "Ok" + color.style.NORMAL)
        return (write_api, influxbucket, influxorg)
    except:
        print(color.style.RED + "ERROR: " + color.style.NORMAL + "Error when connecting to InfluxDB: exiting")
        sys.exit()

def influxWrite(writeinflux, bucket, org, data):
    logging.debug(data)
    print(color.style.GREEN + "Writing Data on Influxdb " + color.style.NORMAL)
    writeinflux.write(bucket, org, data)
