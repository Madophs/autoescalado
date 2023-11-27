#!/usr/bin/env python3

import matplotlib.pyplot as plt
import pandas as pd

class Metric:
    def __init__(self, replicas:int):
        self.m_replicas = replicas
        self.m_traffic = []
        self.m_cpu_usage = []


    def getReplicas(self) -> int:
        return self.m_replicas


class ReplicasMetrics:
    def __init__(self):
        self.m_replicas_metrics = dict()

dataset = pd.read_csv('/home/madophs/Documents/git/autoescalado/src/datasets/data_latest.csv')
# dataset = pd.read_csv('/home/madophs/Documents/git/autoescalado/src/datasets/data_1664422132.csv')

def plot_series(time, traffic):
    plt.figure(figsize=(10,5))
    plt.plot(time, traffic)
    plt.xlabel('Tiempo')
    plt.ylabel('Tráfico')
    plt.grid(True)
    plt.show()

def plot_cpu(traffic, cpu_usage):
    plt.figure(figsize=(10,5))
    # plt.plot(cpu_usage, traffic)
    plt.scatter(traffic, cpu_usage)
    plt.xlabel('Tiempo')
    plt.ylabel('Tráfico')
    plt.grid(True)
    plt.show()

time = dataset.iloc[:,0]
traffic = dataset.iloc[:,1]
cpu_usage = dataset.iloc[:,5]

for i in range(len(dataset)):
    request_size = dataset.iloc[i,1]
    cpu = dataset.iloc[i, 5]
    replicas = dataset.iloc[i,7]
    print(request_size, cpu, replicas)

# plot_series(time, cpu_usage)
# plot_cpu(traffic, cpu_usage)
