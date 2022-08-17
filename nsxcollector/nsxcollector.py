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
from lib import tools, color, connection, influxdb, discovery, grafana, transportnodes
# from fabric import Connection, ThreadingGroup
from threading import current_thread
import numpy as np

def collectData(elementlist,type_thread):
    # Test what kind of threading
    if type_thread == 'GlobalCommands' or type_thread == 'PollingCommands':
        for item in elementlist:
            if item.type == 'API':
                for node in item.tn: 
                    result = connection.sendCommand(node,item, False)
                    influxdb.influxWrite(node.ip_mgmt,item, result, influx_write_api[0], influx_write_api[1], influx_write_api[2] )

            else:
                if len(item.tn) > 1:
                    for node in item.tn: 
                        result = connection.sendCommand(node,item, True)
                        influxdb.influxWrite(node.ip_mgmt,item, result, influx_write_api[0], influx_write_api[1], influx_write_api[2] )

                else:
                    result = connection.sendCommand(item.tn[0],item, False)
                    influxdb.influxWrite(item[0].ip_mgmt, item, result, influx_write_api[0], influx_write_api[1], influx_write_api[2] )


    if type_thread == 'Node':
        SSHnodes = transportnodes.getComponentbyType('EdgeNode', elementlist)
        APInodes = transportnodes.getComponentbyType('Manager', elementlist)
        # Passing command to API nodes
        for apinode in APInodes:
            for cmd in apinode.cmd:
                if isinstance(cmd, list):
                    for call in cmd:
                        result = connection.sendCommand(apinode,call)
                        influxdb.influxWrite(apinode.ip_mgmt,call, result, influx_write_api[0], influx_write_api[1], influx_write_api[2] )
                else:
                    result = connection.sendCommand(apinode,cmd)
                    influxdb.influxWrite(apinode.ip_mgmt,cmd, result, influx_write_api[0], influx_write_api[1], influx_write_api[2])

        # Passing commands to SSH nodes
        for cmd in SSHnodes[0].cmd:
            results = connection.sendCommand(SSHnodes[0],cmd, SSHnodes)
            for i in results:
                influxdb.influxWrite(i['host'],i['cmd'], i['result'], influx_write_api[0], influx_write_api[1], influx_write_api[2])
        
def run_threaded(job_func, listelement, type_thread, index):
    # Create a thread
    logging.info(listelement)
    job_thread = threading.Thread(name=type_thread + ' Thread_' + str(index), target=job_func, args=(listelement,type_thread,))
    job_thread.start()

def createSchedule(thread_config, List):

    if thread_config['type'] == 'Node' or thread_config['type'] == 'GlobalCommands':
        threading_interval = thread_config['polling']

    # Global Thread configuration 
    print(color.style.RED + "-- ==> Type of threading: " + color.style.NORMAL + thread_config['type'])
    print(color.style.RED + "-- ==> Nb of asking threads : " + color.style.NORMAL + str(thread_config['nb_thread']))

    # Elements less than thread => only one thread
    if len(List) < thread_config['nb_thread']:
        print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Create only one Thread")
        if thread_config['type'] == 'PollingCommands':
            threading_interval = List[0][0].polling
        schedule.every(threading_interval).seconds.do(run_threaded, collectData, listelement=List, type_thread=thread_config['type'] ,index=1)

    # Nb of Elements between nb thread and the max (max = 16) 
    elif len(List) >= thread_config['nb_thread'] and len(List) <= 16:
        nb_thread = thread_config['nb_thread']
        elementperthread = len(List) / thread_config['nb_thread']
        index = 1
        print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Creating " + str(nb_thread) +  " Thread(s)")
        if thread_config['type'] == 'PollingCommands':
            for element in List:
                print(color.style.RED + "-- ==> Creating Thread of " + color.style.NORMAL + str(len(element)) + " element(s)")
                schedule.every(element[0].polling).seconds.do(run_threaded, collectData, listelement=element, type_thread=thread_config['type'], index=element[0].polling)
        else:
            splits = np.array_split(List,nb_thread)
            for array in splits:
                print(color.style.RED + "-- ==> Creating Thread of " + color.style.NORMAL + str(len(array)) + " element(s)")
                schedule.every(threading_interval).seconds.do(run_threaded, collectData, listelement=array, type_thread=thread_config['type'], index=index)
                index += 1

    # Elements upper thread => create number of thread in config file - MAX Thread = 16
    elif len(List) >= 16:
        nb_thread == 16
        print(color.style.RED + "-- ==> Found " + color.style.NORMAL + str(len(List)) + " elements - Maximum thread reach - Create " + str(nb_thread) +  " Thread(s) of " + str(int(elementperthread)) + " " + thread_config['type'] + "(s)")
        if thread_config['type'] == 'PollingCommands':
            splits = np.array_split(List,nb_thread)
            for element in splits:
                print(color.style.RED + "-- ==> Creating Thread of " + color.style.NORMAL + str(len(element)) + " element(s)")
                schedule.every(element[0].polling).seconds.do(run_threaded, collectData, listelement=element, type_thread=thread_config['type'], index=element[0].polling)
        else:
            splits = np.array_split(List,nb_thread)
            for array in splits:
                print(color.style.RED + "-- ==> Creating Thread of " + color.style.NORMAL + str(len(array)) + " element(s)")
                schedule.every(threading_interval).seconds.do(run_threaded, collectData, listelement=array, type_thread=thread_config['type'], index=index)
                index += 1      
    else:
        print(color.style.RED + "ERROR: " + color.style.NORMAL + "Thread configuration issue")
        sys.exit()


def main():
    global influx_write_api
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
    dictenv = tools.readENV()
    # Create connection with InfluxDB
    influx_write_api = influxdb.influxConnection(dictenv, args)
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
            createSchedule(config['Thread'], ListPollingCmds)
        # Start thread
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as error:
        print(color.style.RED + "ERROR: " + color.style.NORMAL + str(error))

if __name__ == "__main__":
    main()