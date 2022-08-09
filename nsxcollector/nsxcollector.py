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

from ast import List
import schedule, time, threading, sys, logging, argparse, pprint
from itertools import cycle
from lib import tools, color, connection, influxdb, discovery, commands, transportnodes, grafana
from fabric import Connection, ThreadingGroup
from threading import current_thread
import numpy as np

def collectData(elementlist,type_thread):
    # Connect in ssh on the group of Edge
    # list_edge = transportnodes.getEdge(tn)
    # edgeconnection = []
    # for host in list_edge:   
    #     edgeconnection.append(Connection(host=host.ip_mgmt, user=host.login, connect_kwargs={'password': host.password}))
    # EdgeGroup = ThreadingGroup.from_connections(edgeconnection)

    # Test what kind of threading
    if type_thread == 'GlobalCommands' or type_thread == 'PollingCommands':
        # print(current_thread().name + ": On " + color.style.GREEN + cmd.tn[0].ip_mgmt + color.style.NORMAL + " - Call " + color.style.GREEN + ', '.join(cmd.call) + color.style.NORMAL)
        for item in elementlist:
            if item.type == 'API':
                connection.getAPIData(item, True, influx_write_api)

    if type_thread == 'Node':
        # field all tn on command TN object.
        for node in elementlist:
            for cmd in node.cmd:
                if isinstance(cmd, list):
                    for call in cmd:
                        call.tn.append(node)
                else:
                    cmd.tn.append(node)
        # Connecting to Node and passing commands
        for node in elementlist:
            for cmd in node.cmd:
                if isinstance(cmd, list):
                    for call in cmd:
                        connection.getAPIData(call, True, influx_write_api)

                else:
                     connection.getAPIData(cmd, True, influx_write_api)
                
            
            # Passing commands on the group of Edge
            # if item.type == 'SSH':
            #     connection.getSSHData(EdgeGroup, item, influx_write_api)
            # Get API

    # if type_thread == 'Node':
    #     logging.debug(list)

    # EdgeGroup.close()



def run_threaded(job_func, cmd, type_thread, index):
    # Create a thread
    job_thread = threading.Thread(name=type_thread + ' Thread_' + str(index), target=job_func, args=(cmd,type_thread,))
    job_thread.start()

def createSchedule(thread_config, List):

    if thread_config['type'] == 'Node' or thread_config['type'] == 'GlobalCommands':
        threading_interval = thread_config['polling']

    logging.debug(List)
    # i = cycle(List)
    # Global Thread configuration 
    print(color.style.RED + "-- ==> Type of threading: " + color.style.NORMAL + thread_config['type'])
    print(color.style.RED + "-- ==> Nb of asking threads : " + color.style.NORMAL + str(thread_config['nb_thread']))

    # Elements less than thread => only one thread
    if len(List) < thread_config['nb_thread']:
        print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Create only one Thread")
        if thread_config['type'] == 'PollingCommands':
            threading_interval = List[0][0].polling
        schedule.every(threading_interval).seconds.do(run_threaded, collectData, cmd=List, type_thread=thread_config['type'] ,index=1)

    # Elements equal thread => 1 element per Thread - MAX Thread = 16
    elif len(List) == thread_config['nb_thread'] and len(List) <= 16:   
        splits = np.array_split(List,thread_config['nb_thread'])
        print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Create " + str(len(List)) +  " Thread of " + str(len(List)) + " " + thread_config['type'] + "(s)")
        index = 1
        if thread_config['type'] == 'PollingCommands':
            for element in List:
                schedule.every(element[0].polling).seconds.do(run_threaded, collectData, cmd=element, type_thread=thread_config['type'], index=element[0].polling)
        else:
            splits = np.array_split(List,thread_config['nb_thread'])
            for array in splits:
                schedule.every(threading_interval).seconds.do(run_threaded, collectData, cmd=array, type_thread=thread_config['type'], index=index)
                index += 1   

    # Elements upper thread => create number of thread in config file - MAX Thread = 16
    elif len(List) > thread_config['nb_thread'] and len(List) <= 16:
        nb_thread = thread_config['nb_thread']
        elementperthread = len(List) / thread_config['nb_thread']
        index = 1
        if len(List) >= 16:
            nb_thread == 16
            print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Maximum thread reach - Create " + str(nb_thread) +  " Thread of " + str(int(elementperthread)) + " " + thread_config['type'] + "(s)")
            if thread_config['type'] == 'PollingCommands':
                splits = np.array_split(List,nb_thread)
                for element in splits:
                    schedule.every(element[0].polling).seconds.do(run_threaded, collectData, cmd=element, type_thread=thread_config['type'], index=element[0].polling)
            else:
                splits = np.array_split(List,nb_thread)
                for array in splits:
                    schedule.every(threading_interval).seconds.do(run_threaded, collectData, cmd=array, type_thread=thread_config['type'], index=index)
                    index += 1              
        else:
            print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Create " + str(nb_thread) +  " Thread of " + str(int(elementperthread)) + " " + thread_config['type'] + "(s)")
            if thread_config['type'] == 'PollingCommands':
                for element in List:
                    schedule.every(element[0].polling).seconds.do(run_threaded, collectData, cmd=element, type_thread=thread_config['type'], index=element[0].polling)
            else:
                splits = np.array_split(List,nb_thread)
                for array in splits:
                    schedule.every(threading_interval).seconds.do(run_threaded, collectData, cmd=array, type_thread=thread_config['type'], index=index)
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
        if config['Thread']['type'] == 'GlobalCommands':
            createSchedule(config['Thread'], ListAllCmds)
        if config['Thread']['type'] == 'Node':
            createSchedule(config['Thread'], ListTN)
        if config['Thread']['type'] == 'PollingCommands':
            ListPollingCmds = discovery.getCommandListbyPooling(ListAllCmds)
            logging.debug(ListPollingCmds)
            createSchedule(config['Thread'], ListPollingCmds)
        # Start thread
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as error:
        print(color.style.RED + "ERROR: " + color.style.NORMAL + str(error))

if __name__ == "__main__":
    main()