from pick import pick  # install pick using `pip install pick`

from kubernetes import client, config
from kubernetes.client import configuration

# Configs can be set in Configuration class directly or using helper utility
contexts, active_context = config.list_kube_config_contexts('/home/deepti/.kube/config')
if not contexts:
    print("Cannot find any context in kube-config file.")    
contexts = [context['name'] for context in contexts]
active_index = contexts.index(active_context['name'])
option, _ = pick(contexts, title="Pick the context to load",
                    default_index=active_index)
# Configs can be set in Configuration class directly or using helper
# utility
config.load_kube_config(context=option)

print("Active host is %s" % configuration.Configuration().host)

v1 = client.CoreV1Api()
print("Listing pods with their IPs:")
ret = v1.list_namespaced_service('default')
for i in ret.items:
    print(i)
