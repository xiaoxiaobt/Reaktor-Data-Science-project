# Collect data into data frames based on the year of the file
import glob
import os
import re
import pandas as pd
from pathlib import Path
import numpy as np


def postalcode_and_area(df):
    """
    Split the column "Postal code area" into Postal code (the numerical postal code)
    and Area (the name of the area)
    :param df: the original data frame
    :return: the updated data frame
    """
    # Rename the first column
    df.rename(columns={df.columns[0]: "Postal code"}, inplace=True)

    for c in df.columns:
        drop_double_columns(df, c)

    # Duplicate the first column and add it as the second column
    # df.insert(1, 'Area', df['Postal code'])
    df['Area'] = [''] * len(df.index)

    # Strip out numbers from the content of the second column:
    # only the name of the area will remain.
    content = df["Postal code"].copy()
    content = content.apply(lambda x: re.sub('[0-9_]+', '', x))
    df["Area"] = content

    # Strip out the letters and symbols from the content of the first column:
    # only the postal code digits will remain.
    content = df["Postal code"]
    content = content.apply(lambda x: re.sub('[\D]+', '', x))
    df["Postal code"] = content

    return df


def drop_double_columns(df, header_to_drop):
    """
    Drops duplicate columns whose header is 'header_to_drop' in a data frame.
    :param df: the original data frame
    :param header_to_drop: the column name
    :return: None (the data frame is edited inplace)
    """
    col_list = df.columns.tolist()
    to_drop = get_index_positions(col_list, header_to_drop)
    if len(to_drop) > 1:
        to_drop = to_drop[1:]
        for i in to_drop:
            col_list[i] = 'todrop'
        df.columns = col_list
        df.drop(columns=['todrop'], inplace=True)


def clean_columns(df):
    """
    This function cleans the last part of the name of the column,
    by removing the pattern (AA), counts how many times each column appears,
    and drop the duplicates by calling 'drop_double_columns'.
    :param df: the dataframe to clean
    :return: the cleaned dataframe
    """
    # Saving columns names
    new_columns = {x: x for x in df.columns}
    for key, value in new_columns.items():
        # Removing pattern (AA) from the columns' names
        new_columns[key] = re.sub('\([^)]{2}\)', '', value)

    # The cleaned names become the new columns in the data frame
    df.rename(columns=new_columns, inplace=True)

    for c in df.columns:
        drop_double_columns(df, c)

    return df


def drop_and_replace(df):
    """
    This function deletes the row 0 (Finland), drops remaining duplicate columns,
    and replaces missing values. Inline comments explain how missing/private values are handled.
    :param df: the data frame to clean
    :return: the cleaned data frame
    """
    # Drop row 0: Finland
    df.drop(index=0, inplace=True)

    # Drop unnecessary columns that might have been copied until now
    for c in df.columns:
        drop_double_columns(df, c)

    # Replace missing values
    # RULES:
    #       1) if it's a count, take the min of the column
    #           and if the min is greater than 15, take 15
    #       2) if it's a rate/percentage/average/median, take the median of the column
    # MISSING VALUES COME FROM:
    #       (RA) -> Data on dwellings are protected if there is only one residential building in the area.
    #               Data on the average floor area of dwellings and type of house are protected if there is only one
    #               residential building or fewer than 30 dwellings in the area. Protected fields have the value "..".
    #               Data on free-time residences is not protected.
    #       (KO) -> Data on educational structure are confidential if the area contains fewer than 30 people aged 18 or over
    #       (HR) -> Data on income are confidential if the area contains fewer than 30 people aged 18 or over
    #       (TE) -> Data on size and stage in life of households are confidential if there are fewer than 30 households in the area.
    #       (TR) -> Data on the income of households are confidential if there are fewer than ten households in the area.
    #       (TP) -> Data on workplaces are protected if there are fewer than 10 workplaces in the area
    # SOURCE:
    #       http://www.stat.fi/static/media/uploads/tup/paavo/paavo_kuvaus_en.pdf

    df.replace({'..': np.nan, '.': np.nan}, inplace=True)
    for col_name in df.columns:
        if df[col_name].isna().sum() > 0:
            filter_on_column = df[df[col_name].notna()]
            if 'Average' in col_name or 'average' in col_name or 'ratio' in col_name or 'rate' in col_name \
            or 'income' in col_name or 'purchasing power' in col_name:
                nonzero_minimum = filter_on_column[col_name].median()
            else:
                nonzero_minimum = filter_on_column[col_name][filter_on_column[col_name].astype('float') > 0].min()
                nonzero_minimum = min(float(nonzero_minimum), 15)

            df[col_name].fillna(nonzero_minimum, inplace=True)

    if sum(df.isna().sum()) > 0:
        print("WARNING: There are still missing values!")
        df.replace({None: 0}, inplace=True)
        df.fillna(0, inplace=True)

    return df


def get_index_positions(list_of_elements, element):
    """
    Returns the indexes of all occurrences of the given 'element' in
    the list of columns 'list_of_elements'.
    :param list_of_elements: the list of the columns of the data frame
    :param element: the name of the column to find
    :return: list of indexes
    """
    index_pos_list = []
    index_pos = 0
    while True:
        try:
            # Search for item in list from index_pos to the end of list
            index_pos = list_of_elements.index(element, index_pos)
            # Add the index position in list
            index_pos_list.append(index_pos)
            index_pos += 1
        except ValueError as _:
            break

    return index_pos_list


def add_density(year, pclist):
    """
    Open the file 'density.tsv' in the folder 'data' and return
    a dictionary where the keys are postal codes and the values are density values.
    NOTE: There is no density for the year 2012.
    When asking for 2012, the column 2013 will be returned.
    For the years outside the known range, an empty dictionary is returned.
    :param year: string, the year to read
    :param pclist: list of strings, where each element is a postal code to take
    :return: dictionary of postal codes and population density
    """
    if year == '2012': year = '2013'
    if year not in ['2012', '2013', '2014', '2015', '2016', '2017']:
        print('WARNING: wrong year! Empty Series returned')
        return {}
    else:
        col_name = 'Density (' + year + ')'
        dens_df = pd.read_csv(Path('data/') / 'density.tsv', sep='\t', usecols=['Postal code', col_name], dtype={'Postal code': object})
        dens_df.fillna(0)
        dens_df = dens_df[dens_df['Postal code'].isin(pclist)]
        return dens_df.copy().set_index('Postal code').to_dict()[col_name]


def data_format(df):
    """
    Convert each column to the correct format.
    :param df: the dataframe
    :return: the dataframe
    """
    for key in df.columns:
        if key == 'Postal code' or key == 'Area':
            df[key] = df[key].astype('object')
        else:
            df[key] = df[key].astype('float')
    return df


def get_all_dataframes():
    """
    This function loads all the files that have been downloaded
    as .csv files by calling fetch_paavo("") from pxweb_get_data.py
    (last tested version: 13.11.2019).
    The files are stored in the folder 'paavo_data'.
    This function assigns the data to the correct data frame according to the year,
    and calls drop_and_replace to clean the data frame.
    The latest postal codes (from 2017) are taken into account.
    :return: df_dic, a dictionary where the keys are the years
            and the values are the corresponding data frames, and
            common_columns, a list of common columns as found by 'get_common_columns'
    """
    # Read all the files with the data
    file_list = glob.glob("paavo_data/*.csv")

    # Create a sorted list of the years: remove A-Öa-ö_.,:; /()\\-
    years_list = sorted({re.sub('[\D]+', '', y) for y in file_list})
    print("Preparing data: ",  years_list)

    # Build a dictionary of DataFrames:
    # to each year, it is associated one DataFrame
    df_dic = {y: pd.DataFrame() for y in years_list}

    # Dataframe 2017 --> we need 2017 fists, since we want to refer to the latest postal codes and areas
    for file in file_list:
        if '2017' in file:
            if df_dic['2017'].size == 0:
                df_dic['2017'] = pd.read_csv(file, sep=',', skiprows=0, encoding='iso-8859-1')
            else:
                # Open the file in a temporary data frame
                temp = pd.read_csv(file, sep=',', skiprows=0, encoding='iso-8859-1')
                # Merge the temporary data frame to the main one
                df_dic['2017'] = df_dic['2017'].join(temp, lsuffix='_caller')

    df_dic['2017'] = drop_and_replace(df_dic['2017'])
    df_dic['2017'] = postalcode_and_area(df_dic['2017'])

    postalcodes_list = df_dic['2017']['Postal code'].values

    years_list.remove('2017')
    # Fill the DataFrames with the data from the correct files
    for file in file_list:
        for y in years_list:
            if df_dic[y].size == 0:
                df_dic[y]['Postal code'] = df_dic['2017']['Postal code'].copy()
                df_dic[y]['Area'] = df_dic['2017']['Area'].copy()
            if y in file:
                # Open the file in a temporary dataframe
                temp = pd.read_csv(file, sep=',', skiprows=0, encoding='iso-8859-1')
                temp = drop_and_replace(temp)
                temp = postalcode_and_area(temp)
                temp = data_format(temp)
                idx = pd.Index(temp['Postal code'].values)
                old_pc = list(set(idx) - set(postalcodes_list))
                temp = temp[~temp['Postal code'].isin(old_pc)]
                df_dic[y] = pd.concat([df_dic[y], temp.copy()], axis=1, sort=False).reindex(df_dic[y].index)

    for year, dfy in df_dic.items():
        # Here we add the columns 'Bus stops', 'Sold', 'Rented', 'Population density', 'Lat', 'Lon'
        # The column 'Inhabitants total' becomes useless: we can remove it after scaling
        dfy = clean_columns(dfy)
        dfy.drop(columns=['Postal code area', 'Postialue', 'Area_x', 'Area_y'], inplace=True, errors='ignore')
        dfy = data_format(dfy)
        dfy.reset_index(inplace=True)

        # Add population density
        dfy.drop(columns=['index'], inplace=True)
        dens_df = add_density(year=year, pclist=postalcodes_list)

        mydensitylist = []
        for pc in postalcodes_list:
            if pc in dens_df.keys():
                mydensitylist.append(dens_df[pc])
            else:
                mydensitylist.append(0)

        dfy['Density'] = [0] * len(dfy.index)
        new_df = pd.DataFrame({'Density': mydensitylist})
        dfy.update(new_df)

        # Remove the year and extra comma
        dfy.columns = [re.sub(r", \d{4} $", "", column) for column in dfy.columns]

    print("Data are ready")
    return df_dic, get_common_columns(df_dic)


def get_tsv_files():
    """
    Call get_all_dataframes and save each year on a file
    :return: None
    """
    df_dic, _ = get_all_dataframes()

    folder = 'dataframes'
    if not os.path.exists(folder):
        os.makedirs(folder)

    for y, df in df_dic.items():
        df.fillna(0, inplace=True)
        filename = 'df'+str(y)+'.tsv'
        print("Saving ", filename)
        df.to_csv(Path(folder) / filename, sep='\t', index=False, encoding='utf-8')


def get_common_columns(df_dic):
    """
    :param: df_dic, a dictionary of data frames, as returned by 'get_all_dataframes'
    :return: a list of column names, representing the common subset of columns
            that appears in all data frames from 2013 on (2012 is excluded on purpose,
            since it has too few attributes)
    """
    years = list(df_dic.keys())
    # 2012 is years[0]
    y0 = years[1]
    years = years[2:]
    common = set(df_dic[y0].columns)
    for y in years:
        common = common.intersection(df_dic[y].columns)
    return sorted(common)


if __name__ == '__main__':
    get_tsv_files()