import os
import requests
import time
import json
import io
import pandas as pd
import paavo_queries

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


def fetch_paavo_housing(destination_directory):
    year_list = list(range(2005, 2018))
    dfs = {}

    base_query = paavo_queries.housing_query['query']

    for year in year_list:
        new_query = [{"code": "Vuosi", "selection": {"filter": "item", "values": [str(year)]}}] + base_query
        year_query = {"query": new_query, "response": {"format": "csv"}}
        df = fetch_dataframe('http://pxnet2.stat.fi/PXWeb/api/v1/en/StatFin_Passiivi/asu/ashi/statfinpas_ashi_pxt_004_2017q4.px', query=year_query)
        # Getting only Postal code and house price
        df = df[['Postal code', 'Mean']]

        # Replace missing value '.' with '0'
        df.replace({'.': '0'}, inplace=True)

        # Edit all postal code to have 5 digits
        df['Postal code'] = df['Postal code'].astype(str)
        df['Postal code'] = df['Postal code'].apply(lambda x: '0' * (5 - len(x)) + x)

        # Change mean to housing price and convert to float
        df['Mean'] = df['Mean'].astype(float)
        df.rename(columns={'Mean': ('Housing price (' + str(year) + ')')}, inplace=True)

        # Set Postal code as index
        df.set_index('Postal code', inplace=True)
        dfs[year] = df
        time.sleep(0.2)

    # Combine all tables
    main_table = dfs[2005]
    for year in range(2006, 2018):
        main_table = dfs[year].loc[dfs[year].index.intersection(main_table.index)].combine_first(main_table)

    main_table.to_csv(path=destination_directory + 'paavo_housing.tsv', sep='\t')
