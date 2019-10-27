# -*- coding: utf-8 -*-
#

import requests
import pandas as pd
from tabulate import tabulate
from bs4 import BeautifulSoup
import os


base_url = u'https://asuntojen.hintatiedot.fi/haku/?search=1&l=0&c=&cr=1&ps='
end_url = '&pc=0&nc=0&amin=&amax='

def get_query(ps='00100'):
    """
    Perform the query on one postal code.
    :param ps: the postal code to query.
    :return: a dataframe
    """
    res = requests.get(base_url+ps+end_url)
    soup = BeautifulSoup(res.content,'lxml')
    soup = soup.find("table", {"id": "mainTable"})
    df_list = pd.read_html(str(soup))
    print(tabulate(df_list[0], headers='keys', tablefmt='psql'))
    return df_list[0]

def collect_query():
    """
    Call get_query on all the known postal codes
    and saves a .tsv file for each postal code.
    :return: None
    """
    housing_folder = 'housing'
    if not os.path.exists(housing_folder):
        os.makedirs(housing_folder)
    pc_list = pd.read_csv(r'dataframes//df2017.tsv', sep='\t', encoding='utf-8')['Postal code'].values
    for pc in pc_list:
        df = get_query(pc)
        file = r'df' + str(pc) + '.tsv'
        df.to_csv(os.path.join(housing_folder, file), sep='\t', index=False, encoding='utf-8')
    return None