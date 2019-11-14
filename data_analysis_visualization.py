import pandas as pd
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Using internal project modules


def pairwise_correlation(df):
    """
    This function plots the pairwise correlation
    between attributes of the data frame.
    :param df: the data frame to plot
    :return: None
    """
    f = plt.figure(figsize=(19, 15))
    plt.matshow(df.corr(), fignum=f.number)

    plt.xticks(range(df.shape[1]), df.columns, fontsize=7, rotation=45)
    plt.yticks(range(df.shape[1]), df.columns, fontsize=7)

    cb = plt.colorbar()
    cb.ax.tick_params(labelsize=7)

    plt.title('Correlation Matrix', fontsize=10)
    plt.show()


def cumulative_variance_plot(array_cum):
    """
    Plot the cumulative variance by PCA components
    :param array_cum: an array of floats with the cumulative variances
    :return: None
    """
    f, ax = plt.subplots()
    ax.plot(range(len(list(array_cum))), array_cum, '--bo', label='PCA explained variance per column')
    leg = ax.legend()
    plt.minorticks_on()
    plt.grid(b=True, which='major', linestyle='-')
    plt.grid(b=True, which='minor', linestyle=':')
    plt.show()


def clustering_inertia(array_inertia):
    """
    Plot the inertia with respect to the clusters number.
    :param array_inertia: an array of floats with the inertia. The index is the number of clusters
    :return: None
    """
    f, ax = plt.subplots()
    ax.plot(range(2, len(list(array_inertia))+2), array_inertia, '--bo', label='Clustering inertia per number of clusters')
    leg = ax.legend()
    plt.minorticks_on()
    plt.grid(b=True, which='major', linestyle='-')
    plt.grid(b=True, which='minor', linestyle=':')
    plt.show()