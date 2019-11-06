import json
import numpy as np
from random import random


def generate_random_color_dict(code_list):
    color_dict = {}
    for code in code_list:
        color_dict[code] = [random(), random()]
    return color_dict


def extract_code_list():
    # extract a list of numbers in the same order as in the GeoJSON file
    filename = 'Paavo-postinumeroalueet 2019.geojson'
    with open(filename) as file:
        feature_collection = json.load(file)
    code_list = []
    for feature in feature_collection['features']:
        code = feature['properties']['posti_alue']
        code_list.append(code)
    return code_list


def convert_color(color):
    # convert a color, that is either a number of list of one to three numbers
    # all numbers should be normalized to [0, 1]
    if not isinstance(color, list):
        r = color
        g = 0.0
        b = 0.0
    else:
        r = color[0] if len(color) > 0 else 0.0
        g = color[1] if len(color) > 1 else 0.0
        b = color[2] if len(color) > 2 else 0.0
    return [r, g, b, 1.0]


def convert_color_dict(code_list, color_dict):
    # convert a dictionary from postal code to color (as defined in convert_color)
    # to a list of colors, in the order of the code list
    color_list = list(map(convert_color, map(lambda code: color_dict[code], code_list)))
    return color_list


def main():
    code_list = extract_code_list()
    color_dict = generate_random_color_dict(code_list)
    color_list = convert_color_dict(code_list, color_dict)

    color_array = np.empty(len(color_list), dtype='4<f4')
    for i, color in enumerate(color_list):
        color_array[i] = color

    color_array.tofile('map_color_table.dat')


if __name__ == '__main__':
    main()
