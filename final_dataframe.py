import pandas as pd
import numpy as np
from pathlib import Path

# Using internal project modules
from asuntojen_hintatiedot import list_sold, list_rent
from coordinates import coordinates
from yearly_dataframes import get_all_dataframes


def all_data():
    """
    Data frame 2017 with original columns and scaled columns, augmented with columns
    that are not in 2017 but are in 2016, and also columns from external sources
    (paavo housing, asuntojen hintatiedot, bus stops, latitude and longitude)
    :return: the data frame
    """
    all_dfs, columns = get_all_dataframes()

    newest = all_dfs['2017'].copy()
    for c in all_dfs['2016'].columns:
        if c not in newest.columns:
            newest[c] = all_dfs['2016'][c]
    newest = add_scaled_columns_2017(newest)
    newest = add_scaled_columns_2016(newest)
    return add_newest_attributes(newest)


def add_newest_attributes(df):
    """
    Number of bus stops, average selling prices over the last 12 months,
    average rent with and without ARA over the last 12 months,
    population density, latitude and longitude coordinates, are added to each data frame.
    :return: the updated data frame
    """
    print("Loading sales...")
    sold_df = pd.DataFrame({'Sell price': list_sold()}, dtype=np.float64)
    print("Loading rents...")
    rentARA_df = pd.DataFrame({'Rent price with ARA': list_rent()[0]}, dtype=np.float64)
    rentnoAra_df = pd.DataFrame({'Rent price without ARA': list_rent()[1]}, dtype=np.float64)

    # Add bus stops
    df['Bus stops'] = add_buses()

    # Add avg selling prices in the last 12 months
    df['Sell price'] = [0] * len(df.index)
    df.update(sold_df)

    # Add avg renting prices with ARA in the last 12 months
    df['Rent price with ARA'] = [0] * len(df.index)
    df.update(rentARA_df)

    # Add avg renting prices without ARA in the last 12 months
    df['Rent price without ARA'] = [0] * len(df.index)
    df.update(rentnoAra_df)

    # Add Housing prices
    temp = pd.read_csv(Path('data/') / 'paavo_housing_data.tsv', sep='\t')
    df.update(temp['Housing price (2018)'])

    # Add surface area TODO
    h = pd.read_csv(Path('data/') / 'surface_area.tsv', sep='\t', usecols=['Postal code', 'Surface area (2017)'])

    # Add latitude and longitude
    coord = coordinates()
    lat = []
    lon = []
    for elm in coord:
        lon.append(elm[1][0])
        lat.append(elm[1][1])
    df['Lat'] = lat
    df['Lon'] = lon

    # Add radius
    df['Radius'] = add_radius()

    # Add text description
    df = add_hover_description(df)

    filename = 'final_dataframe.tsv'
    df.to_csv(Path('dataframes/') / filename, sep='\t', index=False, encoding='utf-8')
    return df


def add_buses():
    """
    Open the file 'bus.tsv' from the folder 'data' and return the column to add to the data frame
    :return: list of values as a pandas Series
    """
    print("Loading bus stops...")
    bus_df = pd.read_csv(Path('data/') / 'bus.tsv', sep='\t', usecols=['Bus stops'])
    return bus_df['Bus stops'].copy()


def add_peculiarity(df):
    """
    Add the column 'peculiarity' with a sentence describing some
    particular characteristic of the postalcode area.
    :return: the updated data frame
    """
    list = []
    # TODO: Build the list based on min and max values by column, but at most 1 info per postalcode
    # See notes
    for i, row in df.iterrows():
        list.append(str(row['Area']))
    df['text'] = list
    return df


def add_radius():
    """
    Open the file 'radius.csv' from the folder 'data' and return the column to add to the data frame
    :return: list of values as a pandas Series
    """
    print("Loading radius...")
    r_df = pd.read_csv(Path('data/') / 'radius.csv', sep='\t', dtype={'posti_alue': object, 'Radius': float})
    r_df.sort_values(by=['posti_alue'], inplace=True)
    r_df.reset_index(inplace=True)
    return r_df['Radius'].copy()


def add_hover_description(df):
    """
    Add the column 'text' with the numbers and description
    shown on the app when selecting one postalcode area.
    :return: the updated data frame
    """
    list = []
    for i, row in df.iterrows():
        list.append('<b>' + str(row['Area']) + '</b><br>' +
                    "Density: " + str(row['Density']) + '<br>' +
                    "Average age: " + str(row['Average age of inhabitants']) + '<br>' +
                    "Average income: " + str(row['Average income of inhabitants']) + '<br>')
    df['text'] = list

    return df


def add_scaled_columns_2017(df):
    """
    Add the scaled columns from the data frame 2017.
    :param df: the data frame where to add columns
    :return: the data frame with added columns
    """
    scaled = pd.read_csv('dataframes_scaled/df2017.tsv', sep='\t', dtype={'Postal code': object})
    for col in scaled.columns:
        if "scaled" in col:
            df[col] = scaled[col].copy()
    return df


def add_scaled_columns_2016(df):
    """
    Add the scaled columns from the data frame 2016 when data from 2017 are missing.
    :param df: the data frame where to add columns
    :return: the data frame with added columns
    """
    scaled = pd.read_csv('dataframes_scaled/df2016.tsv', sep='\t', dtype={'Postal code': object})
    for col in scaled.columns:
        if "scaled" in col and col not in df.columns:
            df[col] = scaled[col].copy()
    return df


if __name__ == '__main__':
    d = all_data()
    # print(d.head())
    # temp = pd.read_csv(Path('dataframes/') / 'final_dataframe.tsv', sep='\t', dtype={'Postal code': object})
    # print(temp.head())
    # print(temp[temp['Postal code'] == "02150"]['Sell price'].values[0])

