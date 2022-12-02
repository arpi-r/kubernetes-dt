from asyncio.subprocess import DEVNULL
import signal
import subprocess
import collections
import json
import os

from kubernetes import client, config
from signature_attack_detection import detect_attacks
from state_extractor import *

# todo - poll in separate thread
def poll_audit_logs():
    command = 'docker exec real-k8s-control-plane tail -f /var/log/kubernetes/kube-apiserver-audit.log'
    f = open("audit2.json", "w")
    p = subprocess.Popen(command, shell=True, stdout=f, stderr=subprocess.DEVNULL)
    print(p.pid)
    return p

def generate_load(p, timestep):
    for i in range(10):
        command = 'wget -q -O- http://localhost'
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    connect_to_cluster()
    attacks = detect_attacks(i)
    get_resource_usage(attacks, eval=True)
    if timestep == 99:
        p.kill()

if __name__ == '__main__':
    p = poll_audit_logs()
    for i in range(100):
        generate_load(p, i)
        
