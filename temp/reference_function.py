import pandas as pd

name_paavo_dataframe = "./data/paavo_9_koko.tsv"  # Require UTF-8, Tab-seperated, name of postal code column ='id'
paavo_df = pd.read_table(name_paavo_dataframe, dtype={"id": str})  # The dtype CANNOT be removed!


def zip_name_dict():
    zip_name_dict = dict(zip(paavo_df.id, paavo_df.location))
    return zip_name_dict


def dropdown_dict():
    return [{'label': i + ", " + zip_name_dict()[i], 'value': i} for i in paavo_df.id]
