#!/usr/bin/python3
import requests
import argparse
import multiprocessing as mp
import time

def do_parse_args():
    parser = argparse.ArgumentParser(description='Typical producer to send requests', conflict_handler='resolve')

    parser.add_argument('-h', '--host', default='localhost', help='Host to send the requests.', type=str)
    parser.add_argument('-p', '--port', default='8000', help='Host\'s port', type=int)
    parser.add_argument('-r', '--req_size', default='4', help='Number of requests to send.', type=int)
    parser.add_argument('-i', '--interval', default='0', help='Interval between requests (milliseconds).', type=int)
    parser.add_argument('-l', '--loops', default='5', help='Number of loops', type=int)

    args_map = {}
    for argname, argval in parser.parse_args()._get_kwargs():
        args_map.update({argname:str(argval)})

    return args_map


def build_api_url(args_map):
    api_url = 'http://' + args_map['host'] + ':' + args_map['port'] + '/' + \
        'simulation/' + args_map['req_size']

    return api_url


def send_request(url, args_map):
    print('Sending request to:', url)

    interval = int(args_map['interval']) / 1000
    loops = int(args_map['loops'])

    for i in range(loops):
        req = requests.get(url)
        print(req.json())
        time.sleep(interval)


if __name__ == '__main__':
    args_map = do_parse_args()
    api_url = build_api_url(args_map)
    send_request(api_url, args_map)
