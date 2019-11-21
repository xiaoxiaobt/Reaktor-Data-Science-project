import pandas as pd

name_paavo_dataframe = "./dataframes/final_dataframe.tsv"  # Require UTF-8, Tab-seperated, name of postal code column ='id'
paavo_df = pd.read_table(name_paavo_dataframe, dtype={"Postal code": str})  # The dtype CANNOT be removed!


def zip_name_dict():
    zip_name_dict = dict(zip(paavo_df['Postal code'], paavo_df['Area']))
    return zip_name_dict


def dropdown_dict():
    return [{'label': i + ", " + zip_name_dict()[i], 'value': i} for i in paavo_df['Postal code']]


def get_attribute(postalcode="02150", column=None):
    """
    Read from the data frame: find the value of the given column for the given postal code.
    :param postalcode: str, a valid postal code
    :param column: str, a valid complete column name
    :return: a string with the value of the column, or raise Exception
    """
    if column is not None:
        return str(paavo_df[paavo_df['Postal code'] == postalcode][column].values[0])
    else:
        raise Exception


def radar_attribute(postalcode="02150", column=None):
    """
    Read from the data frame: find the value of the given column for the given postal code,
    and normalize it from 0 to 1 if needed.
    :param postalcode: str, a valid postal code
    :param column: str, a valid complete column name
    :return: a float with the value of the column, or raise Exception
    """
    value = float(get_attribute(postalcode=postalcode, column=column))
    max = paavo_df[column].max()
    min = paavo_df[column].min()
    if "scaled" in column:
        return value
    else:
        return (value-min)/(max-min)


def format_2f(string):
    """
    Format a number to show only 2 decimal digits.
    :param string: the string with the number
    :return: the formatted string
    """
    return "{:.2f}".format(float(string))