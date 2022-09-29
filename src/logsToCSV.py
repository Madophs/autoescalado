#!/usr/bin/env python3

import json
import os
import time
import subprocess
import array

REAL_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(REAL_PATH)
LOG_DIR = DIR_PATH + '/logs'
DATASET_DIR = DIR_PATH + '/datasets'

class Record:
    def __init__(self,json_data):
        self.m_data = json_data
        self.m_accumulative_fields = ['request_size', 'exec_time']


    def mergeResults(self, json_data):
        for accum_field in self.m_accumulative_fields:
            self.m_data[accum_field] = float(json_data[accum_field]) + float(self.m_data[accum_field])


    def joinHeaders(self) -> str:
        return (','.join([str(key) for key in self.m_data])) + '\n'


    def joinValues(self) -> str:
        return (','.join([str(self.m_data[key]) for key in self.m_data])) + '\n'

def backupPrevDataset():
    timestamp = str(int(time.time()))
    prev = DATASET_DIR + '/data_latest.csv'
    target = DATASET_DIR + '/data_' + timestamp + '.csv'
    if os.path.isfile(prev):
        backup_cmd = 'mv ' + DATASET_DIR + '/data_latest.csv ' + DATASET_DIR + '/data_' + timestamp + '.csv &> /dev/null'
        p = subprocess.Popen(['mv', prev, target], stdin=subprocess.PIPE)
        p.wait()



def exportLogsToCSV():
    output_filename = DATASET_DIR + '/data_latest.csv'
    output = open(output_filename, 'w')
    logs_files = os.listdir(LOG_DIR)
    unique_records = dict()
    timestamps_arr = array.array('i', [])

    for log_name in logs_files:
        full_log_path = LOG_DIR + '/' + log_name
        if os.path.isdir(full_log_path):
            continue

        logs = open(full_log_path, 'r')
        lines = logs.readlines()

        # Add all records into a hash
        for line in lines:
            if not line.startswith('{'):
                continue

            json_log = json.loads(line)
            timestamp = int(json_log['timestamp'])

            if not timestamp in unique_records:
                unique_records[timestamp] = Record(json_log)
                timestamps_arr.append(timestamp)
            else:
                unique_records[timestamp].mergeResults(json_log)

        logs.close()

    # Unify all logs into a single dataset by timestamp
    first_record = True
    for timestamp in sorted(timestamps_arr):
        record = unique_records[timestamp]
        if first_record == True:
            output.writelines(record.joinHeaders())
            first_record = False
        output.writelines(record.joinValues())
    output.close()


backupPrevDataset()
exportLogsToCSV()
