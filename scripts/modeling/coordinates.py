import json
from pathlib import Path

INPUT_FILENAME = "area_center_of_mass.geojson"


def coordinates():
    with open(Path("data/") / INPUT_FILENAME) as file:
        data = parse_feature_collection(json.load(file))
    return sorted(data)


def parse_feature_collection(feature_collection):
    if not feature_collection['type'] == 'FeatureCollection':
        raise TypeError()

    # Parse each feature in this collection as a list.
    return [parse_feature(it) for it in feature_collection['features']]


def parse_feature(feature):
    if not feature['type'] == 'Feature':
        raise TypeError()

    # Extract the required properties from the feature.
    code = feature['properties']['posti_alue']
    coordinates = feature['geometry']['coordinates']

    return [code, coordinates]


if __name__ == '__main__':
    d = coordinates()
    print(d)

