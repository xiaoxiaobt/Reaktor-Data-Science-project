# Collecting data into dataframes based on the year the datafile shows
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict


def drop_columns(df):
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

    # Count columns with same name
    count = defaultdict(int)
    for col in new_columns.values():
        count[col] += 1

    # Collect columns to delete
    for col, num in count.items():
        if num >= 2:
            safecopy = df[col].values[:, 0]
            df.drop(columns=df[col], inplace=True)
            df[col] = safecopy

    return df


def clean_df(df):
    """
    This function cleans the dataframe, by dropping the row 0 (Finland),
    splitting the column "Postal code area" into Postal code (the numerical postal code)
    and Area (the name of the area), dropping remaining duplicate columns,
    replacing missing values with 0, and finally converting each column to
    the correct format.
    :param df: the dataframe to clean
    :return: the cleaned dataframe
    """
    # Drop row 0: Finland
    df.drop(index=0, inplace=True)

    # Rename the first column
    df.rename(columns={df.columns[0]: "Postal code"}, inplace=True)

    # Duplicate the first column and add it as the second column
    df.insert(1, 'Area', df['Postal code'])

    # Strip out numbers from the content of the second column:
    # only the name of the area will remain.
    content = df["Area"]
    content = content.apply(lambda x: re.sub('[0-9_]+', '', x))
    df["Area"] = content

    # Strip out the letters and symbols from the content of the first column:
    # only the postal code, in numerical form, will remain.
    content = df["Postal code"]
    content = content.apply(lambda x: re.sub('[A-Öa-ö_ ()\\-]+', '', x))
    df["Postal code"] = content

    # Drop unnecessary columns that might have been copied while building the dataframe
    to_drop = ['Postal code area', 'Postialue']
    for td in to_drop:
        if td in df.columns:
            df.drop(columns=td, inplace=True)

    df = drop_columns(df)

    # Replace missing values with 0
    df.replace({'..': 0, '.': 0}, inplace=True)

    # Convert each column to the correct format
    for key in df.columns:
        if key == 'Postal code' or key == 'Area':
            df[key] = df[key].astype('object')
        else:
            df[key] = df[key].astype('float')

    # Print a summary of the dataframe
    # print(df.describe())
    # print(df.shape)

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

    # Create a sorted list of the years
    years_list = sorted({re.sub('[A-Öa-ö_.,:; /()\\-]+', '', y) for y in file_list})

    # Remove because of missing data (at least for now)
    years_list.remove('2012')
    years_list.remove('2016')
    years_list.remove('2017')

    # Build a dictionary of DataFrames:
    # to each year, it is associated one DataFrame
    df_dic = {y: pd.DataFrame() for y in years_list}

    # Fill the DataFrames with the data from the correct files
    for file in file_list:
        for y in years_list:
            if y in file:
                if df_dic[y].size == 0:
                    df_dic[y] = pd.read_csv(file, sep=',', skiprows=0, encoding='iso-8859-1')
                else:
                    # Open the file in a temporary dataframe
                    temp = pd.read_csv(file, sep=',', skiprows=0, encoding='iso-8859-1')
                    # Merge the temporary dataframe to the main one
                    df_dic[y] = df_dic[y].join(temp, lsuffix='_caller')
                    # Try to locate eventual duplicated columns
                    df_dic[y] = df_dic[y].loc[:, ~df_dic[y].columns.duplicated()]

    for df in iter(df_dic.values()):
        # Clean each dataframe
        df = clean_df(df)
        scale(df)
        # Plot pairwise correlation
        # pairwise_correlation(df)

    return df_dic


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


bulk_load()
