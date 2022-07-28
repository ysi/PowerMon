#!/opt/homebrew/bin/python3

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
from pathlib import Path
from lib import color
import os, pprint

def influxConnection():
    # Load .env file
    dotenv_path = Path('../.env')
    load_dotenv(dotenv_path=dotenv_path)
    influxurl = "http://" + os.getenv('INFLUXDB_NAME')  + ":" + os.getenv('INFLUXDB_PORT')
    influxtoken = os.getenv('INFLUXDB_TOKEN')
    influxorg = os.getenv('INFLUXDB_ORG')
    influxbucket = os.getenv('INFLUXDB_DB')

    # Connect to InfluxDB
    client = InfluxDBClient(url=influxurl, token=influxtoken, org=influxorg)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    return (write_api, influxbucket, influxorg)

def influxWrite(writeinflux, bucket, org, data):
    print(color.style.GREEN + "Writing Data on Influxdb " + color.style.NORMAL)
    writeinflux.write(bucket, org, data)