#!/bin/sh

echo "running state_mapper.py... "
python3 state_mapper.py
echo "K8sDT.abs generated"
echo "Compiling K8sDT.abs... "
java -jar absfrontend.jar --erlang ./model/K8sService.abs ./model/K8sMaster.abs ./model/K8sUtil.abs ./model/K8sWorkflow.abs ./K8sDT.abs
echo "K8sDT.abs compiled"
echo "Running K8sDT.abs... "
echo ""
echo ""
echo ""
./gen/erl/run