#!/usr/bin/env python3

import matplotlib.pyplot as plt
import pandas as pd

dataset = pd.read_csv('/home/madophs/Documents/git/autoescalado/src/datasets/data_latest.csv')

def plot_series(time, traffic):
    plt.figure(figsize=(10,5))
    plt.plot(time, traffic)
    plt.xlabel('Tiempo')
    plt.ylabel('Tráfico')
    plt.grid(True)
    plt.show()

def plot_cpu(time, traffic):
    plt.figure(figsize=(10,5))
    plt.plot(time, traffic)
    plt.xlabel('Tiempo')
    plt.ylabel('Tráfico')
    plt.grid(True)
    plt.show()

time = dataset.iloc[:,0]
traffic = dataset.iloc[:,1]

plot_series(time, traffic)
