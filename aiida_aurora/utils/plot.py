import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

def create_figure(title=None):
    fig, axx = plt.subplots(1, figsize=(9, 4))
    plt.subplots_adjust(left=0.1, right=0.95, bottom=0.15, top=0.9)
    if title:
        fig.suptitle(title)
    return fig, axx

def plot_Ewe(data):
    fig, axx = create_figure()
    axx.plot(data["time"] / 3600., data["Ewe"], label='Ewe')
    axx.set_xlabel('t [h]')
    axx.set_ylabel('Ewe [V]')

def plot_I(data):
    fig, axx = create_figure()
    axx.plot(data["time"] / 3600., data["I"] * 1000., label='I')
    axx.set_xlabel('t [h]')
    axx.set_ylabel('I [mA]')
    return fig

def plot_Ewe_I(data):
    fig, axx = create_figure()
    axx.plot(data["time"] / 3600., data["Ewe"], label='Ewe')
    axx.set_xlabel('t [h]')
    axx.set_ylabel('Ewe [V]', c='b')

    ax2 = axx.twinx()
    ax2.plot(data["time"] / 3600, data["I"] * 1000., 'r--', label='I')
    ax2.set_ylabel('I [mA]', c='r')

def plot_Qd(data, ytick=0.05):
    fig, axx = create_figure()
    axx.plot(range(1, len(data['Qd']) + 1), data['Qd'] / 3.6, '.-', label='Qd')
    axx.set_xlabel('cycle')
    axx.set_ylabel('Qd [mAh]')
    axx.axhline(data['Qd'][0] * 0.8 / 3.6, ls='--', c='r')
    axx.set_xlim([0, None])
