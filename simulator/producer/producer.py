#!/usr/bin/env python3
import requests
import argparse
import time
import random
import math
import multiprocessing as mp
import os
import subprocess
from datetime import datetime
from datetime import timedelta

REAL_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(REAL_PATH)

def doParseArgs():
    parser = argparse.ArgumentParser(description='Typical producer to send requests', conflict_handler='resolve')
    parser.add_argument('-h', '--host', default='localhost', help='Host to send the requests.', type=str)
    parser.add_argument('-p', '--port', default='8000', help='Host\'s port', type=int)
    parser.add_argument('-s', '--sleeptime', default='300', help='Usually used during non-peak hours (in milliseconds)', type=int)
    parser.add_argument('-i', '--interval', default='1m', help='Interval time between requests i.e 30s (s,m,h).', type=str)
    parser.add_argument('-t', '--producers', default='1', help='Number of producers', type=int)
    parser.add_argument('-u', '--use_parallelism', default='0', help='Use parallelism (0 false)', type=int)
    parser.add_argument('-d', '--start_date', default='2022-01-01', help='Year-Month-Day', type=str)
    parser.add_argument('-e', '--end_date', default='2023-01-01', help='Year-Month-Day', type=str)

    args_map = {}
    for argname, argval in parser.parse_args()._get_kwargs():
        args_map.update({argname:str(argval)})

    return args_map


# Lowest allowed value for metrics resolution is 10 seconds, bad for our simulation :(
def getPodsMetrics():
    script = DIR_PATH + '/pods_info.sh'
    metrics_raw_output = subprocess.check_output(script).decode().strip().split(' ')
    cpu_usage_accum, memory_usage_accum = 0, 0

    for i in range(0, len(metrics_raw_output), 2):
        cpu_usage_accum += int(metrics_raw_output[i][0:-1]) # i.e 129m
        memory_usage_accum += int(metrics_raw_output[i+1][0:-2]) # i.e 200Mi

    replicas = len(metrics_raw_output) // 2
    cpu_usage = round(cpu_usage_accum / replicas / 10, 2)
    memory_usage = memory_usage_accum // replicas
    return (cpu_usage, memory_usage, replicas)

def buildApiUrl(args_map,request_size, current_date, cpu_usage, memory_usage, replicas):
    api_url = 'http://' + args_map['host'] + ':' + args_map['port'] + '/' + \
        'simulation/' + str(request_size) + '/' + current_date + '/' + args_map['use_parallelism'] + \
        '/' + str(cpu_usage) + '/' + str(memory_usage) + '/' + str(replicas)
    return api_url


def requestSizeBasedOnDatetime(current_date:datetime) -> int:
    if current_date.hour > 3 and current_date.hour < 17: # Peak hours
        if not should_sleep(5):
            return int(random.randrange(500, 2000))
        else:
            return 0

    if current_date.hour < 9 or current_date.hour > 22: # Off-peak hours
        if not should_sleep(70):
            return int(random.randrange(200, 1000))
        else:
            return 0

    if should_sleep(10):
        return 0

    return int(random.randrange(100, 500))


def should_sleep(probability:int) -> bool:
    if probability == 0:
        return False

    max_range = 10 if (probability % 10 == 0) else 100
    probability = probability if (probability % 10 != 0) else probability // 10

    sleepy_numbers = set()
    while len(sleepy_numbers) < probability:
        sleepy_rand = random.randrange(0, max_range)
        sleepy_numbers.add(sleepy_rand)

    sleepy = random.randrange(0,max_range)
    if sleepy in sleepy_numbers:
        return True
    return False

def requestsPerProducer(producers_amount:int, request_size:int):
    remaining_request_size = request_size
    requests_per_producer = [0 for i in range(producers_amount)]

    for i in range(producers_amount):
        assigned_requests = int(math.floor(remaining_request_size / (producers_amount - i)))
        remaining_request_size -= assigned_requests
        requests_per_producer[i] = assigned_requests
        if remaining_request_size <= 0:
            break

    if remaining_request_size > 0:
        requests_per_producer[-1] += remaining_request_size

    return requests_per_producer


def requestsURLPerProducer(requests_size_arr, args_map, date):
    request_urls = []
    (cpu_usage, memory_usage, replicas) = getPodsMetrics()
    for request_size in requests_size_arr:
        api_url = buildApiUrl(args_map, request_size, date, cpu_usage, memory_usage, replicas)
        request_urls.append(api_url)
    return request_urls


def sendRequest(base_url):
    retries, MAX_RETRIES = 0, 20
    while retries < MAX_RETRIES:
        try:
            api_url = base_url + '/' + str(retries)
            response = requests.get(api_url, timeout=15)
            print(response.json())
            break
        except:
            print('ERROR: unable to process request')
            retries += 1
            continue


def parseInterval(interval:str) -> int:
    if interval.isdigit():
        return int(interval)

    unit = interval[-1]
    value = int(interval[0:-1])

    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    else:
        return value * 60 * 60


def spawnProducers(args_map):
    sleeptime = int(args_map['sleeptime']) / 1000
    current_date = datetime.fromisoformat(args_map['start_date'])
    end_date = datetime.fromisoformat(args_map['end_date'])
    interval = parseInterval(args_map['interval'])
    producers = int(args_map['producers'])

    while current_date < end_date:
        start_time = time.time()
        total_request_size = requestSizeBasedOnDatetime(current_date)
        requests_per_producer = requestsPerProducer(producers, total_request_size)
        request_urls = requestsURLPerProducer(requests_per_producer, args_map, current_date.isoformat())
        print('Total request size:',  total_request_size)
        print(requests_per_producer)
        print(request_urls)

        try:
            pool = mp.Pool(producers)
            pool.map(sendRequest, request_urls)
        finally:
            pool.close()
            pool.join()

        current_date += timedelta(seconds=interval)
        total_time = time.time() - start_time
        print('Time per request chunk sent:', total_time)


def sendRequests(args_map):
    sleeptime = int(args_map['sleeptime']) / 1000
    current_date = datetime.fromisoformat(args_map['start_date'])
    end_date = datetime.fromisoformat(args_map['end_date'])
    interval = int(args_map['interval'])
    retry, MAX_RETRIES = 0, 20

    while current_date < end_date:
        if retry >= MAX_RETRIES:
            print('ERROR: max number of retries reached. Exiting...')
            break

        request_size = requestSizeBasedOnDatetime(current_date)
        if request_size != 0:
            api_url = buildApiUrl(args_map, request_size, current_date.isoformat())
            # print('Sending request:', api_url)
            try:
                req = requests.get(api_url, timeout=5)
                retry = 0
                print(req.json())
            except:
                print('ERROR: connection with server was lost, retrying...')
                time.sleep(0.2)
                retry += 1
                continue
        else:
            print('Process sleeping for', sleeptime, 'seconds')
            time.sleep(sleeptime)
        current_date += timedelta(seconds=interval)


if __name__ == '__main__':
    args_map = doParseArgs()
    spawnProducers(args_map)

