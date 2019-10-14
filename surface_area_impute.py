import numpy as np
import paavo_queries
import pxweb_get_data
import bulk_load_year_based
from sklearn.linear_model import LinearRegression

url_2013 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2015/paavo_9_koko_2015.px'
url_2014 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2016/paavo_9_koko_2016.px/'
url_2015 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2017/paavo_9_koko_2017.px/'
url_2016 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2018/paavo_9_koko_2018.px/'
url_2017 = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/2019/paavo_9_koko_2019.px/'

dfs = {}
densities = {}
years = np.array([[2014], [2015], [2016], [2017]])

dfs[2013] = bulk_load_year_based.clean_df(pxweb_get_data.fetch_dataframe(url_2013, paavo_queries.surface_population_query))
dfs[2014] = bulk_load_year_based.clean_df(pxweb_get_data.fetch_dataframe(url_2014, paavo_queries.surface_population_query))
dfs[2015] = bulk_load_year_based.clean_df(pxweb_get_data.fetch_dataframe(url_2015, paavo_queries.surface_population_query))
dfs[2016] = bulk_load_year_based.clean_df(pxweb_get_data.fetch_dataframe(url_2016, paavo_queries.surface_population_query))
dfs[2017] = bulk_load_year_based.clean_df(pxweb_get_data.fetch_dataframe(url_2017, paavo_queries.surface_population_query))

# Clean and change column labels
for (year, df) in dfs.items():
    pop_str = 'Population (' + str(year) +')'
    area_str = 'Surface area (' + str(year) + ')'
    density_str = 'Density (' + str(year) +')'

    # Set Postal code as index
    df['Postal code'] = df['Postal code'].str.replace(',', '').str.replace('.', '')
    df.set_index('Postal code', inplace=True)


    if year > 2013:
        df.rename(columns={df.columns[1]: area_str, df.columns[2]: pop_str}, inplace=True)
        df.insert(3, density_str, df[pop_str] / df[area_str])
        df.replace({0.0: np.nan})
    else:
        df.rename(columns={df.columns[1]: pop_str}, inplace=True)
        df.replace({0.0: np.nan})

# Merge dataframe using Postal code index, manually adding density and surface area columns for 2013
main_table = dfs[2014]
main_table = dfs[2013].loc[dfs[2013].index.intersection(main_table.index)].combine_first(main_table)
main_table = dfs[2015].loc[dfs[2015].index.intersection(main_table.index)].combine_first(main_table)
main_table = dfs[2016].loc[dfs[2016].index.intersection(main_table.index)].combine_first(main_table)
main_table = dfs[2017].loc[dfs[2017].index.intersection(main_table.index)].combine_first(main_table)
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

# Results
densities = main_table[['Density (2013)', 'Density (2014)', 'Density (2015)', 'Density (2016)', 'Density (2017)']]
areas = main_table[['Surface area (2013)', 'Surface area (2014)', 'Surface area (2015)', 'Surface area (2016)', 'Surface area (2017)']]