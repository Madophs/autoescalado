import logging
import multiprocessing as mp
import threading
import math
import time

def doSqrt(request_size:int):
    for it in range(request_size):
        for i in range(10000000):
            math.sqrt(458475487548789181323449846102497)


def divideWork(request_size_input:int, CPUs:int):
    request_size = request_size_input
    cpu_remaining = CPUs
    threads_args = []

    if CPUs < request_size:
        while request_size > 0:
            input_to_handle = request_size // cpu_remaining
            request_size -= input_to_handle
            cpu_remaining -= 1
            threads_args.append(input_to_handle)
    else:
        for i in range(request_size):
            threads_args.append(1)

    return threads_args


def doWorkload(request_size:int):
    print("doWorkload: starting execution....")

    curr_process = mp.current_process()
    curr_process.daemon = False

    CPUs = mp.cpu_count()
    work_to_handle = divideWork(request_size, CPUs)

    with mp.Pool(CPUs) as p:
        p.map(doSqrt, work_to_handle)

    print("doWorkload: finishing execution....")


