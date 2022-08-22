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

import schedule, time, threading, sys, logging, argparse
from lib import tools, color, connection, influxdb, discovery, grafana
# from threading import current_thread
from collections import defaultdict

def collectData(infra, elementlist,inDB):
    """
    Collect data from a list of cmd and write into influxdb
    """
    # Test what kind of threading
    for item in elementlist:
        result_json, code = connection.GetAPIGeneric(infra.url_api + item.call, infra.cluster.members[0].login, infra.cluster.members[0].password)
        inDB.influxWrite(item, result_json)

        
def run_threaded(job_func, infra, listelement, index, inDB):
    """
    Create and run thread
    """
    # Create a thread
    job_thread = threading.Thread(name='Thread_' + str(index), target=job_func, args=(infra, listelement,inDB,))
    job_thread.start()

def createSchedule(infra, List, inDB):
    """
    Create scheduling
    """
    Num_Max_Thread = 16
    # Global Thread configuration 
    print(color.style.RED + "==> Total number of commands: " + color.style.NORMAL + str(len(List)))
    polling_groups = defaultdict(list)
    # Create list based on polling value
    for cmd in List:
        polling_groups[cmd.polling].append(cmd)

    new_list = polling_groups.items()
    print(color.style.RED + "==> Total of polling interval: " + color.style.NORMAL + str(len(new_list)))
    if len(new_list) <= Num_Max_Thread:
        for key, value in new_list:
            schedule.every(key).seconds.do(run_threaded, collectData, infra=infra, listelement=value, index=key, inDB=inDB)

    else:
        print(color.style.RED + "==> Maximum thread reach: " + color.style.NORMAL + " please reorganize your commands to have maximum 16 polling intervals")
        sys.exit()


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
    # Create connection with InfluxDB and test connectivity
    inDB = influxdb.influxdb(inDBhost,dictenv['INFLUXDB_PORT'], dictenv['INFLUXDB_ORG'], dictenv['INFLUXDB_TOKEN'], dictenv['INFLUXDB_DB'], dictenv['INFLUXDB_DOCKER_CONTAINER_NAME'])
    inDB.influxConnection()
    # Create grafana object and test connectivity
    gf = grafana.grafana(grafanaHost, dictenv['GRAFANA_PORT'], dictenv['GRAFANA_ADMIN_USER'], dictenv['GRAFANA_ADMIN_PASSWORD'])
    gf.testGrafana()
    # Connect to NSX and Get Transport Nodes: Create List of Nodes and Commands
    infra = discovery.discovery(config)
    # Create Grafana Environment (Folder + Dashboard + Panels)
    grafana.createGrafanaEnv(args, config, gf, inDB, infra)
    infra.viewInfra()
    try:
        AllCommands = infra.getCommandsPolling()
        print(AllCommands)
        createSchedule(infra, AllCommands, inDB)
        # Start thread
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as error:
        print(color.style.RED + "ERROR: " + color.style.NORMAL + str(error))
    

if __name__ == "__main__":
    main()