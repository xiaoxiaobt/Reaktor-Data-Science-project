import json
import pandas as pd
import numpy as np
import os


def toutf8():
    FILE_NAME = "./temp/industry_2008.csv"
    OUTPUT_NAME = "./temp/industry_2008_u.csv"
    file = open(FILE_NAME, encoding='iso-8859-1')
    file_write = open(OUTPUT_NAME, "w", encoding='utf-8')
    file_write.writelines(file.readlines())
    file.close()
    file_write.close()


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
    """
    This function add "id" feature to .json file. The id feature works as identifier (key) to access
     corresponding shape, only works for postinumeroalueet 2016.json
    """
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
            file_write.write(line.rstrip("\n") + ",\n")
            file_write.write('            "id": "' + number + '"\n')
            wait_4_write = False
        else:
            file_write.write(line)
    file.close()
    file_write.close()


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


def add_id_for_geojson():
    file = open("./data/finland_2016_p4_utf8_simp.geojson", "r")
    file_write = open("./data/finland_2016_p4_utf8_simp_wid.geojson", "w+")
    for line in file.readlines():
        if 'properties": { "posti_alue' in line:
            line = line.replace('properties": { "posti_alue', 'id')
            line = line.replace('" }, "geometry"', '", "geometry"')
        file_write.write(line)
    file.close()
    file_write.close()


def generate_requirements():
    os.system("pip freeze>requirements.txt")
    file = open("requirements.txt", "r+")
    lines = file.readlines()
    for x in range(len(lines)):
        lines[x] = lines[x].split("==")[0] + "\n" if "ywin" not in lines[x] else ""
    file.close()
    file = open("requirements.txt", "w")
    file.writelines(lines)
    file.write("gunicorn")
    file.close()


def feature_selection(list_of_post_code=None):
    if list_of_post_code is None:
        list_of_post_code = ["02150", "76120", "00900", "33720"]
    file = open("./data/finland_2016_p4_utf8_simp_wid.geojson", 'r')
    lines = file.readlines()
    file.close()
    match = []
    [[match.append(line.rstrip(",\n")) for line in lines if item in line] for item in list_of_post_code]
    selected = open("./data/selected.geojson", 'w')
    head = '{\n"type": "FeatureCollection", \n"name": "selected", \n"crs": {"type": "name", ' \
           '"properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}, \n"features": [\n'
    tail = "\n]\n}"
    selected.writelines(head)
    selected.writelines(",\n".join(match))
    selected.writelines(tail)
    selected.close()
    alltext = head + ",\n".join(match) + tail
    polygons = json.loads(alltext)
    # polygons = json.load(open("./data/selected.geojson", "r"))
    # print(polygons)
    return polygons


def find_num_of_points():
    if os.name == 'nt':
        print("This part cannot run on Windows. ")
        return
    from shapely.geometry import Point
    from shapely.geometry.polygon import Polygon
    FILE_NAME = "./data/paavo_9_koko.csv"
    postal_code = pd.read_table("FILE_NAME", 'r').id


def main():
    try:
        eval(input("Input the name of function you would like to execute, without the bracket:\n").lower() + "()")
        print("Executed successfully.")
    except IOError:
        print("Function name not found. Please check your input.")


if __name__ == "__main__":
    main()
