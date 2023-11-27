#!/usr/bin/env python3
import tensorflow as tf
print(tf.__version__)

import csv
time_step = []
temps = []

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def plot_series(time, series, format="-", start=0, end=None):
    plt.plot(time[start:end], series[start:end], format)
    plt.xlabel("Tiempo")
    plt.ylabel("Tráfico")
    plt.grid(True)

#csv_file = '/home/madophs/Documents/git/autoescalado/src/datasets/daily-min-temperatures.csv'
#split_time = 2500
csv_file = '/home/madophs/Documents/git/autoescalado/src/datasets/data_latest.csv'

from statsmodels.nonparametric.smoothers_lowess import lowess
df_orig  = pd.read_csv(csv_file, index_col='timestamp')
df_loess_5 = pd.DataFrame(lowess(df_orig.request_size, np.arange(len(df_orig.request_size)), frac=0.005)[:, 1], index=df_orig.index, columns=['request_size'])
df_loess_15 = pd.DataFrame(lowess(df_orig.request_size, np.arange(len(df_orig.request_size)), frac=0.15)[:, 1], index=df_orig.index, columns=['request_size'])

df_ma = df_orig.request_size.rolling(3, center=True, closed='both').mean()
# Plot
fig, axes = plt.subplots(4,1, figsize=(7, 7), sharex=True, dpi=120)
df_orig['request_size'].plot(ax=axes[0], color='k', title='Original Series')
df_loess_5['request_size'].plot(ax=axes[1], title='Loess Smoothed 0.05%')
df_loess_15['request_size'].plot(ax=axes[2], title='Loess Smoothed 15%')
df_ma.plot(ax=axes[3], title='Moving Average (3)')
fig.suptitle('Smoothen a Time Series', y=0.95, fontsize=14)
plt.show()

split_time = 3200
with open(csv_file) as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    next(reader)
    step=0
    for row in reader:
        temps.append(float(row[1]))
        time_step.append(step)
        step = step + 1

# time = np.array(time_step)
# plot_series(time, temps)
# plt.show()
# exit()
temps = df_loess_5['request_size']
# exit()
print(temps)
series = np.array(temps)
time = np.array(time_step)
plt.figure(figsize=(10, 6))
plot_series(time, series)
plt.show()
# exit()

## variables para la técnica de la ventana temporal
# split_time = 2500

print('series len:', len(series))
window_size = 30
batch_size = 32
shuffle_buffer_size = 1000

## Split del dataset en entrenamiento y validación

## tu código para la creación de las 4 variables del ejercicio 1 aquí
time_train = time[:split_time]
x_train = series[:split_time]

time_valid = time[split_time:]
x_valid = series[split_time:]

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[1:]))
    return ds.batch(batch_size).prefetch(1)


def model_forecast(model, series, window_size):
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size))
    ds = ds.batch(32).prefetch(1)
    forecast = model.predict(ds)
    return forecast


tf.keras.backend.clear_session()
tf.random.set_seed(51)
np.random.seed(51)
window_size = 64
batch_size = 256

train_set = windowed_dataset(x_train, window_size, batch_size, shuffle_buffer_size)

from keras.layers import Conv1D,LSTM,Dense

def create_model(conv_filters):
    model = tf.keras.Sequential()
    model.add(
        Conv1D(
            filters=conv_filters,
            kernel_size=5,
            strides=1,
            padding='causal',
            activation='relu',
            input_shape=(None, 1)
        )
    )

    model.add(
        LSTM(
            64,
            return_sequences=True,
        )
    )

    model.add(
        LSTM(
            64,
            return_sequences=True,
        )
    )

    model.add(
        Dense(32)
    )

    model.add(
        Dense(10)
    )

    model.add(
        Dense(1)
    )

    model.add(
        tf.keras.layers.Lambda(lambda x: x * 400)
    )
    return model

model = create_model(32)


def callbacks(epoch, lr):
    lr = 1e-8 * 10 ** (epoch/20)
    return lr

lr_schedule = tf.keras.callbacks.LearningRateScheduler(callbacks)

# model.compile(
    # loss='huber_loss',
    # optimizer=tf.keras.optimizers.SGD(learning_rate = 1e-8, momentum = 0.9),
    # metrics=['mean_absolute_error']
# )


# history = model.fit(train_set, epochs=100, callbacks=[lr_schedule])
# plt.semilogx(history.history["lr"], history.history["loss"])
# plt.axis([1e-8, 1e-4, 0, 1200])
# plt.show()
# exit()

tf.keras.backend.clear_session()
tf.random.set_seed(51)
np.random.seed(51)

train_set = windowed_dataset(x_train, window_size=64, batch_size=256, shuffle_buffer=shuffle_buffer_size)

model = create_model(64)

model.compile(
    loss='huber_loss',
    optimizer=tf.keras.optimizers.SGD(learning_rate = 1e-7, momentum = 0.97),
    metrics=['mean_absolute_error']
)

history = model.fit(train_set,epochs=300)

rnn_forecast = model_forecast(model, series[..., np.newaxis], window_size)
rnn_forecast = rnn_forecast[split_time - window_size:-1, -1, 0]
print(rnn_forecast)

plt.figure(figsize=(10, 10))
plot_series(time_valid, x_valid)
plot_series(time_valid, rnn_forecast)
plt.show()
