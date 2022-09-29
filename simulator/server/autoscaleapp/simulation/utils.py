import logging
import multiprocessing as mp
import threading
import math
import time
import logging
import os

logger = logging.getLogger('autoscaleapp')

def getLoopCycles() -> int:
    cycles = os.environ.get('LOOP_CYCLES')
    if cycles is None:
        cycles = 5000
    return int(cycles)


def doSqrt(request_size:int):
    for _ in range(request_size):
        for _ in range(getLoopCycles()):
            math.sqrt(458475487548789181323449846102497)


def divideWork(request_size_input:int, threads:int):
    request_size = request_size_input
    cpu_remaining = threads
    threads_args = []

    if threads < request_size:
        while request_size > 0:
            input_to_handle = request_size // cpu_remaining
            request_size -= input_to_handle
            cpu_remaining -= 1
            threads_args.append(input_to_handle)
    else:
        for i in range(request_size):
            threads_args.append(1)

    return threads_args


def containerized() -> bool:
    return (not os.environ.get('KUBERNETES_ENV') is None)


def parseCPUValue(value:str) -> int:
    if value is None:
        return 1

    if 'm' in value:
        value = value[0:-1]
        value_float = float(value) / 1000
        return int(math.ceil(value_float)) # Ceil CPU allocation value. i.e 500m -> 0.5 Cores -> 1 CPU thread (almost)
    else:
        return int(value)


def getCPULimit() -> int:
    cpu_limit = parseCPUValue(os.environ.get('CPU_LIMIT'))
    cpu_request = parseCPUValue(os.environ.get('CPU_REQUEST'))
    return int(max(cpu_request, cpu_limit))


def getCPUCount() -> int:
    if containerized():
        return getCPULimit()
    else:
        return mp.cpu_count()


def calculateThreads() -> int:
    CPUs = getCPUCount()
    if CPUs == 1:
        return 4
    if CPUs >= 2 and CPUs <= 4:
        return CPUs * 2

def parallelWorkload(request_size:int):
    curr_process = mp.current_process()
    curr_process.daemon = False

    no_threads = calculateThreads()

    logger.debug('Number possible threads: ' + str(no_threads))
    work_to_handle = divideWork(request_size, no_threads)

    try:
        pool = mp.Pool(no_threads)
        pool.map(doSqrt, work_to_handle)
    finally:
        pool.close()
        pool.join()


def doWorkload(request_size:int, use_parallelism:int):
    if use_parallelism == 0:
        logger.debug('Using a single CPU for processing')
        doSqrt(request_size)
    else:
        parallelWorkload(request_size)

