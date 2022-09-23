from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from .utils import doWorkload
from datetime import datetime
import time


# Create your views here.
def index(request, request_size, date):
    start_time = time.time()
    date = datetime.fromisoformat(date)

    # Simulating doing something slow
    doWorkload(request_size)

    total_exec_time = str(time.time() - start_time)
    return JsonResponse({'request_size': request_size, 'exec_time': total_exec_time, 'date': date, 'timestamp': int(date.timestamp())})
