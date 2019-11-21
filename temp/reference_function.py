import pandas as pd

name_paavo_dataframe = "./dataframes/final_dataframe.tsv"  # Require UTF-8, Tab-seperated, name of postal code column ='id'
paavo_df = pd.read_table(name_paavo_dataframe, dtype={"Postal code": str})  # The dtype CANNOT be removed!


def zip_name_dict():
    zip_name_dict = dict(zip(paavo_df['Postal code'], paavo_df['Area']))
    return zip_name_dict


def dropdown_dict():
    return [{'label': i + ", " + zip_name_dict()[i], 'value': i} for i in paavo_df['Postal code']]


def get_attribute(postalcode="02150", column=None):
    if column is not None:
        return str(paavo_df[paavo_df['Postal code'] == postalcode][column].values[0])
    else:
        raise Exception
