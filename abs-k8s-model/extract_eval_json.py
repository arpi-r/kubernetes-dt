import json
import os

def read_file(filename):
    lines = []
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    return lines

def read_original_cluster_state(file_name):
    with open(file_name, 'r') as f:
        cluster_state = json.load(f)
        return cluster_state

def extract_cluster_pod_info(pods):
    pods_info = {}
    
    for pod in pods:
        pod_info = {}
        pod_info['cpu'] = pod['containers'][0]['usage']['cpu']
        cpu_len = len(pod_info['cpu'])
        if pod_info['cpu'][cpu_len - 1] == 'n':
            pod_info['cpu'] = pod_info['cpu'][:cpu_len - 1]
        elif pod_info['cpu'][cpu_len - 1] == 'm':
            pod_info['cpu'] = pod_info['cpu'][:cpu_len - 1]
        pod_info['memory'] = pod['containers'][0]['usage']['memory']
        mem_len = len(pod_info['memory'])
        if pod_info['memory'][mem_len - 2:] == 'Ki':
            pod_info['memory'] = pod_info['memory'][:mem_len - 2]
        pod_info['cpu_limit'] = pod['containers'][0]['cpu_limit']
        cpu_lim_len = len(pod_info['cpu_limit'])
        if pod_info['cpu_limit'][cpu_lim_len - 1] == 'm':
            pod_info['cpu_limit'] = pod_info['cpu_limit'][:cpu_lim_len - 1]
        elif pod_info['cpu_limit'][cpu_lim_len - 1] == 'n':
            pod_info['cpu_limit'] = pod_info['cpu_limit'][:cpu_lim_len - 1]
        
        pods_info[pod['name']] = pod_info

    return pods_info

def extract_cluster_node_info(nodes):
    nodes_info = {}
    
    for node in nodes:
        node_info = {}
        node_info['cpu'] = node['cpu']
        cpu_len = len(node_info['cpu'])
        if node_info['cpu'][cpu_len - 1] == 'n':
            node_info['cpu'] = node_info['cpu'][:cpu_len - 1]
        elif node_info['cpu'][cpu_len - 1] == 'm':
            node_info['cpu'] = node_info['cpu'][:cpu_len - 1]
        node_info['memory'] = node['memory']
        mem_len = len(node_info['memory'])
        if node_info['memory'][mem_len - 2:] == 'Ki':
            node_info['memory'] = node_info['memory'][:mem_len - 2]
        node_info['pods'] = extract_cluster_pod_info(node['pods'])
        nodes_info[node['name']] = node_info
        
    return nodes_info

def get_pod_names(line, pod_names):
    pod_names.append(line.split(" ")[1].strip())

    return pod_names

def get_run_num(line):
    return line.split(" ")[1].strip()

def get_node_info(lines):
    nodes_info = []

    for line in lines:
        node_info = {}
        line = line.split(" ")
        # print(line)
        node_info["name"] = line[1].strip()
        node_info["cpu_load_num"] = line[11].strip()
        node_info["cpu_load_den"] = line[13].strip()
        node_info["cpu_req_num"] = line[19].strip()
        node_info["cpu_req_den"] = line[21].strip()
        node_info["mem_num"] = line[27].strip()
        node_info["mem_den"] = line[29].strip()
        node_info["pods"] = []

        nodes_info.append(node_info)

    return nodes_info

def get_pod_info(lines, pod_names):
    pods_info = []

    for line in lines:
        pod_info = {}
        line = line.split(" ")
        # print(line)
        pod_id = int(line[1].strip())
        if pod_id < len(pod_names):
            pod_info["name"] = pod_names[pod_id]
        else:
            pod_info["name"] = "pod-" + str(pod_id)
        pod_info["node"] = line[6].strip()
        pod_info["cpu"] = line[11].strip()
        pod_info["memory"] = line[17].strip()

        pods_info.append(pod_info)

    return pods_info

def generate_eval_json(run_info, cluster_info):
    eval_json_list = []

    for run in run_info:
        new_run_info = {}
        new_run_info["nodes"] = []
        new_node_info = {}

        for node in run_info[run]["node_info"]:
            new_node_info["name"] = node["name"]
            cluster_node_info = cluster_info[node["name"]]
            cluster_pod_info = cluster_node_info["pods"]
            new_node_info["cpu"] = str((int(node["cpu_load_num"]) * 1000000) + int(cluster_node_info["cpu"]))
            if new_node_info["cpu"] != "0":
                new_node_info["cpu"] = new_node_info["cpu"] + "n"
            new_node_info["memory"] = str(int(node["mem_num"]) + int(cluster_node_info["memory"])) 
            if new_node_info["memory"] != "0":
                new_node_info["memory"] = new_node_info["memory"] + "Ki"
            new_node_info["pods"] = []

            for pod in run_info[run]["pod_info"]:
                if pod["node"] != node["name"]:
                    continue
                new_pod_info = {}
                new_pod_info["name"] = pod["name"]
                new_pod_info["containers"] = []
                pod_container_info = {}
                pod_container_info["name"] = "nginx"
                pod_container_info["usage"] = {}

                if cluster_pod_info != {} and pod["name"] in cluster_pod_info:
                    pod_container_info["usage"]["cpu"] = str((int(pod["cpu"]) * 1000000) + int(cluster_pod_info[pod["name"]]["cpu"]))
                    pod_container_info["usage"]["memory"] = str(int(pod["memory"]) + int(cluster_pod_info[pod["name"]]["memory"]))
                else:
                    pod_container_info["usage"]["cpu"] = str(int(pod["cpu"]) * 1000000)
                    pod_container_info["usage"]["memory"] = pod["memory"]
                
                if pod_container_info["usage"]["cpu"] != "0":
                    pod_container_info["usage"]["cpu"] = pod_container_info["usage"]["cpu"] + "n"
                if pod_container_info["usage"]["memory"] != "0":
                    pod_container_info["usage"]["memory"] = pod_container_info["usage"]["memory"] + "Ki"
                
                pod_container_info["cpu_limit"] = "500m"
                new_pod_info["containers"].append(pod_container_info.copy())
                new_node_info["pods"].append(new_pod_info.copy())

            new_run_info["nodes"].append(new_node_info.copy())

        # new_run_info["nodes"].append(new_node_info)
        eval_json_list.append(new_run_info.copy())

    return eval_json_list

def parse_lines(lines):
    lines_len = len(lines)
    pod_names = []
    run = 0
    run_info = {}

    for i in range(lines_len):
        line = lines[i]

        if "RUN" in line:
            run = get_run_num(line)
            run_info[run] = {}
            # print("run: " + run)

        if "ID" in line:
            pod_names = get_pod_names(line, pod_names)
            # print(line)
        
        if "node info:" in line:
            node_info = get_node_info(lines[i+3:i+5])
            run_info[run]["node_info"] = node_info
            # print(lines[i+3:i+5])
        
        if "service info:" in line:
            pod_info = get_pod_info(lines[i+4:i+8], pod_names)
            run_info[run]["pod_info"] = pod_info
            # print(lines[i+4:i+8])

    return run_info

def write_to_json_file(json_list, file_name):
    eval_json = json.dumps(json_list, indent=2)
    with open(file_name, 'w') as outfile:
        outfile.write(eval_json)

lines = read_file('k8sdt_out_main.txt')
run_info = parse_lines(lines)
# print(json.dumps(run_info, indent=2))
cluster_state = read_original_cluster_state('../real-k8s/cluster_state.json')
cluster_info = extract_cluster_node_info(cluster_state['nodes'])
# print(cluster_info)
eval_json_list = generate_eval_json(run_info, cluster_info)
# print(json.dumps(eval_json_list, indent=2))
write_to_json_file(eval_json_list, "eval.json")
# print(run_info["1"])
