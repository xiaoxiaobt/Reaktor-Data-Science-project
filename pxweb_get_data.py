import os
import requests
import time
import json
import io
import numpy as np
import pandas as pd
import paavo_queries
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm

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

    time.sleep(0.2)


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

def fetch_paavo_density_and_area(density_file_destination, area_file_destination):
    def clean_df(df):
        # Drop Finland row
        df.drop(index=0, inplace=True)

        # Extract postal code
        df.rename(columns={df.columns[0]: 'Postal code'}, inplace=True)
        df['Postal code'] = df['Postal code'].apply(lambda x: x.split(' ')[0])

        #  Replace '.' with 0 and set Postal code as index
        df.replace({'.': 0}, inplace=True)
        df.set_index('Postal code', inplace=True)

        # Change data type of all columns to integer
        for column in df.columns:
            df[column] = df[column].astype(int)

        return df

    url_2013 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2015/paavo_9_koko_2015.px/'
    url_2014 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2016/paavo_9_koko_2016.px/'
    url_2015 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2017/paavo_9_koko_2017.px/'
    url_2016 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2018/paavo_9_koko_2018.px/'
    url_2017 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2019/paavo_9_koko_2019.px/'

    dfs = {}
    years = np.array([[2014], [2015], [2016], [2017]])

    # Download and clean each dataframe
    dfs[2013] = clean_df(fetch_dataframe(url_2013, paavo_queries.surface_population_query))
    dfs[2014] = clean_df(fetch_dataframe(url_2014, paavo_queries.surface_population_query))
    dfs[2015] = clean_df(fetch_dataframe(url_2015, paavo_queries.surface_population_query))
    dfs[2016] = clean_df(fetch_dataframe(url_2016, paavo_queries.surface_population_query))
    dfs[2017] = clean_df(fetch_dataframe(url_2017, paavo_queries.surface_population_query))

    # Change column labels
    for (year, df) in dfs.items():
        pop_str = 'Population (' + str(year) +')'
        area_str = 'Surface area (' + str(year) + ')'
        density_str = 'Density (' + str(year) +')'

        if year > 2013:
            df.rename(columns={df.columns[0]: area_str, df.columns[1]: pop_str}, inplace=True)
            df.insert(2, density_str, df[pop_str] / df[area_str])
            df.replace({0.0: np.nan})
        else:
            df.rename(columns={df.columns[0]: pop_str}, inplace=True)
            df.replace({0.0: np.nan})

    # Merge dataframe using Postal code index, manually adding density and surface area columns for 2013
    main_table = dfs[2014]
    main_table = main_table.merge(dfs[2013], how='left', on='Postal code')
    main_table = main_table.merge(dfs[2015], how='left', on='Postal code')
    main_table = main_table.merge(dfs[2016], how='left', on='Postal code')
    main_table = main_table.merge(dfs[2017], how='left', on='Postal code')
    main_table.insert(0, 'Density (2013)', np.nan)
    main_table.insert(0, 'Surface area (2013)', np.nan)
    densities = main_table[['Density (2014)', 'Density (2015)', 'Density (2016)', 'Density (2017)']]

    # Linear regression on density. If density is negative, drop the latest density and retry. If there is only 1 usable density, copy it to the 2013 density
    for index, row in densities.iterrows():
        y = row.to_numpy()
        valid_index = np.where(y >= 0)
        valid_years = years[valid_index]
        y = y[valid_index]
        density_prediction = -1.0
        while len(y) > 1 and density_prediction < 0:
            reg = LinearRegression().fit(valid_years, y)
            density_prediction = reg.predict([[2013]])
            if density_prediction < 0:
                y = y[:-1]
                valid_years = valid_years[:-1]
        if len(y) > 1:
            main_table.at[index, 'Density (2013)'] = density_prediction
        elif len(y) ==1:
            main_table.at[index, 'Density (2013)'] = y[0]
        else:
            continue


    # Calculate surface area using density and population
    for index, row in main_table.iterrows():
        if row['Population (2013)'] == np.nan:
            continue
        elif row['Population (2013)'] > 0 and row['Density (2013)'] > 0:
            main_table.at[index, 'Surface area (2013)'] = round(row['Population (2013)']/row['Density (2013)'])
        elif row['Population (2013)'] == 0 and row['Density (2013)'] == 0:
            main_table.at[index, 'Surface area (2013)'] = row['Surface area (2014)']

    main_table = main_table.fillna(0)
    # Results
    densities = main_table[['Density (2013)', 'Density (2014)', 'Density (2015)', 'Density (2016)', 'Density (2017)']]
    areas = main_table[['Surface area (2013)', 'Surface area (2014)', 'Surface area (2015)', 'Surface area (2016)', 'Surface area (2017)']]

    # Export to tsv files
    densities.to_csv(density_file_destination, sep='\t')
    areas.to_csv(area_file_destination, sep='\t')


def fetch_paavo_housing(destination_directory, postal_code_file, density_file):
    def postal_standardize(df):
        df= df.astype({'Postal code': str})
        for i in list(df.index):
            df.at[i, 'Postal code'] = '0' * (5-len(df.at[i,'Postal code']))+ df.at[i, 'Postal code']
        return df

    def postal_merge(left, right):
        return left.merge(right, how='left', on='Postal code')

    # Calculate housing prices for groups of postal codes with the same first 6-n digits
    def get_mean_simple(df, n):
        df_n = pd.DataFrame(df['Postal code'].apply(lambda x: x[:(1 - n)]))
        df_n.rename(columns={df_n.columns[0]: 'Postal code'}, inplace=True)
        df_n = df_n.join(df[['Total value', 'Number']].copy())
        df_n = df_n.groupby("Postal code", as_index=False).agg("sum")
        df_n['Mean'] = df_n['Total value'] / df_n['Number']
        df_n.drop(['Total value', 'Number'], axis=1, inplace=True)
        # df_n.set_index('Postal code', inplace=True)
        return df_n

    # Impute using the results above
    def impute_simple(df, df_n):
        df_ni = df_n.set_index('Postal code')
        for code in list(df_n['Postal code']):
            df_rows = np.array(df[df['Postal code'].str.startswith(code)].index)
            for i in df_rows:
                if df.at[i, 'Mean'] == 0 or np.isnan(df.at[i, 'Mean']):
                    df.at[i, 'Mean'] = df_ni.at[code, 'Mean']
        return df

    # Impute with respect to density using a linear model
    def impute_with_density(df, postal_df):

        def postal_truncate(n):
            df_n = postal_df.copy()
            df_n['Postal code'] = df_n['Postal code'].apply(lambda x: x[:(1-n)])
            df_n.drop_duplicates(subset='Postal code', inplace=True)
            return df_n

        def impute_price(df_, n):
            truncated_postal = postal_truncate(n)

            for code in truncated_postal['Postal code']:
                sub_df = df_[df_['Postal code'].str.startswith(code)]
                good_df = sub_df[sub_df['Mean'] != 0]
                bad_df = sub_df[sub_df['Mean'] == 0]
                if len(good_df.index) >= 7:
                    good_df = good_df.nsmallest(15, 'Mean')
                    X = good_df['Density']
                    y = good_df['Mean']
                    X = sm.add_constant(X.values)

                    model = sm.OLS(y, X).fit()
                    for i in bad_df.index:
                        if df_.at[i, 'Mean'] <= 0 or np.isnan(df_.at[i, 'Mean']):
                            df_.at[i, 'Mean'] = int(model.predict([1, df_.at[i, 'Density']])[0])
            return df_

        for i in range(3,6):
            df = impute_price(df, i)

        return df


    main_table = postal_standardize(pd.read_csv(postal_code_file, sep='\t'))
    density = postal_standardize(pd.read_csv(density_file, sep='\t'))
    density = density.fillna(0)
    postal_code =  main_table.copy()

    year_list = list(range(2005, 2018))
    base_query = paavo_queries.ts_housing_query['query']

    for year in year_list:
        for quarter in range(0, 5):
            # Construct the json query
            new_query =  [{"code": "Vuosi", "selection": {"filter": "item", "values": [str(year)]}}, {"code": "Neljännes", "selection": {"filter": "item", "values": [str(quarter)]}}] + base_query
            quarter_query = {"query": new_query, "response": {"format": "csv"}}
            if quarter == 0:
                mean_label = 'Housing price (' + str(year) + ')'
            else:
                mean_label = str(year) + 'Q' +str(quarter)

            # Get the data table for the quarter
            quarter_frame = postal_standardize(fetch_dataframe(paavo_queries.housing_url, query= quarter_query))

            # Leave only Postal code and house price
            quarter_frame = quarter_frame[['Postal code', 'Mean', 'Number']]

            # Replace missing value '.' with '0'
            quarter_frame.replace({'.': '0'}, inplace=True)

            # Change mean to housing price and convert to float, number to Int
            quarter_frame['Mean'] = quarter_frame['Mean'].astype(int)
            quarter_frame['Number'] = quarter_frame['Number'].astype(int)

            # Calculate the total housing value for each row
            quarter_frame['Total value'] = quarter_frame['Mean'] * quarter_frame['Number']

            # Get the complete postal code
            quarter_frame = postal_merge(postal_code, quarter_frame)

            # Change the numbers of houses where the prices are hidden to 0 so that the calculation of the group mean is not affected
            for code in list(quarter_frame.index):
                if quarter_frame.at[code, 'Mean'] == 0 or np.isnan(quarter_frame.at[code, 'Mean']):
                    quarter_frame.at[code, 'Number'] = 0

            if year < 2013:
                # Calculating the average housing price of postal codes with the same first 3, 2, 1 digits
                quarter_frame_3 = get_mean_simple(quarter_frame, 3)
                quarter_frame_4 = get_mean_simple(quarter_frame, 4)
                quarter_frame_5 = get_mean_simple(quarter_frame, 5)

                # Fill df_4 empty values with that of df_5 and df_3 with that of df_4
                quarter_frame_4 = impute_simple(quarter_frame_4, quarter_frame_5)
                quarter_frame_3 = impute_simple(quarter_frame_3, quarter_frame_4)

                # Round mean values and fill empty cells with zero, though there should not be any at this point
                quarter_frame_3.fillna(0, inplace=True)
                quarter_frame_3['Mean'] = quarter_frame_3['Mean'].astype(int)

                # Fill the year frame with mean postal code values
                quarter_frame = impute_simple(quarter_frame, quarter_frame_3)
            else:
                # Extract density values of the year
                year_density = density[['Postal code', 'Density (' + str(year) + ')']]
                year_density = postal_standardize(year_density)
                year_density.rename(columns={('Density (' + str(year) + ')'): 'Density'}, inplace=True)
                quarter_frame = postal_merge(quarter_frame, year_density)
                quarter_frame = quarter_frame.astype({'Density': float})
                quarter_frame = quarter_frame.fillna(0)

                # Imputing using density
                quarter_frame = impute_with_density(quarter_frame, postal_code)
                quarter_frame = quarter_frame.fillna(0)


            # Drop unnecessary columns, set Postal code as index, rename mean by year specific label
            quarter_frame = quarter_frame[['Postal code','Mean']]
            #print(quarter_frame[quarter_frame['Mean'] <= 0].count())
            quarter_frame.rename(columns={'Mean': mean_label}, inplace=True)

            # Combine the data from the year table into the main table
            main_table = postal_merge(main_table, quarter_frame)
            print('Year ' + str(year) + ', quarter ' + str(quarter) + ': Done')

    # Construct yearly and quarterly tables
    quarter_columns = main_table.columns[main_table.columns.str.contains('Q')]
    year_columns = main_table.columns[main_table.columns.str.contains('Housing')]

    main_table.set_index('Postal code', inplace=True)

    year_table = main_table[year_columns]
    quarter_table = main_table[quarter_columns]

    # Save yearly and quarterly tables to files
    year_table.to_csv(os.path.join(destination_directory, 'paavo_housing_data_yearly.tsv'), sep='\t')
    quarter_table.to_csv(os.path.join(destination_directory, 'paavo_housing_data_quarterly.tsv'), sep='\t')
