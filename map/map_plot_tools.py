import math
import re
import numpy as np
import pandas as pd
import sys


def build_map_plot():
    return {
        'age_data': build_age_plot(),
        'water_data': build_water_plot(),
        'forest_data': build_forest_plot(),
        'cluster_data': build_cluster_plot()
    }


def build_and_save_map_plot():
    map_plot = build_map_plot()
    np.savez_compressed('map_plot.npz', **map_plot)


def load_map_plot():
    map_plot = np.load('map_plot.npz')
    if sys.byteorder == 'big':
        for it in map_plot.values():
            it.byteswap()
    return map_plot


def to_linear_rgb(s_rgb):
    def f(x):
        return x / 12.92 if x <= 0.04045 else math.pow((x + 0.055) / 1.055, 2.4)
    return np.array([f(x) for x in s_rgb])


def to_s_rgb(linear_rgb):
    def f(x):
        return x * 12.92 if x <= 0.0031308 else math.pow(1.055 * x, 1 / 2.4) - 0.055
    return np.array([f(x) for x in linear_rgb])


def blend_linear_rgb(linear_rgb_array, weights=None):
    return np.average(linear_rgb_array, axis=0, weights=weights)


def blend_s_rgb(s_rgb_array, weights=None):
    linear_rgb_array = np.array([to_linear_rgb(s_rgb) for s_rgb in s_rgb_array])
    return to_s_rgb(blend_linear_rgb(linear_rgb_array, weights))


def build_color_data_min_max(source_data, color_min, color_max, transform=lambda x: x):
    source_min = np.nanmin(source_data)
    source_max = np.nanmax(source_data)

    def f(val):
        if np.isnan(val).any():
            return [1.0, 1.0, 1.0]
        weight = (val - source_min) / (source_max - source_min)
        weight = transform(weight)
        return blend_s_rgb([color_min, color_max], weights=[1 - weight, weight])

    color_data_array = np.array([f(val) for val in source_data])
    color_data = np.empty(color_data_array.shape[0], dtype='4<f4')
    for i in range(color_data_array.shape[0]):
        d = color_data_array[i]
        color_data[i] = d[0], d[1], d[2], 1.0

    return color_data


def build_cluster_plot():
    final_df = pd.read_csv('../dataframes/final_dataframe.tsv', sep='\t')

    cluster = final_df['label'].to_numpy()

    distinct_colors = '''
        darkgray #a9a9a9
        darkslategray #2f4f4f
        darkolivegreen #556b2f
        olivedrab #6b8e23
        sienna #a0522d
        maroon2 #7f0000
        midnightblue #191970
        slategray #708090
        cadetblue #5f9ea0
        green #008000
        mediumseagreen #3cb371
        rosybrown #bc8f8f
        rebeccapurple #663399
        darkkhaki #bdb76b
        peru #cd853f
        steelblue #4682b4
        navy #000080
        chocolate #d2691e
        yellowgreen #9acd32
        indianred #cd5c5c
        limegreen #32cd32
        goldenrod #daa520
        purple2 #7f007f
        darkseagreen #8fbc8f
        maroon3 #b03060
        mediumturquoise #48d1cc
        orangered #ff4500
        darkorange #ff8c00
        gold #ffd700
        mediumvioletred #c71585
        mediumblue #0000cd
        burlywood #deb887
        lime #00ff00
        darkviolet #9400d3
        mediumorchid #ba55d3
        mediumspringgreen #00fa9a
        royalblue #4169e1
        darksalmon #e9967a
        crimson #dc143c
        aqua #00ffff
        deepskyblue #00bfff
        mediumpurple #9370db
        blue #0000ff
        greenyellow #adff2f
        tomato #ff6347
        thistle #d8bfd8
        fuchsia #ff00ff
        dodgerblue #1e90ff
        palevioletred #db7093
        laserlemon #ffff54
        plum #dda0dd
        lightgreen #90ee90
        skyblue #87ceeb
        deeppink #ff1493
        paleturquoise #afeeee
        violet #ee82ee
        aquamarine #7fffd4
        hotpink #ff69b4
        bisque #ffe4c4
        lightpink #ffb6c1
    '''

    parsed_colors = []

    for color_info in distinct_colors.splitlines():
        if re.match(r'^\s*$', color_info):
            continue
        h = re.search(r'(?<=#).*$', color_info).group(0)
        c = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
        parsed_colors.append(c)

    result = np.empty(cluster.shape[0], dtype='4<f4')
    for i in range(cluster.shape[0]):
        j = cluster[i]
        r = parsed_colors[j][0] / 255
        b = parsed_colors[j][1] / 255
        g = parsed_colors[j][2] / 255
        result[i] = r, g, b, 1.0
    return result


def build_forest_plot():
    forest_data_df = pd.read_csv('../data/forest_data.csv')
    return build_color_data_min_max(forest_data_df['forest_average'].to_numpy(),
                                    [0.0, 0.0, 0.5], [0.0, 1.0, 0.0],
                                    transform=lambda x: x ** 2)


def build_water_plot():
    water_data_df = pd.read_csv('../data/water_data.csv')
    return build_color_data_min_max(water_data_df['water_average_with_sea'].to_numpy(),
                                    [1.0, 0.8, 0.0], [0.0, 0.4, 1.0],
                                    transform=lambda x: 1 - ((1 - x) ** 2))


def build_age_plot():
    final_df = pd.read_csv('../dataframes/final_dataframe.tsv', sep='\t')

    age_groups = final_df[['0-15 years scaled', '16-34 years scaled',
                           '35-64 years scaled', '65 years or over scaled']].to_numpy()

    for i in range(age_groups.shape[0]):
        if np.abs(np.sum(age_groups[i]) - 1.0) > np.finfo(float).eps:
            age_groups[i] = [np.nan] * 4

    age_groups_min = np.nanmin(age_groups, axis=0)
    age_groups_max = np.nanmax(age_groups, axis=0)

    age_groups = (age_groups - age_groups_min) / (age_groups_max - age_groups_min)

    result = np.empty(age_groups.shape[0], dtype='4<f4')
    for i in range(age_groups.shape[0]):
        if np.isnan(age_groups[i]).any():
            result[i] = 1.0, 1.0, 1.0, 1.0
        else:
            argmax = np.argmax(age_groups[i])
            if argmax == 0:
                rgb = [1, 0, 0]
            elif argmax == 1:
                rgb = [0, 1, 0]
            elif argmax == 2:
                rgb = [0, 0, 1]
            elif argmax == 3:
                rgb = [0, 0, 0]
            # rgb = blend_s_rgb([
            #     [1, 0, 0],
            #     [0, 1, 0],
            #     [0, 0, 1],
            #     [1, 1, 1]
            # ], weights=age_groups[i])
            result[i] = rgb[0], rgb[1], rgb[2], 1.0

    return result


if __name__ == '__main__':
    build_and_save_map_plot()
