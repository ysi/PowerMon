#!/opt/homebrew/bin/python3

import paramiko
import json

class style:
    RED = '\33[31m'
    ORANGE = '\33[33m'
    GREEN = '\33[32m'
    NORMAL = '\033[0m'


def connect(Equipment, Port, Login, Password):
    # SSH connection with paramiko
    # Need IP/FQDN of equipment, TCP Port (can be empty), Login and Password 
    try:
        print(style.NORMAL + "Connection to " + style.GREEN + Equipment + ":" + str(Port) + style.NORMAL)
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if Port != '':
            ssh_client.connect(hostname=Equipment, username=Login,password=Password, port=Port)
        else:
            ssh_client.connect(hostname=Equipment, username=Login,password=Password)
        return ssh_client
    except:
        print(style.RED + "error" + style.NORMAL)

def disconnect(sshclient):
    sshclient.close

def exec(sshclient, command, type):
    if type == 'nsx':
        command = command + ' | json'

    try:
        print(style.NORMAL + "Send command: " + style.GREEN + command + style.NORMAL)
        stdin,stdout,stderr=sshclient.exec_command(command)
        if type == 'nsx':
            return json.loads(stdout.read().decode())
        else:
            print('ok')
            return stdout
    except:
        print(stderr)
