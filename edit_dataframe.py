import pandas as pd
import numpy as np


def main():
    """Fix the dataframe to desired format: UTF-8, Tab-seperated, replace '..' with np.nan, changed column name to id"""

    # Reformat all data from semicolon-separated value to tsv with encoding utf-8
    input_filename = "paavo_9_koko.csv"
    df = pd.read_csv(input_filename, delimiter=";", encoding='iso-8859-1', header=1)
    df.to_csv("paavo_9_koko.tsv", sep="\t", encoding="utf-8", index=False)
    # Remove the data for whole Finland
    df = pd.read_csv("paavo_9_koko.tsv", delimiter="\t")
    df.drop(index=0, inplace=True)
    # Split ["Postal code area"] to ["id"] and ["location"]
    col_location = df["Postal code area"].apply(lambda x: x.split(" ")[1])
    col_id = df["Postal code area"].apply(lambda x: x.split(" ")[0])
    df.insert(loc=0, column='location', value=col_location)
    df.insert(loc=0, column='id', value=col_id)
    del df["Postal code area"]
    # Replace all ".." value
    replacing_value = np.nan  # Or other values
    df.replace("..", replacing_value)
    # Add neighbour postal codes
    df_neighbour = pd.read_csv("neighbours.csv", encoding='iso-8859-1', dtype={"NEIGHBORS": str})
    df_neighbour.sort_values(by="posti_alue", inplace=True)
    df_neighbour.reset_index(inplace=True)
    df.insert(loc=2, column='neighbour', value=df_neighbour.NEIGHBORS)
    # Save file
    df.to_csv("paavo_9_koko.tsv", sep="\t", encoding="utf-8", index=False)
    df.to_csv("paavo_9_kokoT.csv", sep="\t", encoding="utf-8", index=False)


main()
