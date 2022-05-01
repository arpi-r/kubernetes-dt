from platform import node
import json
import sys
import matplotlib.pyplot as plt
from state_extractor import *

def convert_cpu(cpu):
    if cpu == "0":
        return 0
    return float(cpu[:-1])

def load_and_compare(act_file, twin_file):
    with open(act_file, 'r') as f:
        act_data = json.load(f)
    with open(twin_file, 'r') as f:
        twin_data = json.load(f)
    
    pods_diffs = []
    node_cpu_diffs = []
    node_mem_diffs = []
    pod_cpu_diffs = []
    pod_mem_diffs = []

    actual_pod_count = []
    twin_pod_count = []
    twin_pod_cpus = []
    actual_pod_cpus = []
    actual_node_cpus = []
    twin_node_cpus = []
    actual_node_mems = []
    twin_node_mems = []
    twin_pod_mems = []
    actual_pod_mems = []

    for i in range(100):
        current_act_data = act_data[i]
        current_twin_data = twin_data[i]

        actual_node_cpu = 0
        actual_node_mem = 0
        twin_node_cpu = 0
        twin_node_mem = 0
        twin_pods = 0
        actual_pods = 0
        twin_pods_cpu = 0
        twin_pods_memory = 0
        actual_pods_cpu = 0
        actual_pods_mem = 0

        for node in current_act_data['nodes']:
            twin_node = next(x for x in current_twin_data['nodes'] if x["name"] == node["name"])            

            actual_node_cpu += convert_cpu(node["cpu"])
            twin_node_cpu += convert_cpu(twin_node["cpu"])
            actual_node_mem += float(node["memory"][:-2])
            twin_node_mem += float(twin_node["memory"][:-2])
            twin_pods += len(twin_node["pods"])
            actual_pods += len(node["pods"])

            for pod in node["pods"]:
                for container in pod["containers"]:
                    actual_pods_cpu += convert_cpu(container["usage"]["cpu"])
                    actual_pods_mem += float(container["usage"]["memory"][:-2])
            
            for pod in twin_node["pods"]:
                for container in pod["containers"]:
                    twin_pods_cpu += convert_cpu(container["usage"]["cpu"])
                    twin_pods_memory += float(container["usage"]["memory"][:-2])

        node_cpu_diffs.append(abs(actual_node_cpu - twin_node_cpu))
        node_mem_diffs.append(abs(actual_node_mem - twin_node_mem))
        pod_cpu_diffs.append(abs(twin_pods_cpu - actual_pods_cpu))
        pod_mem_diffs.append(abs(twin_pods_memory - actual_pods_mem))
        pods_diffs.append(abs(twin_pods - actual_pods))

        actual_pod_count.append(actual_pods)
        twin_pod_count.append(twin_pods)

        actual_node_cpus.append(actual_node_cpu)
        twin_node_cpus.append(twin_node_cpu)

        actual_node_mems.append(actual_node_mem)
        twin_node_mems.append(twin_node_mem)

        twin_pod_cpus.append(twin_pods_cpu)
        actual_pod_cpus.append(actual_pods_cpu)
                
        twin_pod_mems.append(twin_pods_memory)
        actual_pod_mems.append(actual_pods_mem)

    # print("Pod diffs: {}".format(pods_diffs))
    # print("Node cpu diffs: {}".format(node_cpu_diffs))
    # print("Node mem diffs: {}".format(node_mem_diffs))
    # print("Pod cpu diffs: {}".format(pod_cpu_diffs))
    # print("Pod mem diffs: {}".format(pod_mem_diffs))

    # print("Actual pod count: {}".format(actual_pod_count))
    # print("Twin pod count: {}".format(twin_pod_count))
    # print("Twin pod cpus: {}".format(twin_pod_cpus))
    # print("Actual node cpus: {}".format(actual_node_cpus))
    # print("Twin pod mems: {}".format(twin_pod_mems))
    # print("Actual node mems: {}".format(actual_node_mems))

    plt.plot(actual_pod_mems, label="Actual node cpu usage")
    plt.plot(twin_pod_mems, label="Twin node cpu usage")
    plt.show()

        

if __name__ == '__main__':
    actual_eval_file = sys.argv[1]
    twin_eval_file = sys.argv[2]

    load_and_compare(actual_eval_file, twin_eval_file)



# 1. Node count
# 2. For matching node get diff in CPU and memory - 2 data points
# 3. Pod count per node - total pods
# 4. At a node level total pod memory and CPU - total