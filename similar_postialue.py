import pandas as pd
from pathlib import Path
from sklearn import preprocessing
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from cumulative_variance_plot import cumulative_variance_plot


def open():
    """
    Open the dataframe and return it.
    :return: the dataframe
    """
    # Open sample
    df = pd.read_csv(Path("dataframes/") / 'df2016.tsv', sep='\t', skiprows=0, encoding='utf-8',
                     dtype={'Postal code': object})

    df.fillna(0, inplace=True)
    # print(df.isnull().sum(axis=0))
    # print(df.describe())
    # print(df.shape)
    # print(df.columns)
    # print(df.dtypes)
    return df


def find_neighbor_of(placename):
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
    # print(array_cum)
    # cumulative_variance_plot(array_cum)
    pca_df = pd.DataFrame(index=df.index)
    new_col = ['Postal code', 'Area']
    # Copy old columns (left out from PCA)
    for c in new_col:
        pca_df[c] = df[c]

    # Taking the fist 30 PCs
    for i in range(30):
        pca_df['pca_' + str(i + 1)] = X_pca.T[i]
    neigh = NearestNeighbors(algorithm='auto')
    b = neigh.fit(df[df.columns[2:15]])
    A = neigh.radius_neighbors_graph(df[df.columns[2:15]])

    out = pd.DataFrame.sparse.from_spmatrix(A, index=pca_df['Area'], columns=pca_df['Area'])

    row = pca_df.loc[pca_df['Area'].str.contains(placename)]
    print(row['Area'])
    row = row[pca_df.columns[2:15]].values
    # print(row)
    dist, ind = neigh.kneighbors(row, n_neighbors=14)
    print(dist)
    for i in ind:
        print(pca_df.loc[i]['Area'])


if __name__ == '__main__':
    find_neighbor_of('Töölö')