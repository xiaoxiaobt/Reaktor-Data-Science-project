import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn import preprocessing
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score
from sklearn.metrics import silhouette_score
from cumulative_variance_plot import cumulative_variance_plot


def open():
    """
    Open the dataframe and return it.
    :return: the dataframe
    """
    # Open sample
    df = pd.read_csv(Path("dataframes/") / 'df2016.tsv', sep='\t', skiprows=0, encoding='utf-8',
                     dtype={'Postal code': object})
    print(df[df.columns[:5]].head())

    # Correctly assign datatypes
    column_dic = dict.fromkeys(df.columns)
    for key in column_dic.keys():
        if key == 'Postal code' or key == 'Area':
            print(key)
            column_dic[key] = 'object'
        else:
            print(key)
            column_dic[key] = 'float'
    df = df.astype(column_dic)

    df.fillna(0, inplace=True)
    print(df.isnull().sum(axis=0))
    print(df.describe())
    print(df.shape)
    print(df.columns)
    print(df.dtypes)
    return df


def k_means_clustering(automaticClusterNum=False):
    df = open()
    columns = list(set(df.columns) - set(['Postal code', 'Area']))
    X_train = df[columns]
    X_scaled = preprocessing.scale(X_train)
    # print(X_scaled)
    pca = PCA()
    X_pca = pca.fit_transform(X_scaled)
    # print(pca.explained_variance_ratio_)
    array_var = pca.explained_variance_ratio_
    array_cum = array_var.cumsum()
    print(array_cum)
    cumulative_variance_plot(array_cum)
    pca_df = pd.DataFrame(index=df.index)
    new_col = ['Postal code', 'Area']
    # Copy old columns (left out from PCA)
    for c in new_col:
        pca_df[c] = df[c]

    # Taking the fist 30 PCs
    for i in range(30):
        pca_df['pca_' + str(i + 1)] = X_pca.T[i]

    # print(pca_df)
    if automaticClusterNum:
        i = choose_cluster_num(pca_df)
    else:
        i = 71

    kmeans = KMeans(n_clusters=71)
    kmeans.fit(pca_df[pca_df.columns[2:15]])
    labels = kmeans.labels_

    # print(kmeans.cluster_centers_)
    print(kmeans.inertia_)
    print(kmeans.n_iter_)

    pca_df['label'] = labels

    return pca_df


def get_clusters():
    pca_df = k_means_clustering()
    cluster_dic = {}
    for i in list(set(pca_df['label'].to_list())):
        cluster_dic[i] = pca_df[pca_df.label == i]['Area'].values
    return cluster_dic


def choose_cluster_num(df=None, start_point=10, end_point=200, rtype='bouldin'):
    """
    Finds the optimal number of clusters to use for the Kmean or Agglomerative clustering.
    :param df: Data to be clustered. Optional.
    :param start_point: The minimum number of clusters to test. Minimum value is 2.
    :param end_point: The maximum number of clusters to test.
    :param rtype: Metrics to be used, 'bouldin' for Davies Bouldin score, 'silhouette' for Silhouette score.
    :return: Optimal number of clusters.
    """
    # Prepare empty arrays to save the results
    resultd = []
    results = []

    # Create an array with possible numbers of clusters
    k_num = range(start_point, end_point + 1)

    # Loop through the possible numbers of clusters
    for i in k_num:
        kmeans = KMeans(n_clusters=i)
        kmeans.fit(df[df.columns[2:15]])
        labels = kmeans.labels_

        # Calculate Davies Bouldin score
        score_d = davies_bouldin_score(df[df.columns[4:]], labels)
        # Calculate Silhouette score
        score_s = silhouette_score(df[df.columns[4:]], labels)
        print(f'With {i} clusters, Davies Bouldin score is {score_d}, Silhouette score is {score_s}')
        # Save the results
        resultd.append(score_d)
        results.append(score_s)

    # Plot the results
    plt.figure(figsize=(12, 6))
    plt.plot(k_num, results, color='red', linestyle='dashed', marker='o',
             markerfacecolor='blue', markersize=10, label='Silhouette score')
    plt.plot(k_num, resultd, color='green', linestyle='dashed', marker='o',
             markerfacecolor='orange', markersize=10, label='Davies Bouldin score')
    plt.legend()
    plt.show()

    # Choose the metrics to return
    if rtype == 'bouldin':
        return k_num[resultd.index(min(resultd))]
    else:
        return k_num[results.index(max(results))]


if __name__ == '__main__':
    print(get_clusters())