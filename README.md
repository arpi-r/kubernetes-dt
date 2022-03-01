# kubernetes-dt
Digital Twinning Framework for Kubernetes

This repo contains a git submodule: abs-k8s-model. To clone this repo:
`git clone --recurse-submodules https://github.com/arpi-r/kubernetes-dt`.

## Running the ABS Kubernetes Models:

[ABS documentation](https://abs-models.org/getting_started/local-install/)

TLDR:

### Dependencies:
 - Java
 - Erlang

Installing on Mac:
```bash
brew tap adoptopenjdk/openjdk
brew install erlang git adoptopenjdk11
```
Installing on Linux:

 - Install JDK11, Erlang >= 23, and a C compiler

### Running a test
```bash
cd abs-k8s-model/model/
```

#### Compile with Docker:
```bash
docker run --rm -v "$PWD":/usr/src -w /usr/src abslang/absc:latest --erlang K8sService.abs K8sMaster.abs K8sUtil.abs K8sWorkflow.abs ./tests/<test_name>.abs
```
OR
#### Compile with Pre-built ABS Compiler:
A pre-built `absfrontend.jar` of the current release of ABS is always linked [here](https://github.com/abstools/abstools/releases/latest).
Download the jar file and compile as shown below:
```bash
java -jar absfrontend.jar --erlang K8sService.abs K8sMaster.abs K8sUtil.abs K8sWorkflow.abs ./tests/<test_name>.abs
```
THEN
#### Run:
```bash
./gen/erl/run
```    
