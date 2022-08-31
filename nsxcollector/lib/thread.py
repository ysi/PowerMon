#!/opt/homebrew/bin/python3
# coding: utf8
#
import schedule, time, threading, sys, logging
from lib import tools, polling
# from threading import current_thread
from collections import defaultdict


def threadmodule(infra, inDB):
    try:
        AllCommands = infra.getCommandsPolling()
        createSchedule(infra, AllCommands, inDB)
        # Start thread
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as error:
        print(tools.color.RED + "ERROR: " + tools.color.NORMAL + str(error))
    

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
    print(tools.color.RED + "==> Total number of commands: " + tools.color.NORMAL + str(len(List)))
    polling_groups = defaultdict(list)
    # Create list based on polling value
    for cmd in List:
        polling_groups[cmd.polling].append(cmd)

    new_list = polling_groups.items()
    print(tools.color.RED + "==> Total of polling interval: " + tools.color.NORMAL + str(len(new_list)))
    if len(new_list) <= Num_Max_Thread:
        for key, value in new_list:
            schedule.every(key).seconds.do(run_threaded, polling.collectData, infra=infra, listelement=value, index=key, inDB=inDB)

    else:
        print(tools.color.RED + "==> Maximum thread reach: " + tools.color.NORMAL + " please reorganize your commands to have maximum 16 polling intervals")
        sys.exit()
