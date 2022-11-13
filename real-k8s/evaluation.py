from asyncio.subprocess import DEVNULL
import subprocess
import collections
import json

from kubernetes import client, config
from state_extractor import *


def generate_load():
    for i in range(1000):
        command = 'wget -q -O- http://localhost'
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    connect_to_cluster()
    get_resource_usage(eval=True)

    # while True:
    #     command = 'docker exec real-k8s-control-plane tail -f /var/log/kubernetes/kube-apiserver-audit.log'
    #     f = open("audit.json", "r")
    #     subprocess.Popen(command, shell=True, stdout=f, stderr=subprocess.DEVNULL)

if __name__ == '__main__':
    generate_load()
