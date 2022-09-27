#!/bin/bash
minikube kubectl -- top pods | grep autoscaleapp | awk '{print $2" "$3}' | tr '\n' ' '
