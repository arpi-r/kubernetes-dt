import collections
import json

from kubernetes import client, config


def connect_to_cluster():
    # Configs can be set in Configuration class directly or using helper utility
    contexts, active_context = config.list_kube_config_contexts(
        '~/.kube/config')
    if not contexts:
        print("Cannot find any context in kube-config file.")
    contexts = [context['name'] for context in contexts]
    active_index = contexts.index(active_context['name'])
    # option, _ = pick(contexts, title="Pick the context to load", default_index=active_index)
    # Configs can be set in Configuration class directly or using helper
    # utility

    option = 'kind-real-k8s'
    config.load_kube_config(context=option)


def get_pods_usage(api):
    pods = []
    v1 = client.CoreV1Api()
    list_of_pods = v1.list_namespaced_pod('default', watch=False)
    k8s_pods = api.list_cluster_custom_object(
        "metrics.k8s.io", "v1beta1", "pods")
    for stats in k8s_pods['items']:
        if stats['metadata']['namespace'] == 'default':
            containers = []
            for container in stats['containers']:
                for p in list_of_pods.items:
                    if p.metadata.name == stats['metadata']['name']:
                        cur_pod = p
                        for pod_container in cur_pod.spec.containers:
                            if pod_container.name == container['name']:
                                container['cpu_limit'] = pod_container.resources.limits['cpu']
                        containers.append(container)

            pod = {
                'name': stats['metadata']['name'],
                'containers': containers
            }
            pods.append(pod)
    return pods


def get_nodes_usage(api):
    nodes = []
    k8s_nodes = api.list_cluster_custom_object(
        "metrics.k8s.io", "v1beta1", "nodes")
    for stats in k8s_nodes['items']:
        node = {
            'name': stats['metadata']['name'],
            'cpu': stats['usage']['cpu'],
            'memory': stats['usage']['memory']
        }
        nodes.append(node)

    return nodes


def get_service_info():
    api = client.AutoscalingV1Api()
    hpa = api.list_horizontal_pod_autoscaler_for_all_namespaces(watch=False)
    services = []
    for scaler in hpa.items:
        if scaler.metadata.namespace == 'default':
            annotations = json.loads(
                scaler.metadata.annotations['autoscaling.alpha.kubernetes.io/behavior'])
            service = {
                'name': scaler.metadata.name,
                'maxPods': scaler.spec.max_replicas,
                'minPods': scaler.spec.min_replicas,
                'upscaleThreshold': scaler.spec.target_cpu_utilization_percentage,
                'downscalePeriod': annotations['ScaleDown']['StabilizationWindowSeconds']
            }
            services.append(service)
    return services


def map_nodes_to_pods(pods, nodes):
    v1 = client.CoreV1Api()
    for node in nodes:
        node['pods'] = []
        field_selector = 'spec.nodeName=' + node['name']
        pods_on_node = v1.list_pod_for_all_namespaces(
            watch=False, field_selector=field_selector)
        for pod in pods_on_node.items:
            for pod_on_node in pods:
                if pod.metadata.name == pod_on_node['name']:
                    node['pods'].append(pod_on_node)


def get_resource_usage(eval=False):
    api = client.CustomObjectsApi()
    pods = get_pods_usage(api)
    nodes = get_nodes_usage(api)

    map_nodes_to_pods(pods, nodes)
    services = get_service_info()

    cluster_usage = {}

    if eval:
        cluster_usage = {
            'nodes': nodes
        }
    else:
        cluster_usage = {
            'services': services,
            'nodes': nodes
        }

    with open('./new_evaluations/test.json', 'a+') as f:
        state = json.dumps(cluster_usage, indent=2)
        f.write(state)
        f.write(',')


if __name__ == '__main__':
    connect_to_cluster()
    get_resource_usage()
