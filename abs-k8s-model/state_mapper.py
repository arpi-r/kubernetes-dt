import json
import os
import subprocess

def read_cluster_state(file_name):
    with open(file_name, 'r') as f:
        cluster_state = json.load(f)
        return cluster_state

def extract_service_info(services, numPods):
    services_info = []

    for service in services:
        service_info = {}
        service_info['name'] = service['name']
        service_info['maxPods'] = str(service['maxPods'])
        service_info['minPods'] = str(service['minPods'])
        service_info['upscaleThreshold'] = str(service['upscaleThreshold']) + "/100"
        service_info['downscalePeriod'] = str(service['downscalePeriod'])
        service_info['downscaleThreshold'] = "5/100"
        service_info['scalerCycle'] = "1"
        # service_info['startingPods'] = str(numPods)
        service_info['startingPods'] = str(1)
        services_info.append(service_info)

    return services_info

def extract_pods_info(pods):
    pods_info = []
    pod_info = {}
    for pod in pods:
        pod_info['name'] = pod['name']
        pod_info['cpu'] = pod['containers'][0]['usage']['cpu']
        cpu_len = len(pod_info['cpu'])
        if pod_info['cpu'][cpu_len - 1] == 'n':
            # pod_info['cpu'] = pod_info['cpu'][:cpu_len - 1]
            pod_info['cpu'] = str(int(pod_info['cpu'][:cpu_len - 1]) / 1000000)
        elif pod_info['cpu'][cpu_len - 1] == 'm':
            # pod_info['cpu'] = str(int(pod_info['cpu'][:cpu_len - 1]) * 1000000)
            pod_info['cpu'] = pod_info['cpu'][:cpu_len - 1]
        pod_info['memory'] = pod['containers'][0]['usage']['memory']
        mem_len = len(pod_info['memory'])
        if pod_info['memory'][mem_len - 2:] == 'Ki':
            pod_info['memory'] = pod_info['memory'][:mem_len - 2]
        pod_info['cpu_limit'] = pod['containers'][0]['cpu_limit']
        cpu_lim_len = len(pod_info['cpu_limit'])
        if pod_info['cpu_limit'][cpu_lim_len - 1] == 'm':
            # pod_info['cpu_limit'] = str(int(pod_info['cpu_limit'][:cpu_lim_len - 1]) * 1000000)
            pod_info['cpu_limit'] = pod_info['cpu_limit'][:cpu_lim_len - 1]
        elif pod_info['cpu_limit'][cpu_lim_len - 1] == 'n':
            # pod_info['cpu_limit'] = pod_info['cpu_limit'][:cpu_lim_len - 1]
            pod_info['cpu_limit'] = str(int(pod_info['cpu_limit'][:cpu_lim_len - 1]) / 1000000)
        pods_info.append(pod_info)
        pod_info = {}

    return pods_info

def extract_nodes_info(nodes):
    nodes_info = []
    node_info = {}
    for node in nodes:
        node_info['name'] = node['name']
        node_info['cpu'] = node['cpu']
        cpu_len = len(node_info['cpu'])
        if node_info['cpu'][cpu_len - 1] == 'n':
            # node_info['cpu'] = node_info['cpu'][:cpu_len - 1]
            node_info['cpu'] = str(int(node_info['cpu'][:cpu_len - 1]) / 1000000)
        elif node_info['cpu'][cpu_len - 1] == 'm':
            # node_info['cpu'] = str(int(node_info['cpu'][:cpu_len - 1]) * 1000000)
            node_info['cpu'] = node_info['cpu'][:cpu_len - 1]
        node_info['memory'] = node['memory']
        mem_len = len(node_info['memory'])
        if node_info['memory'][mem_len - 2:] == 'Ki':
            node_info['memory'] = node_info['memory'][:mem_len - 2]
        node_info['pods'] = extract_pods_info(node['pods'])
        nodes_info.append(node_info)
        node_info = {}
        
    return nodes_info

def getNumPods(nodes_info):
    numPods = 0
    for node in nodes_info:
        numPods += len(node['pods'])
    return numPods

def get_prefix_abs(file_name):
    with open(file_name, 'r') as f:
        prefix = f.read()
        # print(prefix)
    return prefix

def create_topo_abs(prefix, nodes_info, service):
    main_abs = prefix

    for node in nodes_info:
        main_abs += "\n" + "\tfb = master.createNode(rat(" + node['cpu'] + "), " + node['memory'] + ");"

    main_abs += "\n\n"
    
    main_abs += "\tList<String> nodeNames = list[];\n"
    for node in nodes_info:
        main_abs += "\tnodeNames = appendright(nodeNames,\"" + node['name'] + "\");\n"

    main_abs += "\n\tList<Node> nodeList = master.getNodes();\n\tInt c = 0;\n\tforeach (node in nodeList) {\n"
    main_abs += "\t\tString name = nth(nodeNames,c);\n\t\tnode!setName(name);\n"
    # main_abs += "\n\t\tList<Pod> pods = node.getPods();\n\t\tawait printer!printPods(pods);\n"
    main_abs += "\n\t\tc = c + 1;\n"
    main_abs += "\t}\n\n"

    # main_abs += "\tawait printer!printNodes(master,1,1);\n"
    
    return main_abs

def create_service_abs(prefix, services, nodes):
    service_abs = prefix

    service_abs += "\n\tServiceLoadBalancerPolicy policy = new RoundRobinLbPolicy();\n"
    service_abs += "\n\tList<Service> serviceList = list[];\n"
    service = services[0]
    service_abs += "\tServiceConfig service1Config = ServiceConfig(\"" + service['name'] + "\", " + service['startingPods'] \
                    + ", " + service['minPods'] + ", " + service['maxPods'] + ", " + service['scalerCycle'] + ",  " \
                    + service['upscaleThreshold'] + ", " + service['downscaleThreshold'] + ", " + service['downscalePeriod'] + ");\n"
    
    service_abs += "\tNode n = nth(nodeList, 0);\n\n"
    service_abs += "\tList<Node> deploy_node_list = list[];\n\tList<PodConfig> pod_config_list = list[];\n"
    service_abs += "\tList<String> podNames = list[];\n\n"

    node_count = 0
    pod_count = 1
    service_count = 1
    for node in nodes:
        for pod in node['pods']:
            # Rat compUnitSize, Rat monitorCycle, Rat memoryCooldown, Rat cpuRequest, Rat cpuLimit
            # should memory cooldown value be pod['memory'] or will that be used sometime later?
            service_abs += "\tPodConfig pod" + str(pod_count) + "Config = PodConfig(1, 1, 15, rat(" + pod['cpu'] + "), " + pod['cpu_limit'] + ");\n"
            service_abs += "\tpod_config_list = appendright(pod_config_list,pod" + str(pod_count) + "Config);\n"
            # service_abs += "\tService service" + str(service_count) + " = new ServiceObject(service1Config, pod" + str(pod_count) + "Config, policy);\n"
            # service_abs += "\tserviceList = appendright(serviceList, service" + str(service_count) + ");\n"
            service_abs += "\tn = nth(nodeList, " + str(node_count) + ");\n"
            service_abs += "\tdeploy_node_list = appendright(deploy_node_list,n);\n"
            # service_abs += "\tmaster.deployServiceOnNode(service" + str(service_count) + ", n, \"" + pod['name'] + "\");\n"\
            service_abs += "\tpodNames = appendright(podNames,\"" + pod['name'] + "\");\n"

            pod_count += 1
            service_count += 1
        node_count += 1
    
    # service_abs += "\tService service_" + service['name'] + " = new ServiceObject(service_" + service['name'] + "_config, pod_config_list, policy);\n"
    service_abs += "\tService service1 = new ServiceObject(service1Config, pod_config_list, policy);\n"
    service_abs += "\tserviceList = appendright(serviceList, service1);\n"
    service_abs += "\n\tmaster.deployServiceOnNodes(service1, deploy_node_list, podNames);\n"
    
    service_abs += "\n\tList<ServiceEndpoint> endpoints = list[];\n"
    service_abs += "\tforeach (service in serviceList) {\n"
    # service_abs += "\t\tmaster.deployService(service);\n"
    service_abs += "\t\tServiceEndpoint serviceEP = await service!getServiceEndpoint();\n"
    service_abs += "\t\tendpoints = appendright(endpoints, serviceEP);\n"
    # service_abs += "\t\tawait printer!printService(service, 1, 1);\n"
    service_abs += "\t}\n"

    return service_abs

def create_requests_abs(prefix):
    final_abs = prefix
    final_abs += "\n\tprint(\"INITIAL\");\n"
    final_abs += "\tawait printer!printDT(master, serviceList);\n"

    final_abs += "\tInt perfi = 0;\n"
    final_abs += "\twhile (perfi < 100) {\n"
    final_abs += "\t\tprintln(\"RUN: \" + toString(perfi) + \"\\n\");\n"
    final_abs += "\t\tInt ri = 0;\n"
    final_abs += "\t\tList<ServiceTask> service_tasks = list[];\n"
    final_abs += "\t\twhile (ri < 1000) {\n"
    final_abs += "\t\t\tRequest request1 = Request(\"request_1\", rat(64.6), rat(29.446), 1);\n"
    final_abs += "\t\t\tServiceTask task1 = new ServiceRequest(nth(endpoints,0),request1);\n"
    final_abs += "\t\t\tservice_tasks = appendright(service_tasks,task1);\n"
    final_abs += "\n\t\t\tri = ri + 1;\n\t\t}\n"

    final_abs += "\n\t\tList<List<ServiceTask>> tasks = list[];\n"
    final_abs += "\t\ttasks = appendright(tasks,service_tasks);\n"
    final_abs += "\t\tServiceTask workflow1 = new ServiceWorkflow(tasks);\n"
    final_abs += "\t\tClient c1 = new ClientWorkflow(workflow1,1,rat(10.0),1);\n"
    final_abs += "\t\tList<Rat> rts = await c1!start();\n"

    final_abs += "\n\t\tforeach (t in rts){\n"
    final_abs += "\t\t\tprintln(\"c1 avg response time:\" + toString(float(t)));\n\t\t}\n"
    final_abs += "\t\tprintln(\"\\n\\nservice info:\\n\\n\");\n"
    final_abs += "\t\tawait printer!printService(service1, 1, 1);\n"
    final_abs += "\n\t\tperfi = perfi + 1;\n\t}\n"

    return final_abs

def create_final_abs(prefix):
    final_abs = prefix

    # final_abs += "\tawait printer!printNodes(master,1,1);\n"
    # final_abs += "\n\tawait printer!printDT(master, serviceList);\n"

    final_abs += "\n\tawait duration(5,5);\n"
    final_abs += "}\n"

    return final_abs


def write_k8sdt_abs(file_name, final_abs):
    with open(file_name, 'w') as f:
        f.write(final_abs)
    

cluster_state = read_cluster_state('../real-k8s/cluster_state.json')
nodes_info = extract_nodes_info(cluster_state['nodes'])
# print()
# print(nodes_info)
services_info = extract_service_info(cluster_state['services'], getNumPods(nodes_info))
# print()
# print(service)
prefix = get_prefix_abs('prefix_abs.txt')
main_abs = create_topo_abs(prefix, nodes_info, services_info[0])
service_abs = create_service_abs(main_abs, services_info, nodes_info)
requests_abs = create_requests_abs(service_abs)
final_abs = create_final_abs(requests_abs)
# print()
# print(final_abs)
write_k8sdt_abs('K8sDT.abs', final_abs)
# print("DONE")
