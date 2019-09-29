# Collecting data into dataframes based on the year the datafile shows
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt


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
    to_drop=['Postal code area', 'Postialue']
    for td in to_drop:
        if td in df.columns:
            df.drop(columns=td, inplace=True)

    # Replace missing values with 0
    df.replace({'..': 0, '.': 0}, inplace=True)

    # Convert each column to the correct format
    for key in df.columns:
        if key == 'Postal code' or key == 'Area':
            df[key] = df[key].astype('object')
        else:
            df[key] = df[key].astype('float')

    # Print a summary of the dataframe
    print(df.describe())
    print(df.shape)

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
    and organizes them into dataframes accordin to the years.
    The function also calls clean_df to clean the dataframe
    and pairwise_correlation to plot the correlation.
    :return: df_dic, a dictionary where the keys are the years
            and the values are the corresponding dataframes
    """
    # Read all the files with the data
    file_list = glob.glob("paavo_data/*.csv")

    # Create a sorted list of the years
    years_list = sorted({re.sub('[A-Öa-ö_.,:; ()\\-]+', '', y) for y in file_list})

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
        # Plot pairwise correlation
        # pairwise_correlation(df)

    return df_dic