#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOGS_DIR=${SCRIPT_DIR}/logs
POD_LOGS_DIR=/tmp/autoscaleapp

# Pods share the same volume for storing logs, in other words from any pod with can get all logs
POD=$(minikube kubectl -- get pods | grep autoscaleapp | head -n 1 | awk '{print $1}')
if [[ -z ${POD} ]]; then
    echo "No pods found."
    exit 1
fi

# Backup prev logs
PREV_LOG=logs_$(date +%s)
PREV_LOGS_DIR=${LOGS_DIR}/${PREV_LOG}
mkdir -p ${PREV_LOGS_DIR}
mv ${LOGS_DIR}/*log ${PREV_LOGS_DIR}


echo "Copying files from pod: ${POD}"
minikube kubectl -- cp ${POD}:${POD_LOGS_DIR} ${LOGS_DIR} &> /dev/null

if [[ $? == 0 ]]; then
    echo "Copying files successfully..."
else
    echo "Failed to copy files :("
fi

