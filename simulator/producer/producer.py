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
from enum import Enum

REAL_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(REAL_PATH)
peak_dates = []

class Traffic(Enum):
    SLEEPING    = 0
    VERY_LOW    = 1
    LOW         = 2
    AVERAGE     = 3
    HIGH        = 4
    VERY_HIGH   = 5
    PEAK        = 6


def doParseArgs():
    parser = argparse.ArgumentParser(description='Typical producer to send requests', conflict_handler='resolve')
    parser.add_argument('-h', '--host', default='localhost', help='Host to send the requests.', type=str)
    parser.add_argument('-p', '--port', default='8000', help='Host\'s port', type=int)
    parser.add_argument('-s', '--sleeptime', default='500', help='Usually used during non-peak hours (in milliseconds)', type=int)
    parser.add_argument('-i', '--interval', default='1m', help='Interval time between requests i.e 30s (s,m,h).', type=str)
    parser.add_argument('-t', '--producers', default='1', help='Number of producers', type=int)
    parser.add_argument('-u', '--use_parallelism', default='0', help='Use parallelism (0 false)', type=int)
    parser.add_argument('-d', '--start_date', default='2022-01-01', help='Year-Month-Day', type=str)
    parser.add_argument('-e', '--end_date', default='2023-01-01', help='Year-Month-Day', type=str)
    parser.add_argument('-k', '--peak', default='2022-11-25,2022-11-26', help='-k "2022-11-25,2022-11-26|2022-12-25,etc..."', type=str)

    args_map = {}
    for argname, argval in parser.parse_args()._get_kwargs():
        args_map.update({argname:str(argval)})

    return args_map


def setPeakDates(args_map):
    date_pairs = args_map['peak'].split('|')
    for pair in date_pairs:
        splitted_dates = pair.split(',')
        peak_date_start = datetime.fromisoformat(splitted_dates[0])
        peak_date_end = datetime.fromisoformat(splitted_dates[1])
        peak_dates.append((peak_date_start, peak_date_end))


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


def isPeakDate(current_date:datetime) -> bool:
    for (peak_date_start, peak_date_end) in peak_dates:
        if peak_date_start <= current_date and \
                peak_date_end >= current_date:
            return True
    return False


def requestSizeBasedOnDatetime(current_date:datetime) -> int:
    traffic = Traffic.AVERAGE
    prob_decrease = 0

    if current_date.hour >= 9 and current_date.hour < 15:
        traffic = Traffic.HIGH
        prob_decrease = 5

    if current_date.hour >= 15 and current_date.hour < 19:
        traffic = Traffic.AVERAGE
        prob_decrease = 5

    if (current_date.hour >= 19 and current_date.hour <= 22) \
            or (current_date.hour >= 5 and current_date.hour < 7):
        traffic = Traffic.LOW
        prob_decrease = 10

    if current_date.hour >= 22 or current_date.hour < 1:
        traffic = Traffic.VERY_LOW

    if current_date.hour >= 1 and current_date.hour < 5:
        traffic = Traffic.SLEEPING

    if current_date.weekday() == 5 or current_date.weekday() == 6: # Weekend
        prob_decrease = 90

    if isPeakDate(current_date):
        traffic = Traffic(traffic.value + 1)

    return (getRandomTraffic(traffic, prob_decrease), traffic)


def getRandomTraffic(traffic:Traffic, prob_low_traffic:int) -> int:
    if decreaseTraffic(prob_low_traffic):
        traffic = Traffic(min(traffic.value, max(Traffic.VERY_LOW.value, traffic.value - 1)))

    if traffic is Traffic.PEAK:
        return int(random.randrange(2700, 3050))
    if traffic is Traffic.VERY_HIGH:
        return int(random.randrange(2300, 2700))
    elif traffic is Traffic.HIGH:
        return int(random.randrange(2000, 2500))
    elif traffic is Traffic.AVERAGE:
        return int(random.randrange(1700, 2100))
    elif traffic is Traffic.LOW:
        return int(random.randrange(1000, 1500))
    elif traffic is Traffic.VERY_LOW:
        return int(random.randrange(800, 1200))
    else:
        return int(random.randrange(100, 300))


# Probablity to decrease traffic
def decreaseTraffic(probability:int) -> bool:
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
    setPeakDates(args_map)

    while current_date < end_date:
        start_time = time.time()
        (total_request_size, traffic_level) = requestSizeBasedOnDatetime(current_date)
        requests_per_producer = requestsPerProducer(producers, total_request_size)
        request_urls = requestsURLPerProducer(requests_per_producer, args_map, current_date.isoformat())

        try:
            pool = mp.Pool(producers)
            pool.map(sendRequest, request_urls)
        finally:
            pool.close()
            pool.join()

        # Take a nap to decrease CPU usage during simulation
        if traffic_level is Traffic.VERY_LOW or traffic_level is Traffic.SLEEPING:
            time.sleep(sleeptime)

        current_date += timedelta(seconds=interval)
        total_time = time.time() - start_time


if __name__ == '__main__':
    args_map = doParseArgs()
    spawnProducers(args_map)

