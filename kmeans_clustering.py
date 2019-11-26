import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn import preprocessing
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score
from sklearn.metrics import silhouette_score

# Using internal project modules
from data_analysis_visualization import cumulative_variance_plot, clustering_inertia


def dataframe():
    """
    Open the data frame and return it.
    :return: the data frame
    """
    # Open sample
    df = pd.read_csv(Path("dataframes/") / 'final_dataframe.tsv', sep='\t', skiprows=0, encoding='utf-8',
                     dtype={'Postal code': object})

    # Correctly assign data types
    column_dic = dict.fromkeys(df.columns)
    for key in column_dic.keys():
        if key == 'Postal code' or key == 'Area' or key == 'text':
            column_dic[key] = 'object'
        else:
            column_dic[key] = 'float'
    df = df.astype(column_dic)

    if sum(df.isna().sum(axis=0)) > 0:
        print("WARNING: There are still missing values. They will be replaced with 0.")
        print(df.isna().sum(axis=0)[df.isna().sum(axis=0) > 0])
        df.fillna(0, inplace=True)
    return df


def k_means_clustering(automaticClusterNum=False):
    """
    Perform K-Means clustering on the scaled final data frame,
    and saves the column 'label' with the cluster id.
    :param automaticClusterNum: bool, if True calls 'choose_cluster_num' to find
            an optimal number of clusters; if False, uses an hard-coded value
            as the number of clusters
    :return: a tuple, where the fist element is the PCA scaled data frame, and the second
            element the scaled final data frame. Both the data frame have the new column 'label'
    """
    # Open the final data frame
    df = dataframe()

    # Exclude columns representing string values from PCA
    columns = list(set(df.columns) - {'Postal code', 'Area', 'text', 'Radius', 'lat', 'lon'})

    # Standard scale and PCA
    X_train = df[columns]
    X_scaled = preprocessing.scale(X_train)
    pca = PCA()
    X_pca = pca.fit_transform(X_scaled)

    # Plot cumulative explained variance by PCA component
    array_var = pca.explained_variance_ratio_
    array_cum = array_var.cumsum()
    cumulative_variance_plot(array_cum)

    # Save PCA in a new data frame
    pca_df = pd.DataFrame(index=df.index)
    new_col = ['Postal code', 'Area', 'text']

    # Copy old columns (left out from PCA)
    for c in new_col:
        pca_df[c] = df[c]

    # Taking as many PCs as needed to reach at least 0.995 variance coverage
    var_index = np.where(array_cum > 0.995)[0][0]
    print("Taking " + str(var_index) + " components.")
    for i in range(var_index):
        pca_df['pca_' + str(i + 1)] = X_pca.T[i]

    # Number of clusters
    if automaticClusterNum:
        i = choose_cluster_num(pca_df)
    else:
        i = 60

    # Perform clustering
    kmeans = KMeans(n_clusters=i)
    kmeans.fit(pca_df[pca_df.columns[3:var_index+3]])
    labels = kmeans.labels_

    print("Clustering with " + str(i) + " clusters converged in " + str(kmeans.n_iter_) + " iterations.")

    # Adding the column with cluster label
    pca_df['label'] = labels
    df['label'] = labels

    return pca_df, df


def clusters_dictionary():
    """
    Read the column 'label' from final_dataframe.tsv' and return the clusters as a dictionary.
    If the column 'label' is not in final_dataframe.tsv', call k_means_clustering and perform
    the clustering.
    :return: a dictionary, where the key is the cluster id and the value is a list of Areas
    """
    # Open sample
    df = pd.read_csv(Path("dataframes/") / 'final_dataframe.tsv', sep='\t', skiprows=0, encoding='utf-8',
                     dtype={'Postal code': object})
    if 'label' not in df.columns:
        _, df = k_means_clustering()
    cluster_dic = {}

    for i in list(set(df['label'].to_list())):
        cluster_dic[i] = df[df.label == i][['Postal code', 'Area']].values
    return cluster_dic


def choose_cluster_num(df=None, start_point=2, end_point=70, rtype='bouldin', plot_inertia=True):
    """
    Finds the optimal number of clusters to use for the K-Mean or .
    :param df: Data to be clustered. Optional. Default: the final dataf frame returned by 'dataframe()'
    :param start_point: The minimum number of clusters to test. Minimum value is 2.
    :param end_point: The maximum number of clusters to test. Maximum value should be less than 3026.
    :param rtype: Metrics to be used, 'bouldin' for Davies Bouldin score, 'silhouette' for Silhouette score.
    :param plot_inertia: bool, if True shows the curve of inertia
    :return: Optimal number of clusters.
    """
    # Get the data
    if df is None:
        df = dataframe()

    # Prepare empty arrays to save the results
    # Davies Bouldin
    resultd = []
    # Silhouette
    results = []
    # Inertia
    inertia = []

    # Create an array with possible numbers of clusters
    k_num = range(start_point, end_point + 1)

    # Exclude columns representing string values from PCA
    columns = list(set(df.columns) - {'Postal code', 'Area', 'text', 'Radius', 'lat', 'lon'})

    # Standard scale and PCA
    X_train = df[columns]
    X_scaled = preprocessing.scale(X_train)
    pca = PCA()
    X_pca = pca.fit_transform(X_scaled)

    for i in k_num:
        kmeans = KMeans(n_clusters=i)
        kmeans.fit(X_pca)
        labels = kmeans.labels_

        # Calculate Davies Bouldin score
        score_d = davies_bouldin_score(X_pca, labels)
        # Calculate Silhouette score
        score_s = silhouette_score(X_pca, labels)
        print(f'With {i} clusters, Davies Bouldin score is {score_d}, Silhouette score is {score_s}')
        # Save the results
        resultd.append(score_d)
        results.append(score_s)
        inertia.append(kmeans.inertia_)

    if plot_inertia:
        # Plot inertia
        clustering_inertia(inertia)

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
    _, df = k_means_clustering()
    filename = 'final_dataframe.tsv'
    df.to_csv(Path('dataframes/') / filename, sep='\t', index=False, encoding='utf-8')
    # choose_cluster_num()
    # print(clusters_dictionary())