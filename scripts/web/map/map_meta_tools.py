import json
import numpy as np
import sys


def build_map_meta(source):

    # Parse the GeoJSON into a dictionary.
    feature_collection = json.loads(source)
    if not feature_collection['type'] == 'FeatureCollection':
        raise TypeError()

    index_list = []

    # Iterate over the features in the feature collection.
    for feature in feature_collection['features']:
        if not feature['type'] == 'Feature':
            raise TypeError()

        # Extract the desired properties.
        code = feature['properties']['posti_alue']
        name = feature['properties']['nimi']

        index_list.append((code, name))

    # Sort the index by postal code.
    index_list.sort(key=lambda it: it[0])

    # Test that the names fit the fixed 30-character field.
    if not max(map(lambda it: len(it[1]), index_list)) == 30:
        raise ValueError()

    return {
        'region_code_data': np.array([it[0] for it in index_list], dtype='<U5'),
        'region_name_data': np.array([it[1] for it in index_list], dtype='<U30')
    }


def build_and_save_map_meta(source):
    map_meta = build_map_meta(source)
    np.savez_compressed('map_meta.npz', **map_meta)


def load_map_meta():
    map_meta = np.load('map_meta.npz')
    if sys.byteorder == 'big':
        for it in map_meta.values():
            it.byteswap()
    return map_meta


if __name__ == '__main__':
    source_filename = 'Paavo-postinumeroalueet 2019.geojson'
    with open(source_filename, encoding='utf-8') as source_file:
        build_and_save_map_meta(source_file.read())
