import json
import os
import subprocess

def read_cluster_state(file_name):
    with open(file_name, 'r') as f:
        cluster_state = json.load(f)
        return cluster_state

def extract_pods_info(pods):
    pods_info = []
    pod_info = {}
    for pod in pods:
        pod_info['name'] = pod['name']
        pod_info['cpu'] = pod['containers'][0]['usage']['cpu']
        cpu_len = len(pod_info['cpu'])
        if pod_info['cpu'][cpu_len - 1] == 'n':
            pod_info['cpu'] = pod_info['cpu'][:cpu_len - 1]
        pod_info['memory'] = pod['containers'][0]['usage']['memory']
        mem_len = len(pod_info['memory'])
        if pod_info['memory'][mem_len - 2:] == 'Ki':
            pod_info['memory'] = pod_info['memory'][:mem_len - 2]
        pods_info.append(pod_info)
        pod_info = {}

    return pods_info

def extract_nodes_info(nodes_info):
    for node in nodes_info:
        cpu_len = len(node['cpu'])
        if node['cpu'][cpu_len - 1] == 'n':
            node['cpu'] = node['cpu'][:cpu_len - 1]
        mem_len = len(node['memory'])
        if node['memory'][mem_len - 2:] == 'Ki':
            node['memory'] = node['memory'][:mem_len - 2]
        
    return nodes_info

def get_prefix_abs(file_name):
    with open(file_name, 'r') as f:
        prefix = f.read()
        # print(prefix)
    return prefix

def create_nodes_abs(prefix, nodes_info):
    nodes_abs = prefix

    for node in nodes_info:
        nodes_abs += "\n" + "\tfb = master.createNode(" + node['cpu'] + ", " + node['memory'] + ");"

    nodes_abs += "\n"

    nodes_abs += "\n\tList<Node> nodeList = master.getNodes();\n\tforeach (node in nodeList) {\n"

    for node in nodes_info:
        nodes_abs += "\t\tString name = \"" + node['name'] + "\";\n\t\tnode!setName(name);\n"
    
    nodes_abs += "\t}\n\n"

    # nodes_abs += "\tawait printer!printNodes(master,1,1);\n}\n"
    
    return nodes_abs

def create_pods_abs(prefix, pods_info):
    pods_abs = prefix

    # pods_abs += "\n\tList<Node> nodeList = master.getNodes();\n"

    pods_abs += "\n\n\tforeach (node in nodeList) {\n"

    i = 0
    for pod in pods_info:
        if int(pod['cpu'])*2 == 0:
            pods_abs += "\t\tResourcesMonitor pod" + str(i) + " = new ResourcesMonitorObject(\"service 1\", " + str(i) + ", 1, 1);\n"
            pods_abs += "\t\tPod p" + str(i) + " = new PodObject(\"service 1\", " + str(i) + ", 1, " + pod['cpu'] + ", 1, pod" + str(i) + ", 1, 1);\n"
        else:
            pods_abs += "\t\tResourcesMonitor pod" + str(i) + " = new ResourcesMonitorObject(\"service 1\", " + str(i) + ", 1, " + str(int(pod['cpu'])*2) + ");\n"
            pods_abs += "\t\tPod p" + str(i) + " = new PodObject(\"service 1\", " + str(i) + ", 1, " + pod['cpu'] + ", " + str(int(pod['cpu'])*2) + ", pod" + str(i) + ", 1, 1);\n"

        pods_abs += "\t\tp" + str(i) + ".setName(\"" + pod['name'] + "\");\n"
        pods_abs += "\t\tp" + str(i) + ".consumeCpu(" + pod['cpu'] + ");\n"
        pods_abs += "\t\tp" + str(i) + ".consumeMemory(" + pod['memory'] + ");\n"

        pods_abs += "\t\tawait node!addPod(p" + str(i) + ", pod" + str(i) + ");\n"

        i += 1
    
    pods_abs += "\t}\n\n"

    pods_abs += "\tawait printer!printNodes(master,1,1);\n\tprintln(\"\");\n"

    pods_abs += "\n\tforeach (node in nodeList) {\n"
    pods_abs += "\t\tString name = node.getName();\n\t\tprintln(\"Node \" + name + \": \");\n"
    pods_abs += "\t\tList<Pod> pods = node.getPods();\n\t\tawait printer!printPods(pods);\n"
    pods_abs += "\t}\n\n"

    return pods_abs

def create_final_abs(prefix):
    final_abs = prefix

    final_abs += "\tawait duration(5,5);\n"
    final_abs += "}\n"

    return final_abs


def write_k8sdt_abs(file_name, final_abs):
    with open(file_name, 'w') as f:
        f.write(final_abs)
    

cluster_state = read_cluster_state('../real-k8s/cluster_state.json')
nodes_info = extract_nodes_info(cluster_state['nodes'])
pods_info = extract_pods_info(cluster_state['pods'])
prefix = get_prefix_abs('prefix_abs.txt')
nodes_abs = create_nodes_abs(prefix, nodes_info)
pods_abs = create_pods_abs(nodes_abs, pods_info)
final_abs = create_final_abs(pods_abs)
write_k8sdt_abs('K8sDT.abs', final_abs)
# print("DONE")
