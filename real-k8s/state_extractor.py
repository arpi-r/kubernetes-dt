import collections
import json
from pick import pick  # install pick using `pip install pick`

from kubernetes import client, config


def connect_to_cluster():
    # Configs can be set in Configuration class directly or using helper utility
    contexts, active_context = config.list_kube_config_contexts(
        '/home/deepti/.kube/config')
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
    k8s_pods = api.list_cluster_custom_object(
        "metrics.k8s.io", "v1beta1", "pods")
    for stats in k8s_pods['items']:
        if stats['metadata']['namespace'] == 'default':
            containers = []
            for container in stats['containers']:
                containers.append(container)
            pod = {
                'name': stats['metadata']['name'],
                'containers': containers
            }
            pods.append(pod)
    print(pods)
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

    print(nodes)
    return nodes


def get_resource_usage():
    api = client.CustomObjectsApi()
    pods = get_pods_usage(api)
    nodes = get_nodes_usage(api)

    cluster_usage = {
        'nodes': nodes,
        'pods': pods
    }

    with open('./cluster_state.json', 'w') as f:
        state = json.dumps(cluster_usage, indent=2)
        f.write(state)


if __name__ == '__main__':
    connect_to_cluster()
    get_resource_usage()
