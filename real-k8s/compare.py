from platform import node
import json
import sys
import matplotlib.pyplot as plt
# from state_extractor import *

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

def convert_cpu(cpu):
    if cpu == "0":
        return 0
    return float(cpu[:-1])


def convert_memory(memory):
    if memory == "0":
        return 0
    return float(memory[:-2])


def load_eval_vals(act_file, twin_file):
    with open(act_file, 'r') as f:
        act_data = json.load(f)
    with open(twin_file, 'r') as f:
        twin_data = json.load(f)

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

    # print("Pod diffs: {}\n".format(pods_diffs))
    # print("Node cpu diffs: {}\n".format(node_cpu_diffs))
    # print("Node mem diffs: {}\n".format(node_mem_diffs))
    # print("Pod cpu diffs: {}\n".format(pod_cpu_diffs))
    # print("Pod mem diffs: {}\n".format(pod_mem_diffs))

    # print("Actual pod count: {}\n".format(actual_pod_count))
    # print("Twin pod count: {}\n".format(twin_pod_count))
    # print("Actual pod cpus: {}\n".format(actual_pod_cpus))
    # print("Twin pod cpus: {}\n".format(twin_pod_cpus))
    # print("Actual node cpus: {}\n".format(actual_node_cpus))
    # print("Twin node cpus: {}\n".format(twin_node_cpus))
    # print("Actual pod mems: {}\n".format(actual_pod_mems))
    # print("Twin pod mems: {}\n".format(twin_pod_mems))
    # print("Actual node mems: {}\n".format(actual_node_mems))
    # print("Twin node mems: {}\n".format(twin_node_mems))

def compare_graphs_1():
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(actual_pod_count, label='Actual Pod Count')
    ax.plot(twin_pod_count, label='Twin Pod Count')
    ax.set_title('Pod Count')
    ax.set_xlabel('Requests (x10)')
    ax.set_ylabel('Number of Pods')
    ax.legend()

    bottom, top = ax.get_ylim()
    ax.set_ylim(-1, top * 15)

    plt.show()

def compare_graphs_2():
  fig, axs = plt.subplots(1, 2, figsize=(16, 4), constrained_layout = True)

  axs[0].plot(actual_node_cpus, label='Actual Node CPU')
  axs[0].plot(twin_node_cpus, label='Twin Node CPU')
  axs[0].set_title('Node CPU Usage')
  axs[0].set_xlabel('Requests (x10)')
  axs[0].set_ylabel('CPU Usage (nano cpu units)')
  axs[0].legend()

  axs[1].plot(actual_pod_cpus, label='Actual Pod CPU')
  axs[1].plot(twin_pod_cpus, label='Twin Pod CPU')
  axs[1].set_title('Pod CPU Usage')
  axs[1].set_xlabel('Requests (x10)')
  axs[1].set_ylabel('CPU Usage (nano cpu units)')
  axs[1].legend()

  bottom, top = axs[0].get_ylim()
  axs[0].set_ylim(-1e10, top * 25)

  bottom, top = axs[1].get_ylim()
  axs[1].set_ylim(-1e10, top * 50)

  plt.show()

def compare_graphs_3():
  fig, axs = plt.subplots(1, 2, figsize=(16, 4), constrained_layout = True)

  axs[0].plot(actual_node_mems, label='Actual Node Memory')
  axs[0].plot(twin_node_mems, label='Twin Node Memory')
  axs[0].set_title('Node Memory Usage')
  axs[0].set_xlabel('Requests (x10)')
  axs[0].set_ylabel('Memory Usage (kilobytes)')
  axs[0].legend()

  axs[1].plot(actual_pod_mems, label='Actual Pod Memory')
  axs[1].plot(twin_pod_mems, label='Twin Pod Memory')
  axs[1].set_title('Pod Memory Usage')
  axs[1].set_xlabel('Requests (x10)')
  axs[1].set_ylabel('Memory Usage (kilobytes)')
  axs[1].legend()

  bottom, top = axs[0].get_ylim()
  axs[0].set_ylim(-1e4, top * 2)

  bottom, top = axs[1].get_ylim()
  axs[1].set_ylim(-100000, top * 15)

  plt.show()

def compare_percentage_diff():
    print("Average difference in number of pods: {}".format(sum(pods_diffs) / len(pods_diffs)))
    print("Average difference in node CPU: {}".format(sum(node_cpu_diffs) / len(node_cpu_diffs)))
    print("Average difference in node memory: {}".format(sum(node_mem_diffs) / len(node_mem_diffs)))
    print("Average difference in pod CPU: {}".format(sum(pod_cpu_diffs) / len(pod_cpu_diffs)))
    print("Average difference in pod memory: {}".format(sum(pod_mem_diffs) / len(pod_mem_diffs)))
    print()

    num_vals = len(pods_diffs)

    avg_num_pods_variation = 0
    num_pod_count = 0
    avg_node_cpu_variation = 0
    num_node_cpu = 0
    avg_node_mem_variation = 0
    num_node_mem = 0
    avg_pod_cpu_variation = 0
    num_pod_cpu = 0
    avg_pod_mem_variation = 0
    num_pod_mem = 0
    for i in range(num_vals):
        if actual_pod_count[i] != 0:
            avg_num_pods_variation += (pods_diffs[i] / actual_pod_count[i])
            num_pod_count += 1
        if actual_node_cpus[i] != 0:
            avg_node_cpu_variation += (node_cpu_diffs[i] / actual_node_cpus[i])
            num_node_cpu += 1
        if actual_node_mems[i] != 0:
            avg_node_mem_variation += (node_mem_diffs[i] / actual_node_mems[i])
            num_node_mem += 1
        if actual_pod_cpus[i] != 0:
            avg_pod_cpu_variation += (pod_cpu_diffs[i] / actual_pod_cpus[i])
            num_pod_cpu += 1
        if actual_pod_mems[i] != 0:
            avg_pod_mem_variation += (pod_mem_diffs[i] / actual_pod_mems[i])
            num_pod_mem += 1
    
    avg_num_pods_variation = (avg_num_pods_variation/num_pod_count) * 100
    avg_node_cpu_variation = (avg_node_cpu_variation/num_node_cpu) * 100
    avg_node_mem_variation = (avg_node_mem_variation/num_node_mem) * 100
    avg_pod_cpu_variation = (avg_pod_cpu_variation/num_pod_cpu) * 100
    avg_pod_mem_variation = (avg_pod_mem_variation/num_pod_mem) * 100

    print("Percentage variation in number of pods: {}%".format(avg_num_pods_variation))
    print("Percentage variation in node CPU: {}%".format(avg_node_cpu_variation))
    print("Percentage variation in node memory: {}%".format(avg_node_mem_variation))
    print("Percentage variation in pod CPU: {}%".format(avg_pod_cpu_variation))
    print("Percentage variation in pod memory: {}%".format(avg_pod_mem_variation))


if __name__ == '__main__':
    actual_eval_file = sys.argv[1]
    twin_eval_file = sys.argv[2]

    load_eval_vals(actual_eval_file, twin_eval_file)
    compare_percentage_diff()

    plt.rcParams.update({'font.size': 16})
    # graph for pod count
    compare_graphs_1()
    # graph for node cpu and pod cpu
    compare_graphs_2()
    # graph for node memory and pod memory
    compare_graphs_3()


# 1. Node count
# 2. For matching node get diff in CPU and memory - 2 data points
# 3. Pod count per node - total pods
# 4. At a node level total pod memory and CPU - total
