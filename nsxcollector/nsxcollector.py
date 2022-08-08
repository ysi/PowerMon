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
from itertools import cycle
from lib import tools, color, connection, influxdb, discovery, commands, transportnodes, grafana
from fabric import Connection, ThreadingGroup
from threading import current_thread
import numpy as np

def collectData(list,type_thread):
    # Connect in ssh on the group of Edge
    # list_edge = transportnodes.getEdge(tn)
    # edgeconnection = []
    # for host in list_edge:   
    #     edgeconnection.append(Connection(host=host.ip_mgmt, user=host.login, connect_kwargs={'password': host.password}))
    # EdgeGroup = ThreadingGroup.from_connections(edgeconnection)

    # Test what kind of threading
    if type_thread == 'Command':
        # print(current_thread().name + ": On " + color.style.GREEN + cmd.tn[0].ip_mgmt + color.style.NORMAL + " - Call " + color.style.GREEN + ', '.join(cmd.call) + color.style.NORMAL)
        for item in list:
            if item.type == 'API':
                connection.getAPIData(item, True, influx_write_api)

            # Passing commands on the group of Edge
            # if item.type == 'SSH':
            #     connection.getSSHData(EdgeGroup, item, influx_write_api)
            # Get API

    if type_thread == 'Node':
        logging.debug(list)

    # EdgeGroup.close()



def run_threaded(job_func, cmd, type_thread, index):
    # Create a thread
    job_thread = threading.Thread(name=type_thread + ' Thread_' + str(index), target=job_func, args=(cmd,type_thread,))
    job_thread.start()

def createSchedule(thread_config, List):

    i = cycle(List)
    # Global Thread configuration 
    print(color.style.RED + "-- ==> Type of threading: " + color.style.NORMAL + thread_config['type'])
    print(color.style.RED + "-- ==> Nb of asking threads : " + color.style.NORMAL + str(thread_config['nb_thread']))

    # Commands less than thread => only one thread
    if len(List) < thread_config['nb_thread']:
        print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Create only one Thread")
        schedule.every(thread_config['polling']).seconds.do(run_threaded, collectData, cmd=List, type_thread=thread_config['type'] ,index=1)

    # Commands equal thread => 1 command per Thread - MAX Thread = 16
    elif len(List) == thread_config['nb_thread'] and len(List) <= 16:   
        print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Create " + str(len(List)) +  " Thread")
        splits = np.array_split(List,thread_config['nb_thread'])
        index = 1
        for array in splits:
            schedule.every(thread_config['polling']).seconds.do(run_threaded, collectData, cmd=array, type_thread=thread_config['type'], index=index)
            index += 1

    # Commands upper thread => create number of thread in config file - MAX Thread = 16
    elif len(List) > thread_config['nb_thread'] and len(List) <= 16:
        nb_thread = thread_config['nb_thread']
        if len(List) == 16:
            nb_thread == 16
            print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Maximum thread reach - Create " + str(nb_thread) +  " Thread")
        else:
            print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Create " + str(nb_thread) +  " Thread")

        splits = np.array_split(List,nb_thread)
        index = 1
        for array in splits:
            schedule.every(thread_config['polling']).seconds.do(run_threaded, collectData, cmd=array, type_thread=thread_config['type'], index=index)
            index += 1

    else:
        print(color.style.RED + "ERROR: " + color.style.NORMAL + "Thread configuration issue")
        sys.exit()



def main():
    global influx_write_api
    print("Welcome to PowerMon")
    parser = argparse.ArgumentParser(description='PowerMon', add_help=False)
    parser.add_argument( '-d', '--debug', help="Print lots of debugging statements", action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # read config file
    config = tools.readYML('./config/config.yml')
    # Load .env file
    dictenv = tools.readENV()
    # Create connection with InfluxDB
    influx_write_api = influxdb.influxConnection(dictenv)
    # Connect to NSX and Get Transport Nodes: Create List of Nodes and Commands
    ListTN, ListAllCmds = discovery.discovery(config)
    # Create Grafana Environment (Folder + Dashboard + Panels)
    # Test all commands, and create grafana panels associated
    grafana.createGrafanaEnv(config, dictenv, ListTN)

    try:
        # check type of thread
        # Create Thread depend on type of thread
        if config['Thread']['type'] == 'Command':
            createSchedule(config['Thread'], ListAllCmds)
        if config['Thread']['type'] == 'Node':
            logging.debug(ListTN)
            createSchedule(config['Thread'], ListTN)
        # Start thread
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as error:
        print(color.style.RED + "ERROR: " + color.style.NORMAL + str(error))

if __name__ == "__main__":
    main()