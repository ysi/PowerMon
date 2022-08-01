#!/opt/homebrew/bin/python3

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from lib import color, grafana

def influxConnection(dictenv):
    # DEbug
    influxurl = "http://localhost:" + dictenv['INFLUXDB_PORT']
    influxtoken = dictenv['INFLUXDB_TOKEN']
    influxorg = dictenv['INFLUXDB_ORG']
    influxbucket = dictenv['INFLUXDB_DB']

    # Connect to InfluxDB
    try:
        client = InfluxDBClient(url=influxurl, token=influxtoken, org=influxorg)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        print(color.style.RED + "==> " + color.style.NORMAL + "Connecting to InfluxDB - " + color.style.GREEN + "Ok" + color.style.NORMAL)
        return (write_api, influxbucket, influxorg)
    except:
        print(color.style.RED + "Error when connecting to InfluxDB: exiting" + color.style.NORMAL)
        exit

def influxWrite(writeinflux, bucket, org, data):
    print(color.style.GREEN + "Writing Data on Influxdb " + color.style.NORMAL)
    writeinflux.write(bucket, org, data)
