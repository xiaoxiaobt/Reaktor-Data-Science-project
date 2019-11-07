# Collecting data into dataframes based on the year the datafile shows
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
from housing_price import list_sold, list_rent


def first_columns(df):
    """
    Split the column "Postal code area" into Postal code (the numerical postal code)
    and Area (the name of the area)
    :param df: the dataframe
    :return: the dataframe
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
    # only the postal code, in numerical form, will remain.
    content = df["Postal code"]
    content = content.apply(lambda x: re.sub('[\D]+', '', x))
    df["Postal code"] = content

    return df


def drop_double_columns(df, header_to_drop):
    """
    Drops duplicate columns whose header is 'header_to_drop' in a dataframe.
    :param df: the dataframe
    :param header_to_drop: the column name
    :return: None (the dataframe is edited inplace)
    """
    col_list = df.columns.tolist()
    to_drop = getIndexPositions(col_list, header_to_drop)
    if len(to_drop) > 1:
        to_drop = to_drop[1:]
        for i in to_drop:
            col_list[i] = 'todrop'
        df.columns = col_list
        df.drop(columns=['todrop'], inplace=True)


def clean_columns(df):
    """
    This function clean the last part of the name of the column,
    by removing the pattern (AA). Then it renames the columns
    of the dataframe and counts how many times each column appears.
    We drop the duplicates and keep only one of the duplicate columns.
    :param df: the dataframe to clean
    :return: the cleaned dataframe
    """
    # Dropping duplicates columns
    new_columns = {x: x for x in df.columns}
    for key, value in new_columns.items():
        # Removing pattern (AA) from the columns' names
        new_columns[key] = re.sub('\([^)]{2}\)', '', value)

    df.rename(columns=new_columns, inplace=True)

    for c in df.columns:
        drop_double_columns(df, c)

    return df


def clean_df(df):
    """
    This function cleans the dataframe, by dropping the row 0 (Finland),
    dropping remaining duplicate columns, and replacing missing values with 0.
    :param df: the dataframe to clean
    :return: the cleaned dataframe
    """
    # Drop row 0: Finland
    df.drop(index=0, inplace=True)

    # Drop unnecessary columns that might have been copied while building the dataframe
    for c in df.columns:
        drop_double_columns(df, c)

    # Replace missing values with 0
    df.replace({'..': np.nan, '.': np.nan}, inplace=True)
    df.replace({None: 0}, inplace=True)
    df.fillna(0, inplace=True)

    return df


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


def pairwise_correlation(df):
    """
    This function plots the pairwise correlation
    between attributes of the dataframe.
    :param df: the dataframe to plot
    :return: None
    """
    f = plt.figure(figsize=(19, 15))
    plt.matshow(df.corr(), fignum=f.number)

    plt.xticks(range(df.shape[1]), df.columns, fontsize=7, rotation=45)
    plt.yticks(range(df.shape[1]), df.columns, fontsize=7)

    cb = plt.colorbar()
    cb.ax.tick_params(labelsize=7)

    plt.title('Correlation Matrix', fontsize=10)
    plt.show()


def bulk_load():
    """
    This function loads all the datafiles that have been
    downloaded by pxweb_get_data.py (Version: 29.09.2019)
    and organizes them into dataframes according to the years.
    The function also calls clean_df to clean the dataframe
    and pairwise_correlation to plot the correlation.
    :return: df_dic, a dictionary where the keys are the years
            and the values are the corresponding dataframes
    """
    # Read all the files with the data
    file_list = glob.glob("paavo_data/*.csv")

    # Create a sorted list of the years: remove A-Öa-ö_.,:; /()\\-
    years_list = sorted({re.sub('[\D]+', '', y) for y in file_list})
    print(years_list)

    # Build a dictionary of DataFrames:
    # to each year, it is associated one DataFrame
    df_dic = {y: pd.DataFrame() for y in years_list}

    # Dataframe 2017 --> we'll get postal codes and areas from this
    for file in file_list:
        if '2017' in file:
            if df_dic['2017'].size == 0:
                df_dic['2017'] = pd.read_csv(file, sep=',', skiprows=0, encoding='iso-8859-1')
            else:
                # Open the file in a temporary dataframe
                temp = pd.read_csv(file, sep=',', skiprows=0, encoding='iso-8859-1')
                # Merge the temporary dataframe to the main one
                df_dic['2017'] = df_dic['2017'].join(temp, lsuffix='_caller')

    df_dic['2017'] = clean_df(df_dic['2017'])
    df_dic['2017'] = first_columns(df_dic['2017'])

    # print('-----------------------------\n2017:\n')
    # print(df_dic['2017'].head())
    # print(df_dic['2017'].columns)

    postalcodes_list = df_dic['2017']['Postal code'].values

    years_list.remove('2017')
    # Fill the DataFrames with the data from the correct files
    for file in file_list:
        for y in years_list:
            if df_dic[y].size == 0:
                df_dic[y]['Postal code'] = df_dic['2017']['Postal code'].copy()
                df_dic[y]['Area'] = df_dic['2017']['Area'].copy()
                # df_dic[y].set_index('Postal code', inplace=True)
            if y in file:
                # Open the file in a temporary dataframe
                temp = pd.read_csv(file, sep=',', skiprows=0, encoding='iso-8859-1')
                temp = clean_df(temp)
                temp = first_columns(temp)
                temp = data_format(temp)
                idx = pd.Index(temp['Postal code'].values)
                old_pc = list(set(idx) - set(postalcodes_list))
                temp = temp[~temp['Postal code'].isin(old_pc)]
                df_dic[y] = pd.concat([df_dic[y], temp.copy()], axis=1, sort=False).reindex(df_dic[y].index)

    sold_df = pd.DataFrame({'Sell price': list_sold()}, dtype=np.float64)
    rentARA_df = pd.DataFrame({'Rent price with ARA': list_rent()[0]}, dtype=np.float64)
    rentnoAra_df = pd.DataFrame({'Rent price without ARA': list_rent()[1]}, dtype=np.float64)

    for year, dfy in df_dic.items():
        # Here we add the columns 'Bus stops', 'Sold', 'Rented', 'Population density'
        # Therefore, the column 'Inhabitants total' becomes useless.
        # We can remove it after scaling
        dfy = clean_columns(dfy)
        dfy.drop(columns=['Postal code area', 'Postialue', 'Area_x', 'Area_y'], inplace=True, errors='ignore')
        dfy = data_format(dfy)
        dfy.reset_index(inplace=True)
        # Add bus stops
        dfy['Bus stops'] = add_buses()

        # Add population density
        dfy.drop(columns=['index'], inplace=True)
        dens_df = add_density(year=year, pclist=postalcodes_list)

        mydensitylist = []
        for pc in postalcodes_list:
            if pc in dens_df.keys():
                mydensitylist.append(dens_df[pc])
            else:
                mydensitylist.append(0)

        print(len(mydensitylist))
        dfy['Density'] = [0] * len(dfy.index)
        new_df = pd.DataFrame({'Density': mydensitylist})
        dfy.update(new_df)

        # Add avg selling prices in the last 12 months
        dfy['Sell price'] = [0] * len(dfy.index)
        # sold_df = pd.DataFrame({'Sell price': list_sold()}, dtype=np.float64)
        dfy.update(sold_df)

        # Add avg renting prices with ARA in the last 12 months
        dfy['Rent price with ARA'] = [0] * len(dfy.index)
        # rentARA_df = pd.DataFrame({'Rent price with ARA': list_rent()[0]}, dtype=np.float64)
        dfy.update(rentARA_df)

        # Add avg renting prices without ARA in the last 12 months
        dfy['Rent price without ARA'] = [0] * len(dfy.index)
        # rentnoAra_df = pd.DataFrame({'Rent price without ARA': list_rent()[1]}, dtype=np.float64)
        dfy.update(rentnoAra_df)

        print('FINALLY, ' + year + ':')
        # print(dfy.head())
        # print(dfy.columns)
        print(dfy.shape)
        # print(dfy.describe())

    return df_dic


def getIndexPositions(listOfElements, element):
    """
    Returns the indexes of all occurrences of the given element in the list listOfElements
    :param listOfElements: a list
    :param element: the element to find
    :return: list of indexes
    """
    indexPosList = []
    indexPos = 0
    while True:
        try:
            # Search for item in list from indexPos to the end of list
            indexPos = listOfElements.index(element, indexPos)
            # Add the index position in list
            indexPosList.append(indexPos)
            indexPos += 1
        except ValueError as e:
            break

    return indexPosList


def scale(df):
    """
    This function scales all the attributes according to
    their properties.
    :param df: the dataframe to scale
    """
    columns_with_year = df.columns

    # Strip out the year from every column
    # The columns with the same content have the same name, regardless of the year
    columns_without_year = [re.sub(r" \d{4}", "", title) for title in columns_with_year]
    df.columns = columns_without_year

    labels_scale_by_labour_force = {
        "Employed, ", "Unemployed, "
    }
    labels_scale_by_outside_labour = {
        "Children aged 0 to 14, ", "Pensioners, ", "Others, "
    }

    # Labels scaled by labour force and outside labour force are scaled first
    # labour force and outside labour force are later modified
    for key in columns_without_year:
        if key in labels_scale_by_labour_force:
            df[key] = df[key] / df["Labour force, "]
        elif key in labels_scale_by_outside_labour:
            df[key] = df[key] / df["Persons outside the labour force, "]

    labels_scale_by_inhabitants = {
        "Males, ", "Females, ", "Average age of inhabitants, ",
        "0 - 2 years, ", "3 - 6 years, ",
        "7 - 12 years, ", "13 - 15 years, ", "16 - 17 years, ", "18 - 19 years, ", "20 - 24 years, ",
        "25 - 29 years, ", "30 - 34 years, ", "35 - 39 years, ", "40 - 44 years, ", "45 - 49 years, ",
        "50 - 54 years, ", "55 - 59 years, ", "60 - 64 years, ", "65 - 69 years, ", "70 - 74 years, ",
        "75 - 79 years, ", "80 - 84 years, ", "85 years or over, ", "Aged 18 or over, total, ",
        "Basic level studies, ", "With education, total, ", "Matriculation examination, ",
        "Vocational diploma, ", "Academic degree - Lower level university degree, ",
        "Academic degree - Higher level university degree, ",
        "Inhabintants belonging to the lowest income category, ",
        "Inhabitants belonging to the middle income category, ",
        "Inhabintants belonging to the highest income category, ",
        "Labour force, ", "Persons outside the labour force, ", "Students, "
    }
    labels_scale_by_households = {
        "Average size of households, ", "Young single persons, ", "Young couples without children, ",
        "Households with children, ", "Households with small children, ",
        "Households with children under school age, ", "Households with school-age children, ",
        "Households with teenagers, ", "Adult households, ", "Pensioner households, ",
        "Households living in owner-occupied dwellings, ", "Households living in rented dwellings, ",
        "Households living in other dwellings, ", "Households belonging to the lowest income category, ",
        "Households belonging to the middle income category, ",
        "Households belonging to the highest income category, "
    }
    labels_scale_by_buildings = {
        "Free - time residences, ", "Other buildings, ", "Residential buildings, "
    }
    labels_scale_by_dwellings = {
        "Dwellings in small houses, ", "Dwellings in blocks of flats, "
    }

    # Scale the four sets above
    for key in columns_without_year:
        if key in labels_scale_by_inhabitants:
            df[key] = df[key] / df["Inhabitants, total, "]
        elif key in labels_scale_by_households:
            df[key] = df[key] / df["Households, total, "]
        elif key in labels_scale_by_buildings:
            df[key] = df[key] / df["Buildings, total, "]
        elif key in labels_scale_by_dwellings:
            df[key] = df[key] / df["Dwellings, "]

    labels_combine_scale_by_inhabitants = {
        "Primary production, ", "Processing, ", "Services, "
    }
    labels_combine_scale_by_workplaces = {
        "A Agriculture, forestry and fishing, ",
        "B Mining and quarrying, ", "C Manufacturing, ", "D Electricity, gas, steam and air conditioning supply, ",
        "E Water supply; sewerage, waste management and remediation activities, ", "F Construction, ",
        "G Wholesale and retail trade; repair of motor vehicles and motorcycles, ", "H Transportation and storage, ",
        "I Accommodation and food service activities, ", "J Information and communication, ",
        "K Financial and insurance activities, ", "L Real estate activities, ",
        "M Professional, scientific and technical activities, ", "N Administrative and support service activities, ",
        "O Public administration and defence; compulsory social security, ", "P Education, ",
        "Q Human health and social work activities, ", "R Arts, entertainment and recreation, ",
        "S Other service activities, ", "T Activities of households as employers; " +
        "undifferentiated goods- and services-producing activities of households for own use, ",
        "U Activities of extraterritorial organisations and bodies, "
    }

    # Sum the selected attributes for each area with the similar postal code
    # In other words, postal codes with the same first 3 digits
    df_combine = df[
        ["Postal code", "Inhabitants, total, ", "Workplaces, "] +
        list(labels_combine_scale_by_inhabitants) + list(labels_combine_scale_by_workplaces)
    ].copy()
    df_combine["Postal code"] = df_combine["Postal code"].map(lambda x: x[:-2])
    df_combine = df_combine.groupby("Postal code", as_index=False).agg("sum")

    # Scale the combined columns
    for key in df_combine.columns:
        if key in labels_combine_scale_by_inhabitants:
            df_combine[key] = df_combine[key] / df_combine["Inhabitants, total, "]
        elif key in labels_combine_scale_by_workplaces:
            df_combine[key] = df_combine[key] / df_combine["Workplaces, "]

    # Replace the combined and scaled values into the original dataframe
    for _, row in df_combine.iterrows():
        code = row["Postal code"]
        df_rows = df["Postal code"].str.startswith(code)
        # Postal code, Inhabitants and workplaces remain unchanged
        columns = row.index.drop(["Postal code", "Inhabitants, total, ", "Workplaces, "])
        for column in columns:
            df.loc[df_rows, column] = row[column]


def add_buses():
    """
    Open the file and return the column to add to the dataframe
    :return: list of values as a pandas Series
    """
    bus_df = pd.read_csv(Path('temp/') / 'bus.tsv', sep='\t', usecols=['Bus stops'])
    return bus_df['Bus stops'].copy()


def add_density(year, pclist):
    """
    Open the file and return the column to add to the dataframe.
    There is no density 2012. Where asking for 2012, the column 2013
    will be returned.
    :param year: string, the year to read
    :param pclist: list of strings, each element is a postal code to take
    :return: list of values as a dictionary
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
        print(dens_df[col_name].head())
        return dens_df.copy().set_index('Postal code').to_dict()[col_name]


def get_tsv_files(scaled=False):
    """
    Call bulk_load and save each year on a file
    :param scaled: bool, if true, the data are scaled to percentages
    :return: None
    """
    df_dic = bulk_load()
    if scaled:
        # Read all the files with the data
        file_list = glob.glob("paavo_data/*.csv")

        # Create a sorted list of the years: remove A-Öa-ö_.,:; /()\\-
        years_list = sorted({re.sub('[\D]+', '', y) for y in file_list})

        # Remove because of missing data (at least for now)
        # years_list.remove('2012')
        # years_list.remove('2016')
        # years_list.remove('2017')

    for y, df in df_dic.items():
        do_we_have = ['Density', 'Surface', 'Inhabitants, total', 'Labour force', 'Services', 'Area',
                      'Average income', 'Average size of households', 'Average age']
        for sub in do_we_have:
            print(y, sub, any(sub in cols for cols in df.columns))
        print('--------')

        if scaled: scale(df)

        df.fillna(0, inplace=True)
        filename = 'df'+str(y)+'.tsv'
        df.to_csv(Path('dataframes') / filename, sep='\t', index=False, encoding='utf-8')


if __name__ == '__main__':
    get_tsv_files(scaled=False)