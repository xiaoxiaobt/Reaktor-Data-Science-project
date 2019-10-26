import pandas as pd
import numpy as np


def toutf8():
    FILE_NAME = "./temp/industry_2008.csv"
    OUTPUT_NAME = "./temp/industry_2008_u.csv"
    file = open(FILE_NAME, encoding='iso-8859-1')
    file_write = open(OUTPUT_NAME, "w", encoding='utf-8')
    [file_write.write(_) for _ in file.readlines()]


def industry_data_cleaner():
    """Find names of all types of industries"""
    storage = open("./temp/modified_type.tsv", 'w+', encoding='utf-8')
    file = open('./temp/industry_2008.csv', 'r', encoding='iso-8859-1')
    file.readline()
    for line in file.readlines():
        line = line.rstrip('\n').split('\t')[1:]
        line[0] = " ".join(line[0].split()[1:]).rstrip("\"")
        storage.write(line[0] + "\t" + line[1] + '\n')
    storage.close()
    file.close()


def add_id():
    """This function add "id" feature to .json file. The id feature works as identifier (key) to access
     corresponding shape, only works for postinumeroalueet 2016.json"""
    file = open("./data/postinumeroalueet 2016.json", "r")
    file_write = open("./data/idchanged.json", "w")
    wait_4_write = False
    number = 0
    for line in file.readlines():
        if '"posti_alue"' in line:
            number = line.split(": \"")[1].split("\",")[0]
            wait_4_write = True
            file_write.write(line)
        elif '"namn"' in line:
            continue
        elif '"kuntanro"' in line:
            continue
        elif '"description"' in line:
            continue
        elif '"vuosi"' in line:
            continue
        elif wait_4_write and ("}" in line):
            file_write.write(line.rstrip("\n") + "," + "\n")
            file_write.write('            "id": "' + number + '"\n')
            wait_4_write = False
        else:
            file_write.write(line)


def change_precision():
    return
    file = open("./data/idchanged.json", "r")
    PRECISION = 4
    file_write = open("./temp/map_w_id_precision.json", "w")
    for line in file.readlines():
        if "                                    " in line:
            if ',' in line:
                temp = str(round(float(line.strip().split(',')[0]), PRECISION)) + ','
            else:
                temp = str(round(float(line.strip().split(',')[0]), PRECISION))
            file_write.write("                                    " + temp + '\n')
        else:
            file_write.write(line)


def fix_dataframe():
    """Fix the dataframe to desired format: UTF-8, Tab-seperated, replace '..' with np.nan, changed column name to id"""
    # Reformat all data from semicolon-separated value to tsv with encoding utf-8
    input_filename = "./data/paavo_9_koko.csv"
    df = pd.read_csv(input_filename, delimiter=";", encoding='iso-8859-1', header=1)
    df.to_csv("./data/paavo_9_koko.tsv", sep="\t", encoding="utf-8", index=False)
    # Remove the data for whole Finland
    df = pd.read_csv("./data/paavo_9_koko.tsv", delimiter="\t")
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
    df_neighbour = pd.read_csv("./temp/neighbours.csv", encoding='iso-8859-1', dtype={"NEIGHBORS": str})
    df_neighbour.sort_values(by="posti_alue", inplace=True)
    df_neighbour.reset_index(inplace=True)
    df.insert(loc=2, column='neighbour', value=df_neighbour.NEIGHBORS)
    # Save file
    df.to_csv("./data/paavo_9_koko.tsv", sep="\t", encoding="utf-8", index=False)
