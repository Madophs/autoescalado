from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from .utils import doWorkload
from datetime import datetime
import time
import logging

logger = logging.getLogger('autoscaleapp')

# Create your views here.
def index(request, request_size, date, parallelism, cpu_usage, memory_usage, replicas, retries):
    start_time = time.time()
    date = datetime.fromisoformat(date)

    # Simulating doing something slow
    doWorkload(request_size, parallelism)

    total_exec_time = str(round(time.time() - start_time, 4))

    response = {'request_size': request_size, 'exec_time': total_exec_time, 'date': date.isoformat(), \
                'timestamp': int(date.timestamp()), 'retries': retries, 'cpu_usage': str(cpu_usage), \
                'memory_usage': str(memory_usage), 'replicas': replicas}
    logger.info(response)
    return JsonResponse(response)
