#!/opt/homebrew/bin/python3

from lib import sshcommand, tools


def getAllInfos(fqdn, port):
    TotalResult = []

    # read config file
    config = tools.readYML('./config/config.yml')

    # Connect to Edge
    sshconnect = sshcommand.connect(fqdn,port,config['Edge']['login'],config['Edge']['password'])
    # Loop in all commands
    for item in config['Edge']['commands']:
        result = sshcommand.exec(sshconnect, item['command'], 'nsx')
        TotalResult.append(result)
    
    sshcommand.disconnect(sshconnect)
    return TotalResult
