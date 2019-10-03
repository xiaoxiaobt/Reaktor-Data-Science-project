import os
import requests
import time
import json
import io
import pandas as pd

##NOTE: Table 9_koko access is forbidden from the API for some reasons.

# url to the API
main_paavo_url = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/'

## Helper to make url to the paavo API
def paavo_url(level, table):
    return main_paavo_url + str(level) + '/' + table


# Fetch a single file from PXweb API. File name should end with '.csv'
def fetch_csv(url, destination_directory, file_name):
    response = requests.post(url, json = {"query":[],"response":{"format":"csv"}}, stream=True, allow_redirects=True)

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
        response = requests.post('http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/'+ str(level))
        response_texts = json.loads(response.text)
        table_data={}

        for response_text in response_texts:
            table_data[response_text['id']] = str(response_text['text']).split('. ')[-1].replace("'", "").replace(" ", "_")

        for (id, name) in table_data.items():
            url = paavo_url(level, id)
            file_name = name + '.csv'
            fetch_csv(url, paavo_directory, file_name)

# Download a table from PXweb API to a DataFrame
def fetch_dataframe(url):
    response = requests.post(url, json={"query": [], "response": {"format": "csv"}}, stream=True, allow_redirects=True)

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
