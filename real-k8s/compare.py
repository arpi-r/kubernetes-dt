from platform import node
import json
import sys
import matplotlib.pyplot as plt
from state_extractor import *


def convert_cpu(cpu):
    if cpu == "0":
        return 0
    return float(cpu[:-1])


def convert_memory(memory):
    if memory == "0":
        return 0
    return float(memory[:-2])


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
            twin_node = next(
                x for x in current_twin_data['nodes'] if x["name"] == node["name"])

            actual_node_cpu += convert_cpu(node["cpu"])
            twin_node_cpu += convert_cpu(twin_node["cpu"])
            actual_node_mem += convert_memory(node["memory"])
            twin_node_mem += convert_memory(twin_node["memory"])
            actual_twin_pods = []
            for pod in twin_node["pods"]:
                if pod["containers"][0]["usage"]["cpu"] != "0":
                    actual_twin_pods.append(pod)
            twin_pods += len(actual_twin_pods)
            actual_pods += len(node["pods"])

            for pod in node["pods"]:
                for container in pod["containers"]:
                    actual_pods_cpu += convert_cpu(container["usage"]["cpu"])
                    actual_pods_mem += convert_memory(
                        container["usage"]["memory"])

            for pod in twin_node["pods"]:
                for container in pod["containers"]:
                    twin_pods_cpu += convert_cpu(container["usage"]["cpu"])
                    twin_pods_memory += convert_memory(
                        container["usage"]["memory"])

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

    fig, axs = plt.subplots(2, 3)
    axs[0, 0].plot(actual_node_cpus, label='Actual Node CPU')
    axs[0, 0].plot(twin_node_cpus, label='Twin Node CPU')
    axs[0, 0].set_title('Node CPU Usage')
    axs[0, 0].legend()

    axs[0, 1].plot(actual_node_mems, label='Actual Node Memory')
    axs[0, 1].plot(twin_node_mems, label='Twin Node Memory')
    axs[0, 1].set_title('Node Memory Usage')
    axs[0, 1].legend()

    axs[0, 2].plot(actual_pod_mems, label='Actual Pod Memory')
    axs[0, 2].plot(twin_pod_mems, label='Twin Pod Memory')
    axs[0, 2].set_title('Pod Memory Usage')
    axs[0, 2].legend()

    axs[1, 0].plot(actual_pod_cpus, label='Actual Pod CPU')
    axs[1, 0].plot(twin_pod_cpus, label='Twin Pod CPU')
    axs[1, 0].set_title('Pod CPU Usage')
    axs[1, 0].legend()

    axs[1, 1].plot(actual_pod_count, label='Actual Pod Count')
    axs[1, 1].plot(twin_pod_count, label='Twin Pod Count')
    axs[1, 1].set_title('Pod Count')
    axs[1, 1].legend()

    fig.delaxes(axs[1, 2])

    for x in range(2):
        for y in range(3):
            bottom, top = axs[x, y].get_ylim()
            axs[x, y].set_ylim(bottom, top * 4)

    plt.show()


if __name__ == '__main__':
    actual_eval_file = sys.argv[1]
    twin_eval_file = sys.argv[2]

    load_and_compare(actual_eval_file, twin_eval_file)


# 1. Node count
# 2. For matching node get diff in CPU and memory - 2 data points
# 3. Pod count per node - total pods
# 4. At a node level total pod memory and CPU - total
