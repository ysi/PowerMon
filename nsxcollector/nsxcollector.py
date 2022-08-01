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

import schedule, time, threading, pprint
from lib import tools, color, connection, influxdb, discovery, commands, transportnodes, grafana
from fabric import Connection, ThreadingGroup


def collectDataNSX(list_cmd, interval, session, tn):
    # Connect in ssh on the group of Edge
    list_edge = transportnodes.getEdge(tn)
    edgeconnection = []
    for host in list_edge:   
        edgeconnection.append(Connection(host=host.ip_mgmt, user=host.login, connect_kwargs={'password': host.password}))
    EdgeGroup = ThreadingGroup.from_connections(edgeconnection)

    # Loop in commands or API calls
    for cmd in list_cmd:
        if cmd.type == 'API':
            # Get API
            connection.getAPIData(session, cmd, True, influx_write_api)

        # Passing commands on the group of Edge
        if cmd.type == 'SSH':
            connection.getSSHData(EdgeGroup, cmd, influx_write_api)

    EdgeGroup.close()


def run_threaded(job_func, cmd, intvl, session, tn):
    # Create a thread
    job_thread = threading.Thread(name='Thread-' + str(intvl), target=job_func, args=(cmd,intvl,session,tn,))
    job_thread.start()

def createSchedule(ListTN, session, config, cmdlist):
    # Create schedule based on interval on config file
    # Construct Lists of commands based on intervals
    interval_list = commands.getListInterval(cmdlist)
    for i in interval_list:
        int_cmd = commands.intervalListCmd(cmdlist, i)
        # to display all commands
        str_cmd = []
        for cd in int_cmd: 
            str_cmd = str_cmd + cd.call
        print(color.style.RED + "==> " + color.style.NORMAL + "Create thread for commands with interval at: " + str(i))
        print(color.style.RED + "-- ==> " + color.style.NORMAL + "commands or calls for this thread: " + ', '.join(str_cmd) )
        schedule.every(i).seconds.do(run_threaded, collectDataNSX, cmd=int_cmd, intvl=i, session=session, tn=ListTN)

def main():
    global influx_write_api

    print("Welcome to PowerMon")
    # read config file
    config = tools.readYML('./config/config.yml')
    # Load .env file
    dictenv = tools.readENV()

    # Create connection with InfluxDB
    influx_write_api = influxdb.influxConnection(dictenv)
    try:
        # Get IPs Edge and collect NSX Manager Data through API
        # Connect to NSX and Get Transport Nodes
        ListTN, session = discovery.discovery(config)
        # Construct Lists of commands based on intervals
        Commands_List = commands.createCommandList(config,ListTN)
        # Add commands on object TN - useful for grafana
        for i in Commands_List:
            for idx, tn in enumerate(i.tn):
                tn.addCmd(i)
                i.tn[idx] = tn

        # Create Grafana Folder and Dashboards
        grafana.createGrafanaEnv(config, dictenv, ListTN, Commands_List)
        # Get All informations on NSX Managers, Edge
        createSchedule(ListTN, session, config, Commands_List)

        # Get All informations for Edge by using IP addresses of Edge take previously
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as error:
        print(color.style.RED + str(error) + color.style.NORMAL)

if __name__ == "__main__":
    main()