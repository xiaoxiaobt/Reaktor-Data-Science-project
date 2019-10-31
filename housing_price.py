# -*- coding: utf-8 -*- #

import requests
import pandas as pd
from tabulate import tabulate
from bs4 import BeautifulSoup
import os
import glob
import re
from pathlib import Path
import time

#TODO: for sales, compute average price/m^2 for each postcode, save it in pandas.Series
#TODO: for rents, compute average price/m^2 with and without ARA for each postcode, save it in 2 pandas.Series

# Sales in the last 12 months
sales_url = u'https://asuntojen.hintatiedot.fi/haku/?search=1&l=0&c=&cr=1&ps='
end_sales = '&pc=0&nc=0&amin=&amax='

# Rents with yleinen asumistuki
rent_url = u'https://asuntojen.hintatiedot.fi/haku/vuokratiedot?c=&ps='
end_rent = '&renderType=renderTypeTable'

# Postal codes list
to_open = Path("dataframes/") / 'df2017.tsv'
pc_list = [c[:5] for c in pd.read_csv(to_open, sep='\t', encoding='utf-8')['Postal code'].values]


def get_query(ps='00100', onSale=True):
    """
    Perform the query on one postal code.
    QUERY TESTED: 30.10.2019
    :param ps: the postal code to query.
    :param onSale: bool, if true do the query sales, if false do the query on rents
    :return: a dataframe
    """
    ps = re.sub('[^0-9]+', '', ps)[:5]
    df_list = [pd.DataFrame()]
    try:
        if onSale:
            res = requests.get(sales_url + ps + end_sales)
        else:
            res = requests.get(rent_url + ps + end_rent)
        soup = BeautifulSoup(res.content,'lxml')
        soup = soup.find("table", {"id": "mainTable"})
        if soup is not None:
            df_list = pd.read_html(str(soup))
            print(tabulate(df_list[0], headers='keys', tablefmt='psql'))
    except requests.ConnectionError as e:
        print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
        print(str(e))
        time.sleep(5)
        get_query(ps=ps, onSale=onSale)
    except requests.Timeout as e:
        print("OOPS!! Timeout Error")
        print(str(e))
        time.sleep(5)
        get_query(ps=ps, onSale=onSale)
    except requests.RequestException as e:
        print("OOPS!! General Error")
        print(str(e))
        time.sleep(5)
        get_query(ps=ps, onSale=onSale)
    except KeyboardInterrupt:
        print("Someone closed the program")
    return df_list[0]


def collect_query(onSale=True, pc_list=pc_list):
    """
    Call get_query on all the known postal codes
    and saves a .tsv file for each postal code.
    :param: onSales, bool, if true collect the query on sales, if false do it on rents
    :return: None
    """
    filename = 'sale' if onSale else 'rent'
    housing_folder = 'housing_' + filename
    if not os.path.exists(housing_folder):
        os.makedirs(housing_folder)

    for pc in pc_list:
        df = get_query(ps=pc, onSale=onSale)
        file = str(pc) + '.tsv'
        df.to_csv(os.path.join(housing_folder, file), sep='\t', index=False, encoding='utf-8')
    return None


def clean_sale(df):
    """
    Clean the dataframe from the sales query.
    :param df: the dataframe with data from sales
    :return: the cleaned dataframe
    """
    # Clean the columns list and reassign it
    col = [re.sub('[^\w]', '', c) for c in df.columns]
    df.columns = col

    # The following sentence indicates that there is no information for that postal code
    empty_flag = 'Tuloksia on vähemmän kuin kolme, joten tuloksia ei näytetä.'

    # Collect indexes to drop
    to_drop = df[df.Kaupunginosa == empty_flag].index.tolist()
    to_drop += df[df.Kaupunginosa == 1].index.tolist()
    to_drop += df[df.Kaupunginosa == '1'].index.tolist()
    to_drop += df[df.Kaupunginosa == 'Yksiö'].index.tolist()
    to_drop += df[df.Kaupunginosa == 'Kaksi huonetta'].index.tolist()
    to_drop += df[df.Kaupunginosa.isnull()].index.tolist()

    # Drop the indexes in the list
    df.drop(to_drop, axis=0, inplace=True)

    # Reset the index
    df.reset_index(drop=True, inplace=True)
    return df


def clean_rent(df):
    """
    Clean the dataframe from the sales query.
    :param df: the dataframe with data from sales
    :return: the cleaned dataframe
    """
    # Reassign column names
    col = ['Unnamed', 'Keskivuokra ARA-vuokra', 'Keskivuokra Vapaarah. vanhat', 'Keskivuokra Vapaarah. uudet',
           'Kuukausivuokra ARA-vuokra', 'Kuukausivuokra Vapaarah. vanhat', 'Kuukausivuokra Vapaarah. uudet']
    df.columns = col

    # Collect indexes to drop
    to_drop = [0, 1]

    # Drop the indexes in the list
    if len(df) > len(to_drop):
        df.drop(to_drop, axis=0, inplace=True)

    # Reset the index
    df.reset_index(drop=True, inplace=True)
    return df


def clean(onSale=True):
    """
    Read all the files collected from asuntojen hintatiedot into dataframes,
    clean the dataframes.
    :param: onSales, bool, if true clean the sales, if false clean the rents
    :return: dictionary of dataframes, where the key is the postal code
    """
    filename = 'sale' if onSale else 'rent'
    housing_folder = 'housing_' + filename
    # Read all the files
    file_list = glob.glob(housing_folder + '/*.tsv')
    while len(file_list) == 0:
        print('Folder not found!\n Doing the webscraping...')
        collect_query(onSale=onSale)
        file_list = glob.glob(housing_folder + '/*.tsv')

    # Extract back the postal codes
    codes = sorted({(re.sub('[^0-9]+', '', y))[:5] for y in file_list})

    if len(file_list) < len(pc_list):
        print('Folder has incomplete data!\n Doing the webscraping on missing values...')
        missing = list(set(pc_list) - set(codes))
        print(missing)
        collect_query(onSale=onSale, pc_list=missing)

    # Build a dictionary of DataFrames:
    # to each postal code, it is associated one DataFrame
    df_dic = {y: pd.DataFrame() for y in codes}

    # Fill one DataFrame per postalcode
    for file in file_list:
        for code in codes:
            if code in file:
                try:
                    # Read the file
                    df_dic[code] = pd.read_csv(file, sep='\t', skiprows=0)
                except:
                    collect_query(onSale=onSale, pc_list=[code])
                    df_dic[code] = pd.read_csv(file, sep='\t', skiprows=0)
                if onSale:
                    df_dic[code] = clean_sale(df_dic[code])
                else:
                    df_dic[code] = clean_rent(df_dic[code])

                # Save dataframe to file
                print('Postalcode: ' + str(code))
                df_folder = 'dataframes_' + filename
                if not os.path.exists(df_folder):
                    os.makedirs(df_folder)
                df_dic[code].to_csv(Path(df_folder) / (str(code)[:5] + '.tsv'), sep='\t', index=False, encoding='iso-8859-1')

    return df_dic


if __name__ == '__main__':
    sales_dic = clean(onSale=True)
    rent_dic = clean(onSale=False)