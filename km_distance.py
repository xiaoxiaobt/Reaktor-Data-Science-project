import pandas as pd
import geopy.distance
from pathlib import Path


def get_distance(df, postalcode='00100'):
    """
    :param df: the data frame
    :param postalcode: string, the postal code with respect to which the distance is computed
    :return: the data frame, with a new column named 'Distance' that stores the geographical distance
            in km between 'postalcode' and each postal code in the data frame
    """

    target = df[df['Postal code'] == postalcode][['Lat', 'Lon']].values[0]

    df['Distance'] = [0] * len(df.index)
    for i, row in df.iterrows():
        pc = row['Postal code']
        lat = row['Lat']
        lon = row['Lon']
        coord = (lat, lon)
        dist = geopy.distance.distance(coord, target).km
        df.at[i, 'Distance'] = dist

    return df


if __name__ == '__main__':
    df = pd.read_csv(Path("dataframes/") / 'final_dataframe.tsv', sep='\t', skiprows=0, encoding='utf-8',
                     dtype={'Postal code': object})
    df = get_distance(df)
    print(df['Distance'])
