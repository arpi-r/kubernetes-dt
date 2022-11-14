import json
import sys
import psutil
import subprocess
import time

security_logs = ""
restart_index = -1

def read_cluster_state(new_cluster_json):
    with open(new_cluster_json, 'r') as f:
        new_cluster_state = json.load(f)
    return new_cluster_state

def read_twin_state(twin_file):
    with open(twin_file, 'r') as f:
        twin_state = f.readlines()
    return twin_state

def write_security_logs():
    with open("security_logs.txt", "w") as f:
        f.write(security_logs)

def update_cluster_state(new_cluster):
    with open('../real-k8s/old_evaluations/cluster_state.json', 'r') as f:
        old_cluster_state = json.load(f)

    new_cluster_state = {}
    new_cluster_state["services"] = old_cluster_state["services"]
    new_cluster_state["nodes"] = new_cluster[restart_index]["nodes"]

    new_cluster_json_object = json.dumps(new_cluster_state, indent=2) 
    with open("new_cluster_state.json", "w") as outfile:
        outfile.write(new_cluster_json_object)

def kill_running_model():
    ps_process = subprocess.run(['ps', '-a'], stdout=subprocess.PIPE)
    ps_output = ps_process.stdout.decode('utf-8').split('\n')
    abs_pid = -1
    tee_pid = -1

    for out in ps_output:
        # print(out)
        if "/gen/erl/run" in out:
            abs_pid = int(out.split()[0])
        if "tee" in out:
            tee_pid = int(out.split()[0])
    print(abs_pid)
    print(tee_pid)

    if abs_pid != -1:
        psutil.Process(abs_pid).terminate()
        print("Terminating running K8sDT model")
    if tee_pid != -1:  
        psutil.Process(tee_pid).terminate()
        print("Terminating writing to twin log file")

def get_twin_resource_usage(twin_state):
    num_pods = []
    total_node_cpu_usage = []
    total_node_mem_usage = []
    total_pod_cpu_usage = []
    total_pod_mem_usage = []

    pod = 0
    nmem = 0
    ncpu = 0
    pmem = 0
    pcpu = 0

    zero_run = True
    first_run = True

    for line in twin_state:
        if "RUN" in line:
            num_pods.append(pod)
            total_node_cpu_usage.append(ncpu)
            total_node_mem_usage.append(nmem)
            total_pod_cpu_usage.append(pcpu)
            total_pod_mem_usage.append(pmem)

            pod = 0
            nmem = 0
            ncpu = 0
            pmem = 0
            pcpu = 0

            if zero_run:
                zero_run = False
                continue
            if first_run:
                first_run = False
                continue

        if "Pod" in line:
            if "Pods" in line:
                line = line.split(":")
                pod_count = int(line[2].strip().split()[0])
                pod += pod_count
                n_cpu = int(line[3].strip().split("/")[0])
                n_mem = int(line[5].strip().split("/")[0])
                ncpu += n_cpu
                nmem += n_mem
                # print(line)
            else:
                line = line.split(":")
                p_cpu = int(line[3].strip().split()[0])
                p_mem = int(line[4].strip().split()[0])
                pcpu += p_cpu
                pmem += p_mem
                # print(line)

    num_pods.append(pod)
    total_node_cpu_usage.append(ncpu)
    total_node_mem_usage.append(nmem)
    total_pod_cpu_usage.append(pcpu)
    total_pod_mem_usage.append(pmem)

    num_pods = num_pods[1:]
    total_node_cpu_usage = total_node_cpu_usage[1:]
    total_node_mem_usage = total_node_mem_usage[1:]
    total_pod_cpu_usage = total_pod_cpu_usage[1:]
    total_pod_mem_usage = total_pod_mem_usage[1:]

    # print(num_pods)
    # print(len(num_pods))
    # print(total_node_cpu_usage)
    # print(len(total_node_cpu_usage))
    # print(total_node_mem_usage)
    # print(len(total_node_mem_usage))
    # print(total_pod_cpu_usage)
    # print(len(total_pod_cpu_usage))
    # print(total_pod_mem_usage)
    # print(len(total_pod_mem_usage))

    return num_pods, total_node_cpu_usage, total_node_mem_usage, total_pod_cpu_usage, total_pod_mem_usage

def convert_cpu(cpu):
    if cpu == "0":
        return 0
    return float(cpu[:-1])

def convert_memory(memory):
    if memory == "0":
        return 0
    return float(memory[:-2])

def get_new_cluster_resource_usage(new_cluster):
    num_pods = []
    total_node_cpu_usage = []
    total_node_mem_usage = []
    total_pod_cpu_usage = []
    total_pod_mem_usage = []

    new_cluster_len = len(new_cluster)
    for i in range(new_cluster_len):
        current_state_data = new_cluster[i]
        # print(current_state_data)

        npod = 0
        nmem = 0
        ncpu = 0
        pmem = 0
        pcpu = 0

        for node in current_state_data['nodes']:
            ncpu += convert_cpu(node["cpu"])
            nmem += convert_memory(node["memory"])
            npod += len(node["pods"])

            for pod in node["pods"]:
                for container in pod["containers"]:
                    pcpu += convert_cpu(container["usage"]["cpu"])
                    pmem += convert_memory(container["usage"]["memory"])

        num_pods.append(int(npod))
        total_node_cpu_usage.append(int(ncpu))
        total_node_mem_usage.append(int(nmem))
        total_pod_cpu_usage.append(int(pcpu))
        total_pod_mem_usage.append(int(pmem))
    
    # print(num_pods)
    # print(len(num_pods))
    # print(total_node_cpu_usage)
    # print(len(total_node_cpu_usage))
    # print(total_node_mem_usage)
    # print(len(total_node_mem_usage))
    # print(total_pod_cpu_usage)
    # print(len(total_pod_cpu_usage))
    # print(total_pod_mem_usage)
    # print(len(total_pod_mem_usage))

    return num_pods, total_node_cpu_usage, total_node_mem_usage, total_pod_cpu_usage, total_pod_mem_usage

def num_pods_diff(twin_num_pods, new_cluster_num_pods):
    diff = []
    max_diff, min_diff = -1, 1000
    max_diff_index, min_diff_index = -1, -1

    for i in range(len(twin_num_pods)):
        d = abs(twin_num_pods[i] - new_cluster_num_pods[i])
        diff.append(d)
        if d > max_diff:
            max_diff = d
            max_diff_index = i
        if d < min_diff:
            min_diff = d
            min_diff_index = i
    
    # print(diff)
    return min(diff), max(diff), min_diff_index, max_diff_index

def total_node_cpu_usage_diff(twin_total_node_cpu_usage, new_cluster_total_node_cpu_usage):
    diff = []
    max_diff, min_diff = -1, 10000000000000
    max_diff_index, min_diff_index = -1, -1

    for i in range(len(twin_total_node_cpu_usage)):
        d = abs(twin_total_node_cpu_usage[i] - new_cluster_total_node_cpu_usage[i])
        diff.append(d)
        if d > max_diff:
            max_diff = d
            max_diff_index = i
        if d < min_diff:
            min_diff = d
            min_diff_index = i
    
    # print(diff)
    return min(diff), max(diff), min_diff_index, max_diff_index

def total_node_mem_usage_diff(twin_total_node_mem_usage, new_cluster_total_node_mem_usage):
    diff = []
    max_diff, min_diff = -1, 10000000000000
    max_diff_index, min_diff_index = -1, -1

    for i in range(len(twin_total_node_mem_usage)):
        d = abs(twin_total_node_mem_usage[i] - new_cluster_total_node_mem_usage[i])
        diff.append(d)
        if d > max_diff:
            max_diff = d
            max_diff_index = i
        if d < min_diff:
            min_diff = d
            min_diff_index = i
    
    # print(diff)
    return min(diff), max(diff), min_diff_index, max_diff_index

def total_pod_cpu_usage_diff(twin_total_pod_cpu_usage, new_cluster_total_pod_cpu_usage):
    diff = []
    max_diff, min_diff = -1, 10000000000000
    max_diff_index, min_diff_index = -1, -1

    for i in range(len(twin_total_pod_cpu_usage)):
        d = abs(twin_total_pod_cpu_usage[i] - new_cluster_total_pod_cpu_usage[i])
        diff.append(d)
        if d > max_diff:
            max_diff = d
            max_diff_index = i
        if d < min_diff:
            min_diff = d
            min_diff_index = i
    
    # print(diff)
    return min(diff), max(diff), min_diff_index, max_diff_index

def total_pod_mem_usage_diff(twin_total_pod_mem_usage, new_cluster_total_pod_mem_usage):
    diff = []
    max_diff, min_diff = -1, 10000000000000
    max_diff_index, min_diff_index = -1, -1

    for i in range(len(twin_total_pod_mem_usage)):
        d = abs(twin_total_pod_mem_usage[i] - new_cluster_total_pod_mem_usage[i])
        diff.append(d)
        if d > max_diff:
            max_diff = d
            max_diff_index = i
        if d < min_diff:
            min_diff = d
            min_diff_index = i
    
    # print(diff)
    return min(diff), max(diff), min_diff_index, max_diff_index

def check_for_signature_based_attacks(new_cluster):
    global security_logs
    global restart_index
    attack_detected = False

    state_index = -1
    for state in new_cluster:
        state_index += 1
        if "attacks" in state and len(state["attacks"]) > 0:
            attack_detected = True
            security_logs += "Signature-based attack detected!\n"
            security_logs += json.dumps(state["attacks"]) + "\n"
            restart_index = state_index
            break

    return attack_detected

def check_for_anomalies(new_cluster):
    global security_logs
    global restart_index
    anomaly_detected = False

    # read from the twin log file
    twin_state = read_twin_state("saved_k8s_state")
    # parse runwise logs
    # store total number of pods, total memory usage, total cpu usage for each run
    twin_num_pods, twin_node_cpu_usage, twin_node_mem_usage, twin_pod_cpu_usage, twin_pod_mem_usage = get_twin_resource_usage(twin_state)

    # read from new cluster json
    # get total number of pods, total memory usage, total cpu usage for each run
    new_num_pods, new_node_cpu_usage, new_node_mem_usage, new_pod_cpu_usage, new_pod_mem_usage = get_new_cluster_resource_usage(new_cluster)

    # compare the two
    min_pod_diff, max_pod_diff, min_pod_diff_ind, max_pod_diff_ind = num_pods_diff(twin_num_pods, new_num_pods)
    min_node_cpu_diff, max_node_cpu_diff, min_node_cpu_diff_ind, max_node_cpu_diff_ind = total_node_cpu_usage_diff(twin_node_cpu_usage, new_node_cpu_usage)
    min_node_mem_diff, max_node_mem_diff, min_node_mem_diff_ind, max_node_mem_diff_ind = total_node_mem_usage_diff(twin_node_mem_usage, new_node_mem_usage)
    min_pod_cpu_diff, max_pod_cpu_diff, min_pod_cpu_diff_ind, max_pod_cpu_diff_ind = total_pod_cpu_usage_diff(twin_pod_cpu_usage, new_pod_cpu_usage)
    min_pod_mem_diff, max_pod_mem_diff, min_pod_mem_diff_ind, max_pod_mem_diff_ind = total_pod_mem_usage_diff(twin_pod_mem_usage, new_pod_mem_usage)

    # print("pod diff: ", min_pod_diff, max_pod_diff)
    # print("node cpu diff: ", min_node_cpu_diff, max_node_cpu_diff)
    # print("node mem diff: ", min_node_mem_diff, max_node_mem_diff)
    # print("pod cpu diff: ", min_pod_cpu_diff, max_pod_cpu_diff)
    # print("pod mem diff: ", min_pod_mem_diff, max_pod_mem_diff)

    possible_indices = []

    if min_pod_diff > 0 or max_pod_diff > 2:
        anomaly_detected = True
        security_logs += "Anomaly detected in number of pods\n"
        possible_indices.append(max_pod_diff_ind)
        possible_indices.append(min_pod_diff_ind)
    
    if min_node_cpu_diff > 500000000 or max_node_cpu_diff > 750000000:
        anomaly_detected = True
        security_logs += "Anomaly detected in node cpu usage\n"
        possible_indices.append(max_node_cpu_diff_ind)
        possible_indices.append(min_node_cpu_diff_ind)
    
    if min_node_mem_diff > 800000 or max_node_mem_diff > 850000:
        anomaly_detected = True
        security_logs += "Anomaly detected in node memory usage\n"
        possible_indices.append(max_node_mem_diff_ind)
        possible_indices.append(min_node_mem_diff_ind)
    
    if min_pod_cpu_diff > 20 or max_pod_cpu_diff > 300000000:
        anomaly_detected = True
        security_logs += "Anomaly detected in pod cpu usage\n"
        restart_index = min(max_pod_cpu_diff_ind, min_pod_cpu_diff_ind)
        possible_indices.append(max_pod_cpu_diff_ind)
        possible_indices.append(min_pod_cpu_diff_ind)
    
    if min_pod_mem_diff > 120 or max_pod_mem_diff > 20000:
        anomaly_detected = True
        security_logs += "Anomaly detected in pod memory usage\n"
        restart_index = min(max_pod_mem_diff_ind, min_pod_mem_diff_ind)
        possible_indices.append(max_pod_mem_diff_ind)
        possible_indices.append(min_pod_mem_diff_ind)
    
    if anomaly_detected:
        restart_index = min(possible_indices)
    
    # print("restart index: ", restart_index)
    
    return anomaly_detected

def response_to_attack(new_cluster):
    kill_running_model()
    write_security_logs()
    checkpoint_process = subprocess.run(['python3', 'state_saver.py'], stdout=subprocess.PIPE)
    update_cluster_state(new_cluster)
    time.sleep(5)
    # TODO: Check why this fails to use updated abs file
    # running state mapper with the new cluster state json works correctly
    # k8sdt abs file seems to be updated correctly
    generate_run_new_twin_process = subprocess.Popen(['sh', '../abs-k8s-model/state_mapper.sh', '../security/new_cluster_state.json'])
    # print(security_logs)
    # print(restart_index)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 security_check.py <new_cluster_state>")
        exit(1)
    
    new_cluster_file_name = sys.argv[1]
    new_cluster = read_cluster_state(new_cluster_file_name)
    # print()
    # print(new_cluster)
    # print()

    signature_attack_detected = check_for_signature_based_attacks(new_cluster)
    if signature_attack_detected:
        print("Signature-based attack detected!")
        response_to_attack(new_cluster)
        exit(1)
    
    anomaly_detected = check_for_anomalies(new_cluster)
    if anomaly_detected:
        print("Anomaly detected: Possible DDoS attack!")
        print(security_logs)
        response_to_attack(new_cluster)
        exit(1)
    
    security_logs = ""
    write_security_logs()
    print("No attack detected!")
