#!/bin/sh

if [ "$#" -ne 1 ]; then
    echo "Incorrect usage"
    echo "Usage: bash $0 <path_to_cluster_state_file>"
    exit 1
fi

pwd=$(pwd)
# echo $pwd

echo "running state_mapper.py... "
python3 $pwd/../abs-k8s-model/state_mapper.py $1
if [ "$?" -ne 0 ]; then
    echo "Error generating K8sDT.abs"
    exit 1
fi
echo "K8sDT.abs generated"
echo "Compiling K8sDT.abs... "
java -jar $pwd/../abs-k8s-model/absfrontend.jar --erlang $pwd/../abs-k8s-model/model/K8sService.abs $pwd/../abs-k8s-model/model/K8sMaster.abs $pwd/../abs-k8s-model/model/K8sUtil.abs $pwd/../abs-k8s-model/model/K8sWorkflow.abs $pwd/../abs-k8s-model/K8sDT.abs
if [ "$?" -ne 0 ]; then
    echo "Error compiling K8sDT.abs"
    exit 1
fi
echo "K8sDT.abs compiled"
echo "Running K8sDT.abs... "
echo ""
echo ""
echo ""
$pwd/../abs-k8s-model/gen/erl/run | tee $pwd/../abs-k8s-model/K8sDT_output.txt
