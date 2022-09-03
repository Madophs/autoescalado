from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from .utils import doWorkload
import time

# Create your views here.
def index(request):
    start_time = time.time()

    request_size = int(request.GET['req_size'])

    # Simulating doing something slow
    doWorkload(request_size)

    total_exec_time = str(time.time() - start_time)
    return JsonResponse({'request_size': request_size, 'exec_time': total_exec_time})
