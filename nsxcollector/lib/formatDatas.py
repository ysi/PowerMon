#!/opt/homebrew/bin/python3

def processAPI(host, json):
    # Format result of call api/v1/systemhealth/appliances/process/status
    Tab_result = []
    if isinstance(json, dict) and 'results' in json and json['result_count'] > 0: 
        for rs in json["results"]:
            for pc in rs['top_process_by_cpu_list']:
                cpu = "Process,host=" + host + ",process=" + pc['user'] + " cpu_usage=" + str(pc['cpu_usage']) + ",memory_usage=" + str(pc['memory_usage'])
                # mem = "mem, host=" + host + ",process=" + pc['user'] + ",memory_usage=" + str(pc['memory_usage'])
                Tab_result.append(cpu)


    return Tab_result