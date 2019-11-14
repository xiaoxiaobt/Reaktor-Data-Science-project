import pandas as pd
import geopy.distance


def get_distance(df, threshold='80', postalcode='00100'):
    """
    :param df: the data frame, with clusters labels in the column 'label'
    :param threshold: float, expressed in km. Distances greater than this number
            will not be considered
    :param postalcode: string, the postal code with respect to which the distance is computed
    :return: a dictionary of postal codes with distance less than or equal to threshold
    """

    target = df[df['Postal code'] == postalcode][['Lat'], ['Lon']]
    df = df[df['Postal code'] == postalcode]['label']

    our_dic = {}
    for i, row in df.iterrows():
        pc = row['Postal code']
        lat = row['Lat']
        lon = row['Lon']
        our_dic[pc] = (lat, lon)

    distance_dic = {}
    for k in our_dic.keys():
        dist = geopy.distance.distance(our_dic[k], target).km
        if dist <= threshold:
            distance_dic[k] = dist

    return sort_dictionary(distance_dic)


def sort_dictionary(my_dict, reverse=False):
    """
    Sort the dictionary based on values.
    :param my_dict: the dictionary to sort
    :param reverse: boolean, when True sorts in decreasing order, and
            when False shows in increasing order, with respect to the values.
            Default: False.
    :return: a list of tuples, where the first element is the key,
            and the second element is the value.
    """
    return sorted(my_dict.items(), key=lambda x: x[1], reverse=reverse)