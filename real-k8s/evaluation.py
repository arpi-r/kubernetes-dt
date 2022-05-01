from asyncio.subprocess import DEVNULL
import subprocess
import collections
import json
from pick import pick  # install pick using `pip install pick`

from kubernetes import client, config
from state_extractor import *


def generate_load():
    for i in range(1000):
        command = 'wget -q -O- http://localhost'
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    connect_to_cluster()
    get_resource_usage(eval=True)

if __name__ == '__main__':
    for i in range(100):
        generate_load()
