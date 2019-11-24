import json
import pandas as pd
import numpy as np
import os
import requests
import random
import re
from bs4 import BeautifulSoup


def toutf8(input_name="./temp/industry_2008.csv", output_name="./temp/industry_2008_u.csv"):
    file = open(input_name, encoding='iso-8859-1')
    file_write = open(output_name, "w", encoding='utf-8')
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
    DEPRECATED
    This function add "id" feature to .json file. The id feature works as identifier (key) to access
     corresponding shape, only works for postinumeroalueet 2016.json
    """
    return
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
    output_filename = "./data/paavo_9_koko.tsv"
    df = pd.read_csv(input_filename, delimiter=";", encoding='iso-8859-1', header=1)
    df.to_csv(output_filename, sep="\t", encoding="utf-8", index=False)
    # Remove the data for whole Finland
    df = pd.read_csv(output_filename, delimiter="\t")
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
    df_neighbour = pd.read_csv("./temp/neighbours.csv", encoding='iso-8859-1', dtype={"NEIGHBORS": object})
    df_neighbour.sort_values(by="posti_alue", inplace=True)
    df_neighbour.reset_index(inplace=True)
    df.insert(loc=2, column='neighbour', value=df_neighbour.NEIGHBORS)
    # Save file
    df.to_csv("output_filename", sep="\t", encoding="utf-8", index=False)


def add_id_for_geojson():
    file = open("./data/finland_2019_p4_utf8_simp.geojson", "r")
    file_write = open("./data/finland_2019_p4_utf8_simp_wid.geojson", "w+")
    for line in file.readlines():
        if 'properties": { "posti_alue' in line:
            line = line.replace('properties": { "posti_alue', 'id').replace('" }, "geometry"', '", "geometry"')
        file_write.write(line)
    file.close()
    file_write.close()


def generate_requirements():
    os.system("pip freeze>requirements.txt")
    file = open("requirements.txt", "r+")
    lines = file.readlines()
    for x in range(len(lines)):
        if "ywin" in lines[x]:
            lines[x] = ""
        elif "pygobject" in lines[x]:
            lines[x] = ""
        else:
            lines[x] = lines[x].split("==")[0] + "\n"
    file.close()
    with open("requirements.txt", "w") as file:
        file.writelines(lines)
        file.write("gunicorn")


def feature_selection(list_of_post_code=None):
    if list_of_post_code is None:
        list_of_post_code = ["02150", "76120", "00900", "33720"]
    file = open("./data/finland_2019_p4_utf8_simp_wid.geojson", 'r')
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
    all_text = head + ",\n".join(match) + tail
    polygons = json.loads(all_text)
    # polygons = json.load(open("./data/selected.geojson", "r"))
    # print(polygons)
    return polygons


def read_stops():
    file = pd.read_csv("./data/stops.txt", sep=",", usecols={"stop_lat", "stop_lon"})
    dic = zip(file.stop_lon, file.stop_lat)
    result = [(float(line[1]), float(line[0])) for line in dic]
    print(find_num_of_points(result))


def find_num_of_points(points):
    if os.name == 'nt':
        print("This part cannot be run on Windows. ")
        return
    else:
        print("This algorithm should work on your computer. Remember to remove the exec() function call. ")
        from shapely import wkt
        from shapely.geometry import Point
    point_dict = dict()
    polygon_dict = dict()
    FILE_NAME = "./data/zip_polygon.csv"
    with open(FILE_NAME) as f:
        for line in f.readlines():
            polygon, code = [x.strip("\"") for x in line.strip().split("\t")]
            polygon_dict[code] = wkt.loads(polygon)
            point_dict[code] = 0
    # If the input is a list of points:
    if isinstance(points, list):
        for current, code in enumerate(polygon_dict.keys()):
            print("Progress: {:d}\t/ 3026".format(current))
            for y, x in points:
                if polygon_dict[code].contains(Point(x, y)):
                    point_dict[code] += 1
    return point_dict


def get_amount_of_service(zip="02150"):
    """
    Get number of services of a postal code
    :param zip: zip_code (str)
    :return:  dictionary("service_name" -> number)
    """
    service_list = ["ruokakauppa", "ravintola", "kirjasto", "terveys", "kuntosali", "hotelli", "pubit ja baarit"]
    counts = dict()
    # random.shuffle(service_list)
    pattern = r"-->([0-9]+)<!--"
    for service in service_list:
        URL = "https://www.finder.fi/search?what={:s}%20{:s}&type=company".format(service, zip)
        soup = BeautifulSoup(requests.get(URL).content, features="html.parser")
        main_content = soup.find('span', attrs={'class': 'SearchResultList__TabBar__Count'})
        num = re.findall(pattern, str(main_content))[0]
        counts[service] = int(num)
        print(service, num)
    return counts


def find_all_transportation():
    """
    This function finds all stations in finland
    Bus, Tram and Ferry -> DigiTransit api
    https://api.digitransit.fi/graphiql/finland?query=%257B%2520%250A%2520%2520stations%2520%257B%250A%2520%2520%2520%2520name%250A%2520%2520%2520%2520lat%250A%2520%2520%2520%2520lon%250A%2520%2520%2520%2520vehicleMode%250A%2520%2520%257D%250A%257D
    Train -> DigiTraffic website
    https://www.digitraffic.fi/rautatieliikenne/#junien-tiedot-trains
    Metro -> Hand-scraped, this is the first time I am glad that Finland has such a short metro lane LMAO
    https://www.google.fi/maps/

    Data have been pre-processed
    """

    # Calculate data from Bus, Tram and Ferry
    busTramFerry_info = './data_transportation/bus_tram_ferry_stations_oneline.json'
    file_bus = "./data_transportation/bus_stations.tsv"
    file_tram = "./data_transportation/tram_stations.tsv"
    file_ferry = "./data_transportation/ferry_stations.tsv"
    write_bus = open(file_bus, "w+")
    write_ferry = open(file_ferry, "w+")
    write_tram = open(file_tram, "w+")
    pattern = r'"lat":([0-9.]*),"lon":([0-9.]*),'
    with open(busTramFerry_info) as f:
        lines = f.readlines()
        for line in lines:
            if "BUS" in line:
                lat, lon = re.findall(pattern, line)[0]
                write_bus.write(lat + '\t' + lon + '\n')
            elif "TRAM" in line:
                lat, lon = re.findall(pattern, line)[0]
                write_tram.write(lat + '\t' + lon + '\n')
            elif "FERRY" in line:
                lat, lon = re.findall(pattern, line)[0]
                write_ferry.write(lat + '\t' + lon + '\n')

    # Calculate data from Train
    train_info = './data_transportation/train_stations_oneline.json'
    file_train = "./data_transportation/train_stations.tsv"
    write_train = open(file_train, "w+")
    pattern = r',"longitude":([0-9.]*),"latitude":([0-9.]*)}'
    with open(train_info) as f:
        lines = f.readlines()
        for line in lines:
            if "true" in line:  # Then the station is passenger station
                lat, lon = re.findall(pattern, line)[0]
                write_train.write(lat + '\t' + lon + '\n')


def tax_remove_white_space():
    write_new = open("municipality_tax.csv", "w+")
    with open("./data/municipality_tax.tsv") as f:
        lines = f.readlines()
        for line in lines:
            name, tax = line.split("\t")
            write_new.write(name.strip() + "\t" + tax)


def calculate_transportation_df():
    train_raw = pd.read_csv("./data_transportation/train_stations.tsv", sep="\t"), "Train"
    metro_raw = pd.read_csv("./data_transportation/metro_stations.tsv", sep="\t"), "Metro"
    ferry_raw = pd.read_csv("./data_transportation/ferry_stations.tsv", sep="\t"), "Ferry"
    tram_raw = pd.read_csv("./data_transportation/tram_stations.tsv", sep="\t"), "Tram"
    bus_raw = pd.read_csv("./data_transportation/bus_stations.tsv", sep="\t"), "Bus"
    file_raw_list = [metro_raw, train_raw, ferry_raw, tram_raw, bus_raw]
    combined_dict = dict()
    for file, name_of_file in file_raw_list:
        lis = list(zip(file["lat"], file["lon"]))
        dic = find_num_of_points(lis)
        print(str(sum(dic.values())) + " points classified in file " + name_of_file)
        df = pd.DataFrame.from_dict(dic, orient='index', columns=[name_of_file])
        combined_dict[name_of_file] = df
    final_df = pd.concat(combined_dict.values(), axis=1)
    final_df.to_csv("./data_transportation/final_transportation.tsv", sep="\t")


def calculate_tax_rate_df():
    zip_municipality = pd.read_csv("./data/zip_municipality.tsv", sep="\t", dtype={"Postinumeroalue": object})
    municipality_tax = pd.read_csv("./data/municipality_tax.tsv", sep="\t")
    zip_municipality_dict = dict(zip(zip_municipality['Postinumeroalue'], zip_municipality['Kunnan nimi']))
    municipality_tax_dict = dict(zip(municipality_tax['Municipality'], municipality_tax['Tax']))
    zip_tax = dict()
    for key in zip_municipality['Postinumeroalue']:
        zip_tax[key] = municipality_tax_dict[zip_municipality_dict[key]]
    zip_df = pd.DataFrame.from_dict(zip_tax, orient='index', columns=["Tax"])
    zip_df.to_csv("./data/final_tax.tsv", sep="\t")


def main():
    try:
        eval(input("Input the name of function you would like to execute: \n").lower().strip())
        print("Executed successfully.")
    except Exception:
        print("Function name not found. Please check your input.")


if __name__ == "__main__":
    main()
