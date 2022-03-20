import pandas as pd
import numpy as np
from pathlib import Path

# Using internal project modules
from scripts.fetching.asuntojen_hintatiedot import list_sold, list_rent
from scripts.modeling.coordinates import coordinates
from scripts.modeling.yearly_dataframes import get_all_dataframes


def all_data():
    """
    This is the main function. It uses the data frame 2017 with original columns and
    scaled columns, augmented with columns that are not in 2017 but are in 2016, and
    also columns from external sources (paavo housing, asuntojen hintatiedot, bus stops,
    latitude and longitude, radius, forest data, water data). The column 'text'
    with the description shown when hovering is also added here.
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
    # df['Bus stops'] = add_buses()
    bus_stops, metro, train, ferry, tram, bus = add_all_transportation()
    df['Bus stops'] = bus_stops
    df['Metro'] = metro
    df['Train'] = train
    df['Ferry'] = ferry
    df['Tram'] = tram
    df['Bus'] = bus

    # Add avg selling prices in the last 12 months
    df['Sell price'] = [0] * len(df.index)
    df.update(sold_df)

    # Add avg renting prices with ARA in the last 12 months
    df['Rent price with ARA'] = [0] * len(df.index)
    df.update(rentARA_df)

    # Add avg renting prices without ARA in the last 12 months
    df['Rent price without ARA'] = [0] * len(df.index)
    df.update(rentnoAra_df)

    # Add Paavo Housing prices and trends
    df = add_paavo_housing(df)

    # Add forest data
    df['Forest'] = add_forest()

    # Add water data
    df = add_water(df)

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
    bus_df = pd.read_csv(Path('data/transportation/') / 'bus.tsv', sep='\t', usecols=['Bus stops'])
    return bus_df['Bus stops'].copy()


def add_all_transportation():
    """
    Open the file 'final_transportation.tsv' from the folder 'data/transportation' and return the column
    to add to the data frame
    :return: list of values as a pandas Series
    """
    print("Loading public transportation...")
    pt_df = pd.read_csv(Path('data/transportation/') / 'final_transportation.tsv', sep='\t',
                        dtype={'Postal code': object}, index_col="Postal code")
    # The column "Bus stops" is the sum of all public transportation
    pt_df['Bus stops'] = pt_df.sum(axis=1)
    pt_df = pt_df.sort_values(by=['Postal code']).reset_index()
    # print(pt_df)
    return pt_df['Bus stops'].copy(), \
           pt_df['Metro'].copy(), pt_df['Train'].copy(), pt_df['Ferry'].copy(), pt_df['Tram'].copy(), pt_df['Bus'].copy()


def add_forest():
    """
    Open the file 'forest.csv' from the folder 'data' and return the column to add to the data frame
    :return: list of values as a pandas Series
    """
    print("Loading forest data...")
    f_df = pd.read_csv(Path('data/environment/') / 'forest.csv', sep=',', usecols=['forest_average'])
    return f_df['forest_average'].copy()


def add_water(df):
    """
    Open the file 'water.csv' from the folder 'data' and add the information to the data frame
    :param df: the data frame where to add the columns
    :return: the updated data frame
    """
    print("Loading water data...")
    w_df = pd.read_csv(Path('data/environment/') / 'water.csv', sep=',', usecols=['water_average_with_sea',
                                                                           'water_average_without_sea'])
    df['Water'] = 100*w_df['water_average_with_sea'].copy()
    diff = w_df['water_average_with_sea'] - w_df['water_average_without_sea']
    mask = (diff.values > 0)
    df['Boolean sea'] = mask.astype(int)
    return df


def add_paavo_housing(df):
    """
    Read the file 'paavo_housing_quartetly_prediction.tsv' from the folder 'data/paavo'
    and add 2020Q1 price prediction, trend from 2018 and trend for 2020Q2
    :param df: the data frame where to add the columns
    :return: the updated data frame
    """
    print("Loading 2020Q1 price prediction...")
    temp = pd.read_csv(Path('data/paavo/') / 'paavo_housing_quarterly_prediction.tsv', sep='\t',
                       dtype={'2018Q4': float, '2018Q3': float, '2018Q2': float, '2018Q1': float,
                              '2020Q1': float, '2020Q2': float})
    # Add Paavo prediction for 2020Q1
    df.update(temp['2020Q1'])

    avg_2018 = (temp[['2018Q4', '2018Q3', '2018Q2', '2018Q1']].mean(axis=1))
    long_trend = (temp['2020Q2'] - avg_2018) / avg_2018
    near_future_trend = (temp['2020Q2'] - temp['2020Q1']) / temp['2020Q1']

    # Add Paavo Housing trend
    df['Trend from 2018'] = long_trend
    df['Trend near future'] = near_future_trend
    return df


def add_peculiarity(df):
    """
    Add the column 'peculiarity' with a sentence describing some
    particular characteristic of the postalcode area.
    :return: the updated data frame
    """
    list = []
    # See notes
    for i, row in df.iterrows():
        list.append(str(row['Area']))
    df['interesting'] = list
    return df


def add_radius():
    """
    Open the file 'radius.csv' from the folder 'data' and return the column to add to the data frame
    :return: list of values as a pandas Series
    """
    print("Loading radius...")
    r_df = pd.read_csv(Path('data/geographic/') / 'radius.csv', sep='\t', dtype={'posti_alue': object, 'Radius': float})
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
    for _, row in df.iterrows():
        list.append('<b>' + str(row['Area']) + '</b><br>' +
                    "Density: " + str(row['Density']) + '<br>' +
                    "Average age: " + str(row['Average age of inhabitants']) + '<br>' +
                    "Median income: " + str(row['Median income of inhabitants']) + '<br>' +
                    "Employment rate: " + str(row['Employment rate %']) + '<br>')
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

