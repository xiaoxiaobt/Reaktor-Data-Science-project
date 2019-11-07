import matplotlib.pyplot as plt


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