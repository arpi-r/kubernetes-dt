from asyncio.subprocess import DEVNULL
import subprocess
import collections
import json

from kubernetes import client, config
from signature_attack_detection import detect_attacks
from state_extractor import *

# todo - poll in separate thread
def poll_audit_logs():
    command = 'docker exec real-k8s-control-plane tail -f /var/log/kubernetes/kube-apiserver-audit.log'
    f = open("audit.json", "r")
    subprocess.Popen(command, shell=True, stdout=f, stderr=subprocess.DEVNULL)

def generate_load():
    for i in range(1000):
        command = 'wget -q -O- http://localhost'
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    poll_audit_logs()
    connect_to_cluster()
    attacks = detect_attacks(i)
    get_resource_usage(attacks, eval=True)

if __name__ == '__main__':
    for i in range(1000):
        generate_load()
