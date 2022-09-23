#!/usr/bin/env python3
import requests
import argparse
import time
import random
from datetime import datetime
from datetime import timedelta


def do_parse_args():
    parser = argparse.ArgumentParser(description='Typical producer to send requests', conflict_handler='resolve')
    parser.add_argument('-h', '--host', default='localhost', help='Host to send the requests.', type=str)
    parser.add_argument('-p', '--port', default='8000', help='Host\'s port', type=int)
    parser.add_argument('-s', '--sleeptime', default='300', help='Usually used during non-peak hours (in milliseconds)', type=int)
    parser.add_argument('-i', '--interval', default='60', help='Interval between requests in seconds.', type=int)
    parser.add_argument('-l', '--requests_per_day', default='5', help='Number of request per day', type=int)
    parser.add_argument('-d', '--start_date', default='2022-01-01', help='Year-Month-Day', type=str)
    parser.add_argument('-e', '--end_date', default='2023-01-01', help='Year-Month-Day', type=str)

    args_map = {}
    for argname, argval in parser.parse_args()._get_kwargs():
        args_map.update({argname:str(argval)})

    return args_map


def build_api_url(args_map,request_size, current_date):
    api_url = 'http://' + args_map['host'] + ':' + args_map['port'] + '/' + \
        'simulation/' + str(request_size) + '/' + current_date
    return api_url


def request_size_based_on_datetime(current_date:datetime) -> int:
    if current_date.hour > 8 and current_date.hour < 17: # Peak hours
        if not should_sleep(5):
            return int(random.randrange(1, 500))
        else:
            return 0

    if current_date.hour < 9 or current_date.hour > 22: # Off-peak hours
        if not should_sleep(70):
            return int(random.randrange(30, 80))
        else:
            return 0

    if should_sleep(10):
        return 0

    return int(random.randrange(20, 150))

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


def send_requests(args_map):
    sleeptime = int(args_map['sleeptime']) / 1000
    request_per_day = int(args_map['requests_per_day'])
    current_date = datetime.fromisoformat(args_map['start_date'])
    end_date = datetime.fromisoformat(args_map['end_date'])
    interval = int(args_map['interval'])
    while current_date < end_date:
        request_size = request_size_based_on_datetime(current_date)
        if request_size != 0:
            api_url = build_api_url(args_map, request_size, current_date.isoformat())
            # print('Sending request:', api_url)
            req = requests.get(api_url, timeout=3)
            print(req.json())
        else:
            print('Process sleeping for', sleeptime, 'seconds')
            time.sleep(sleeptime)
        current_date += timedelta(seconds=interval)


if __name__ == '__main__':
    args_map = do_parse_args()
    send_requests(args_map)

