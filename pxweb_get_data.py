import os
import requests
import time
import json
import io
import numpy as np
import pandas as pd
import paavo_queries
from sklearn.linear_model import LinearRegression

## NOTE: Table 9_koko access is forbidden from the API for some reasons.

# url to the API
main_paavo_url = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/'


## Helper to make url to the paavo API
def paavo_url(level, table):
    return main_paavo_url + str(level) + '/' + table


# Fetch a single file from PXweb API. File name should end with '.csv'
def fetch_csv(url, destination_directory, file_name, query={"query": [], "response": {"format": "csv"}}):
    response = requests.post(url, json=query, stream=True, allow_redirects=True)

    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    destination_file = os.path.join(destination_directory, file_name)

    if response.status_code == 200:
        open(destination_file, 'wb').write(response.content)
        print('Downloaded ' + file_name + ' from ' + url)
    else:
        print('Could not download ' + file_name + ' from ' + url)
        print('HTTP/1.1 ' + str(response.status_code))

    time.sleep(1)


# Fetch the whole paavo directory
def fetch_paavo(destination_directory):
    # Getting levels from paavo database
    levels = []
    response = requests.post('http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/')
    response_texts = json.loads(response.text)

    for response_text in response_texts:
        levels.append(str(response_text['id']))

    paavo_directory = os.path.join(destination_directory, 'paavo_data')

    for level in levels:
        response = requests.post('http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/' + str(level))
        response_texts = json.loads(response.text)
        table_data = {}

        for response_text in response_texts:
            table_data[response_text['id']] = str(response_text['text']).split('. ')[-1].replace("'", "").replace(" ", "_")

        for (id, name) in table_data.items():
            url = paavo_url(level, id)
            file_name = name + '.csv'
            fetch_csv(url, paavo_directory, file_name)


# Download a table from PXweb API to a DataFrame
def fetch_dataframe(url, query={"query": [], "response": {"format": "csv"}}):
    response = requests.post(url, json=query, stream=True, allow_redirects=True)

    if response.status_code == 200:
        byte_data = io.BytesIO(response.content)
        df = pd.read_csv(byte_data, sep=',', encoding='iso-8859-1')
        print('Downloaded data from ' + url)
        return df
    else:
        print('Could not download from ' + url)
        print('HTTP/1.1 ' + str(response.status_code))
        return pd.DataFrame()

    time.sleep(1)


# Download the whole paavo directory to a dictionary with names as keys and dataframes as values
def paavo_data():
    data = {}
    # Getting levels from paavo database
    levels = []
    response = requests.post('http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/')
    response_texts = json.loads(response.text)

    for response_text in response_texts:
        levels.append(str(response_text['id']))

    for level in levels:
        response = requests.post(
            'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/' + str(level))
        response_texts = json.loads(response.text)
        table_data = {}

        for response_text in response_texts:
            table_data[response_text['id']] = str(response_text['text']).split('. ')[-1].replace("'", "").replace(" ", "_")

        for (id, name) in table_data.items():
            url = paavo_url(level, id)
            df = fetch_dataframe(url)

            if not df.empty:
                data[name] = df

            time.sleep(1)

    return data


def fetch_paavo_housing(destination_directory, postal_code_file):
    main_table = pd.read_csv(postal_code_file, sep='\t')

    # print(main_table.columns)
    main_table['Postal code'] = main_table['Postal code'].astype(str)
    main_table['Postal code'] = main_table['Postal code'].apply(lambda x: '0' * (5 - len(x)) + x)
    main_table['Postal index'] = main_table['Postal code'].astype(str)
    main_table.set_index('Postal index', inplace=True)

    year_list = list(range(2005, 2018))

    base_query = paavo_queries.housing_query['query']

    for year in year_list:
        # Construct the json query
        new_query = [{"code": "Vuosi", "selection": {"filter": "item", "values": [str(year)]}}] + base_query
        year_query = {"query": new_query, "response": {"format": "csv"}}

        # Get the data table for the year
        df = fetch_dataframe('http://pxnet2.stat.fi/PXWeb/api/v1/en/StatFin_Passiivi/asu/ashi/statfinpas_ashi_pxt_004_2017q4.px', query=year_query)

        # Getting only Postal code and house price
        df = df[['Postal code', 'Mean', 'Number']]

        # Replace missing value '.' with '0'
        df.replace({'.': '0'}, inplace=True)

        # Edit all postal code to have 5 digits
        df['Postal code'] = df['Postal code'].astype(str)
        df['Postal code'] = df['Postal code'].apply(lambda x: '0' * (5 - len(x)) + x)
        df.rename(columns={'Postal code': 'Postal index'}, inplace=True)
        df.set_index('Postal index', inplace=True)

        # Change mean to housing price and convert to float, number to Int
        df['Mean'] = df['Mean'].astype(int)
        df['Number'] = df['Number'].astype(int)
        df['Total value'] = df['Mean'] * df['Number']

        # Get the full postal code from the main table
        df = df.loc[df.index.intersection(main_table.index)].combine_first(main_table)
        df['Postal code'] = df['Postal code'].astype(int).astype(str)
        df['Postal code'] = df['Postal code'].apply(lambda x: '0' * (5 - len(x)) + x)

        # Change the numbers of houses where the prices are hidden to 0 so that the calculation of the group mean is not affected
        for code in list(df.index):
            if df.at[code, 'Mean'] == 0 or np.isnan(df.at[code, 'Mean']):
                df.at[code, 'Number'] = 0

        # Calculating the average housing price of postal codes with the same first 3 digits
        df_3 = pd.DataFrame(df['Postal code'].apply(lambda x: x[:-2]))
        df_3 = df_3.join(df[['Total value', 'Number']].copy())
        df_3 = df_3.groupby("Postal code", as_index=False).agg("sum")
        df_3['Mean'] = df_3['Total value'] / df_3['Number']
        df_3.drop(['Total value', 'Number'], axis=1, inplace=True)
        df_3.set_index('Postal code', inplace=True)

        # Calculating the average housing price of postal codes with the same first 2 digits
        df_4 = pd.DataFrame(df['Postal code'].apply(lambda x: x[:-3]))
        df_4 = df_4.join(df[['Total value', 'Number']].copy())
        df_4 = df_4.groupby("Postal code", as_index=False).agg("sum")
        df_4['Mean'] = df_4['Total value'] / df_4['Number']
        df_4.drop(['Total value', 'Number'], axis=1, inplace=True)
        df_4.set_index('Postal code', inplace=True)

        # Calculating the average housing price of postal codes with the same first 1 digit
        df_5 = pd.DataFrame(df['Postal code'].apply(lambda x: x[:-4]))
        df_5 = df_5.join(df[['Total value', 'Number']].copy())
        df_5 = df_5.groupby("Postal code", as_index=False).agg("sum")
        df_5['Mean'] = df_5['Total value'] / df_5['Number']
        df_5.drop(['Total value', 'Number'], axis=1, inplace=True)
        df_5.set_index('Postal code', inplace=True)

        # Fill df_4 empty values with that of df_5
        for code in list(df_5.index):
            df_rows = np.array(df_4[df_4.index.str.startswith(code)].index)

            for i in df_rows:
                if df_4.at[i, 'Mean'] == 0 or np.isnan(df_4.at[i, 'Mean']):
                    df_4.at[i, 'Mean'] = df_5.at[i[:-1], 'Mean']

        # Fill df_3 empty values with that of df_4
        for code in list(df_4.index):
            df_rows = np.array(df_3[df_3.index.str.startswith(code)].index)

            for i in df_rows:
                if df_3.at[i, 'Mean'] == 0 or np.isnan(df_3.at[i, 'Mean']):
                    df_3.at[i, 'Mean'] = df_4.at[i[:-1], 'Mean']

        # Round mean values and fill empty cells with zero, though there should not be any at this point
        df_3.fillna(0, inplace=True)
        df_3['Mean'] = df_3['Mean'].astype(int)

        # Drop unnecessary columns, set Postal code as index
        df.drop(['Number', 'Total value'], axis=1, inplace=True)
        df.set_index('Postal code', inplace=True)

        # Combine the data from the year table into the main table
        main_table = df.loc[df.index.intersection(main_table.index)].combine_first(main_table)
        mean_label = 'Housing price (' + str(year) + ')'
        main_table.rename(columns={'Mean': mean_label}, inplace=True)
        main_table.fillna(0, inplace=True)

        for code in list(df_3.index):
            df_rows = np.array(main_table[main_table.index.str.startswith(code)].index)

            for i in df_rows:
                if main_table.at[i, mean_label] == 0 or np.isnan(main_table.at[i, mean_label]):
                    main_table.at[i, mean_label] = df_3.at[i[:-2], 'Mean']

        time.sleep(0.2)

    # Drop Postal code column, insert columns for prediction values
    main_table.drop(['Postal code'], axis=1, inplace=True)
    old_columns = main_table.columns
    old_columns_count = len(old_columns)
    main_table.insert(old_columns_count, 'Housing price (2018)', np.nan)
    main_table.insert(old_columns_count + 1, 'Housing price (2019)', np.nan)
    main_table.insert(old_columns_count + 2, 'Housing price (2020)', np.nan)

    # Create the year array for regression
    year_array = np.reshape(np.array(year_list), (len(year_list), 1))

    # Linear regression for every row
    for index, row in main_table.iterrows():
        y = row[old_columns].to_numpy()
        reg = LinearRegression().fit(year_array, y)
        main_table.at[index, 'Housing price (2018)'] = int(reg.predict([[2018]]))
        main_table.at[index, 'Housing price (2019)'] = int(reg.predict([[2019]]))
        main_table.at[index, 'Housing price (2020)'] = int(reg.predict([[2020]]))

    # Combine all tables
    main_table.to_csv(destination_directory + 'paavo_housing_data.tsv', sep='\t')
