#!/opt/homebrew/bin/python3
# coding: utf8
#
# -------------------------------------------------------------------------
# PowerMon                                        
# -------------------------------------------------------------------------
# Utilisation:
# './nsxcollector.py'
#
# -------------------------------------------------------------------------
# |  Version History                                                      |
# -------------------------------------------------------------------------
# version=0.1
# version_date='22/08/2022'
#
# 0.1: Version initiale

import sys, logging, argparse
from lib import tools, influxdb, discovery, grafana, thread, polling


def main():
    print("Welcome to PowerMon")
    parser = argparse.ArgumentParser(description='PowerMon', add_help=True)
    parser.add_argument( '-d', '--debug', help="Print lots of debugging statements", action="store_true")
    parser.add_argument( '-v', '--verbose', help="verbose mode for PowerMon", action="store_true")
    parser.add_argument( '-s', '--standalone', help="execute PowerMon outside a container", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    # read config file
    config = tools.readYML('./config/config.yml')
    # Load .env file
    dictenv = tools.readENV(args)
    if args.standalone:
        inDBhost = "localhost"
        grafanaHost = "localhost"
    else:
        inDBhost = dictenv['INFLUXDB_NAME']
        grafanaHost = dictenv['GRAFANA_NAME']
    # Read all panel config files

    # Create connection with InfluxDB and test connectivity
    inDB = influxdb.influxdb(inDBhost,dictenv['INFLUXDB_PORT'], dictenv['INFLUXDB_ORG'], dictenv['INFLUXDB_TOKEN'], dictenv['INFLUXDB_DB'], dictenv['INFLUXDB_DOCKER_CONTAINER_NAME'])
    inDB.influxConnection()
    # Create grafana object and test connectivity
    gf = grafana.grafana(grafanaHost, dictenv['GRAFANA_PORT'], dictenv['GRAFANA_ADMIN_USER'], dictenv['GRAFANA_ADMIN_PASSWORD'])
    gf.testGrafana()
    # Connect to NSX and Get Transport Nodes: Create List of Nodes and Commands
    infra = discovery.discovery(config)
    pollinglist = polling.PollingListCmds(infra)
    for i in pollinglist:
        i.viewCommand()
        
    sys.exit()

    # Create Grafana Environment (Folder + Dashboard + Panels)
    grafana.createGrafanaEnv(args, config, gf, inDB, infra)
    thread.threadmodule(infra, inDB)

if __name__ == "__main__":
    main()