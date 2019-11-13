# Get data from asuntojen.hintatiedot.fi
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
import numpy as np

# Sales in the last 12 months
sales_url = u'https://asuntojen.hintatiedot.fi/haku/?search=1&l=0&c=&cr=1&ps='
end_sales = '&pc=0&nc=0&amin=&amax='

# Rents with yleinen asumistuki
rent_url = u'https://asuntojen.hintatiedot.fi/haku/vuokratiedot?c=&ps='
end_rent = '&renderType=renderTypeTable'

# Read postal codes list (saved from 2017)
to_open = Path("data/") / 'postalcodes.tsv'
pc_list = pd.read_csv(to_open, sep='\t', encoding='utf-8', dtype={'Postal code': object})['Postal code'].values

# Or generate postal codes list from 2017
# to_open = Path("dataframes/") / 'df2017.tsv'
# pc_list = pd.read_csv(to_open, sep='\t', encoding='utf-8', dtype={'Postal code': object})['Postal code'].values
# pd.DataFrame({'Postal code': pc_list}).to_csv(Path("data/") / 'postalcodes.tsv', index=False)


def get_one_postalcode(ps='00100', onSale=True):
    """
    Perform the query on one postal code.
    QUERY TESTED: 13.11.2019
    :param ps: the postal code to query.
    :param onSale: bool, if true do the query sales, if false do the query on rents
    :return: a data frame
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
        get_one_postalcode(ps=ps, onSale=onSale)
    except requests.Timeout as e:
        print("OOPS!! Timeout Error")
        print(str(e))
        time.sleep(5)
        get_one_postalcode(ps=ps, onSale=onSale)
    except requests.RequestException as e:
        print("OOPS!! General Error")
        print(str(e))
        time.sleep(5)
        get_one_postalcode(ps=ps, onSale=onSale)
    except KeyboardInterrupt:
        print("Someone closed the program")
    return df_list[0]


def all_queries_to_tsv(onSale=True, pc_list=pc_list):
    """
    Call get_one_postalcode on all the known postal codes and save a .tsv file for each postal code
    in the folder 'asuntojen_hintatiedot_sale' or asuntojen_hintatiedot_rent'.
    :param: onSales, bool, if true collect the query on sales, if false do it on rents
    :return: None
    """
    filename = 'sale' if onSale else 'rent'
    housing_folder = 'asuntojen_hintatiedot_' + filename
    if not os.path.exists(housing_folder):
        os.makedirs(housing_folder)

    for pc in pc_list:
        df = get_one_postalcode(ps=pc, onSale=onSale)
        file = str(pc) + '.tsv'
        df.to_csv(os.path.join(housing_folder, file), sep='\t', index=False, encoding='utf-8')
    return None


def clean_sale(df):
    """
    Clean the data frame from the sales query.
    :param df: the data frame with data from sales
    :return: the cleaned data frame
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
    to_drop += df[df.Kaupunginosa == 'Kolme huonetta'].index.tolist()
    to_drop += df[df.Kaupunginosa == 'Neljä huonetta tai enemmän'].index.tolist()
    to_drop += df[df.Kaupunginosa.isnull()].index.tolist()

    # Drop the indexes in the list
    df.drop(to_drop, axis=0, inplace=True)

    # Reset the index
    df.reset_index(drop=True, inplace=True)
    return df.copy()


def clean_rent(df):
    """
    Clean the data frame from the sales query.
    :param df: the data frame with data from sales
    :return: the cleaned data frame
    """
    # Reassign column names
    col = ['Unnamed', 'Keskivuokra ARA-vuokra', 'Keskivuokra Vapaarah. vanhat', 'Keskivuokra Vapaarah. uudet',
           'Kuukausivuokra ARA-vuokra', 'Kuukausivuokra Vapaarah. vanhat', 'Kuukausivuokra Vapaarah. uudet']
    df.columns = col

    # Collect indexes to drop
    to_keep = ['1h', '2h', '3h+', 'Kaikki', 'Lkm']
    to_drop = [0, 1]

    # Drop the indexes in the list
    if len(df) > len(to_drop):
        for i in to_drop:
            if df.loc[i]['Unnamed'] not in to_keep:
                df.drop(i, axis=0, inplace=True)

    # Reset the index
    df.reset_index(drop=True, inplace=True)
    return df.copy()


def clean(onSale=True, andSave=False):
    """
    Read all the files collected from asuntojen hintatiedot and saved in the folder 'asuntojen_hintatiedot_sale'
    or 'asuntojen_hintatiedot_rent' (missing files are downloaded by calling 'all_queries_to_tsv') into data frames,
    clean the data frames, and return a dictionary of data frames, where the postal code is the key.
    :param: onSales, bool, if true read and clean the sales, if false read and clean the rents
    :param: onSales, bool, if true save the data frames by overwriting the original .tsv files
            in the folder 'asuntojen_hintatiedot_sale' or 'asuntojen_hintatiedot_rent';
            if false only return the dictionary of data frames
    :return: dictionary of data frames, where the key is the postal code
    """
    filename = 'sale' if onSale else 'rent'
    housing_folder = 'asuntojen_hintatiedot_' + filename
    # Read all the files
    file_list = glob.glob(housing_folder + '/*.tsv')
    while len(file_list) == 0:
        print('Folder not found!\n Doing the webscraping...')
        all_queries_to_tsv(onSale=onSale)
        file_list = glob.glob(housing_folder + '/*.tsv')

    # Extract back the postal codes
    codes = sorted({(re.sub('[^0-9]+', '', y))[:5] for y in file_list})

    if len(file_list) < len(pc_list):
        print('Folder has incomplete data!\n Doing the webscraping on missing values...')
        missing = list(set(pc_list) - set(codes))
        print(missing)
        all_queries_to_tsv(onSale=onSale, pc_list=missing)

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
                    all_queries_to_tsv(onSale=onSale, pc_list=[code])
                    df_dic[code] = pd.read_csv(file, sep='\t', skiprows=0)
                if onSale:
                    df_dic[code] = clean_sale(df_dic[code])
                else:
                    df_dic[code] = clean_rent(df_dic[code])

                # Save dataframe to file
                if (andSave):
                    print('Save postalcode: ' + str(code))
                    df_folder = 'asuntojen_hintatiedot_' + filename
                    if not os.path.exists(df_folder):
                        os.makedirs(df_folder)
                    df_dic[code].to_csv(Path(df_folder) / (str(code)[:5] + '.tsv'), sep='\t', index=False, encoding='utf-8')

    return df_dic


def sold_avg(df):
    """
    Return the average prices per square meters
    :param df: a data frame where the 5th column is price per square meter
    :return: float, the average (or np.nan)
    """
    df = clean_sale(df)
    if df[df.columns[5]].empty:
        return np.nan
    else:
        return df[df.columns[5]].mean()


def list_sold(pc_list=pc_list):
    """
    Build the list of average selling prices per square meter, for each postal code
    :param pc_list: list of strings, where each string is a postal code
    :return: list of floats, with np.nan
    """
    avg_price_list = []
    for y in pc_list:
        filename = str(y)[:5] + '.tsv'
        df = pd.read_csv(Path('asuntojen_hintatiedot_sale') / filename, sep='\t', encoding='iso-8859-1')
        avg_price_list.append(sold_avg(df))
    return avg_price_list


def rent_avg(df, withARA=True):
    """
    Return the average prices per square meters for the rents
    :param df: a data frame where the 5th column is price per square meter
    :param withARA: compute the weighted mean including ARA houses
    :return: float, the average (or np.nan)
    """
    cols = ['Unnamed', 'Keskivuokra ARA-vuokra', 'Keskivuokra Vapaarah. vanhat', 'Keskivuokra Vapaarah. uudet']
    df = clean_rent(df)
    df.replace({'-': 0.0}, inplace=True)
    price = []
    lkm = []
    if df.empty:
        return np.nan
    else:
        df = df[df.columns[:4]]
        for i, row in df.iterrows():
            if row['Unnamed'] == 'Kaikki':
                price.append(float(row[cols[1]]))
                price.append(float(row[cols[2]]))
                price.append(float(row[cols[3]]))
            if row['Unnamed'] == 'Lkm':
                lkm.append(int(row[cols[1]]))
                lkm.append(int(row[cols[2]]))
                lkm.append(int(row[cols[3]]))
        if len(price) > 0 and len(price) == len(lkm):
            if withARA:
                mysum = sum([price[i]*lkm[i] for i in range(len(price))])
                if mysum != 0.0:
                    return mysum/sum(lkm)
                else:
                    return np.nan
            else:
                mysum = sum([price[i] * lkm[i] for i in range(1, len(price))])
                if mysum != 0.0:
                    return mysum / (sum(lkm)-lkm[0])
                else:
                    return np.nan


def list_rent(pc_list=pc_list):
    """
    Build the list of average selling prices per square meter, for each postal code
    :param pc_list: list of strings, where each string is a postal code
    :return: tuple of 2 lists of floats, with np.nan; the first list includes ARA,
            the second list does not include ARA
    """
    avg_ARA_price_list = []
    avg_noARA_price_list = []
    for y in pc_list:
        filename = str(y)[:5] + '.tsv'
        df = pd.read_csv(Path('asuntojen_hintatiedot_rent') / filename, sep='\t', encoding='iso-8859-1')
        avg_ARA_price_list.append(rent_avg(df, withARA=True))
        avg_noARA_price_list.append(rent_avg(df, withARA=False))
    return avg_ARA_price_list, avg_noARA_price_list


if __name__ == '__main__':
    sales_dic = clean(onSale=True, andSave=True)
    print(list_sold())
    rent_dic = clean(onSale=False, andSave=True)
    print(list_rent())