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

import schedule, time, threading, pprint,json
from lib import tools, color, managerconnection, influxdb
from lib.formatDatas import processAPI
from fabric import Connection, ThreadingGroup
from threading import current_thread



def collectDataNSX(command, intvl, session, edge):
    # Loop in commands or API calls
    for cmd in command['cmd']:
        if cmd['type'] == 'API':
            # Get API
            print(current_thread().name + ": On " + color.style.GREEN + config['Manager']['fqdn'] + color.style.NORMAL + " - Call " + color.style.GREEN + cmd['call'] + color.style.NORMAL)
            result = managerconnection.GetAPI(session[0], config['Manager']['fqdn'] + ":" + str(config['Manager']['port']),cmd['call'], auth_list)
            if isinstance(result, int):
                print(current_thread().name + color.style.RED + "ERROR in call + " + cmd['call'] + color.style.NORMAL + " - error " + result)
            else:
                # Call format function of a call
                function_name = globals()[cmd['name']]
                format_data = function_name(config['Manager']['fqdn'], result)
                influxdb.influxWrite(write_api[0],write_api[1], write_api[2], format_data )

    # Connect in ssh on the group of Edge
    list_edge =[]
    edg =  []
    for host in edge:   
        edg.append(Connection(host=host, user=config['Edge']['login'], connect_kwargs={'password': config['Edge']['password']}))
        list_edge.append(host)
    group = ThreadingGroup.from_connections(edg)

    # Passing commands on the group of Edge
    for cmd in command['cmd']:
        if cmd['type'] == 'SSH':
            print(current_thread().name + ": Sent on " + color.style.GREEN + ', '.join(list_edge) + color.style.NORMAL + " - ssh commands " + color.style.GREEN + cmd['call'] + color.style.NORMAL)
            output = group.run(cmd['call'] + ' | json', hide=True)
            for r in output:
                connection = output[r]
                # run function return a string with \n. Need to erase \n from the string and convert it on a real json
                result = json.loads(connection.stdout.replace('\n', ''))
                # print(result['summary'][0] + ":" + result['summary'][7].split(':')[1])

                # for i in result['summary']:
                #     print(i)
                # with open('../tests/result.txt', 'a') as f:
                #     f.write(connection.stdout)
    group.close()


def run_threaded(job_func, call, intvl, session, edge):
    # Create a thread
    job_thread = threading.Thread(name='Thread-' + str(intvl), target=job_func, args=(call,intvl,session,edge,))
    job_thread.start()

def createSchedule(List_Edge_IPs, session, config):
    # Create schedule based on interval on config file
    # loop on all commands in config file
    for cd in config['Commands']:
        # Create a Thread based on interval
        interval = cd['interval']
        schedule.every(cd['interval']).seconds.do(run_threaded, collectDataNSX, call=cd, intvl=interval, session=session, edge=List_Edge_IPs)


def main():
    global config
    global write_api
    global NSXManager_Datas
    global Edge_Datas
    global auth_list
    NSXManager_Datas = []
    Edge_Datas = []

    print("Welcome to PowerMon")
    # read config file
    config = tools.readYML('./config/config.yml')
    # Create connection with InfluxDB
    write_api = influxdb.influxConnection()

    try:
        # Get IPs Edge and collect NSX Manager Data through API
        # Connect to NSX and Get Transport Nodes
        session = managerconnection.ConnectNSX([config['Manager']['login'], config['Manager']['password'], 'AUTH'])
        auth_list = [config['Manager']['login'], config['Manager']['password'], 'AUTH']
        tn_json = managerconnection.GetAPI(session[0], config['Manager']['fqdn'] + ":" + str(config['Manager']['port']),'/api/v1/transport-nodes', auth_list)

        # List of Edge IPs
        print(color.style.RED + "==> " + color.style.NORMAL + "Connecting to NSX Manager " + color.style.GREEN + config['Manager']['fqdn'] + color.style.NORMAL + " and Getting Edge IPs")

        List_Edge_IPs = []
        if isinstance(tn_json, dict) and 'results' in tn_json and tn_json['result_count'] > 0: 
            for node in tn_json['results']:
                if node['node_deployment_info']['resource_type'] == 'EdgeNode':
                    List_Edge_IPs.append(node['node_deployment_info']['ip_addresses'][0])
        
        print(color.style.RED + "==> " + color.style.NORMAL + "Found " + str(len(List_Edge_IPs)) + " Edges")
        # Get All informations on NSX Managers, Edge
        print(color.style.RED + "==> " + color.style.NORMAL + "Collecting all informations")
        createSchedule(List_Edge_IPs, session, config)

        # Get All informations for Edge by using IP addresses of Edge take previously
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as error:
        print(color.style.RED + str(error) + color.style.NORMAL)


if __name__ == "__main__":
    main()