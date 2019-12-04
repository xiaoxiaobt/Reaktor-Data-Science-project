import pandas as pd
import numpy as np
import geopy.distance
from pathlib import Path
from scipy.spatial import distance


column_list = ['Postal code',
               'Area',
               'Academic degree - Higher level university degree scaled',
               'Employment rate %',
               'Average income of inhabitants',
               'Average age of inhabitants',
               '0-15 years scaled',
               '16-34 years scaled',
               '35-64 years scaled',
               '65 years or over scaled',
               'Average size of households',
               'Density',
               'Students',
               'Primary production combine scaled',
               'Processing combine scaled',
               'Services combine scaled',
               'A Agriculture, forestry and fishing combine scaled',
               'B Mining and quarrying combine scaled',
               'C Manufacturing combine scaled',
               'D Electricity, gas, steam and air conditioning supply combine scaled',
               'E Water supply; sewerage, waste management and remediation activities combine scaled',
               'F Construction combine scaled',
               'G Wholesale and retail trade; repair of motor vehicles and motorcycles combine scaled',
               'H Transportation and storage combine scaled',
               'I Accommodation and food service activities combine scaled',
               'J Information and communication combine scaled',
               'K Financial and insurance activities combine scaled',
               'L Real estate activities combine scaled',
               'M Professional, scientific and technical activities combine scaled',
               'N Administrative and support service activities combine scaled',
               'O Public administration and defence; compulsory social security combine scaled',
               'P Education combine scaled',
               'Q Human health and social work activities combine scaled',
               'R Arts, entertainment and recreation combine scaled',
               'S Other service activities combine scaled',
               'T Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use combine scaled',
               'U Activities of extraterritorial organisations and bodies combine scaled',
               'Forest',
               'Water',
               'Bus stops',
               'Sell price',
               'Rent price with ARA',
               'Rent price without ARA',
               'Lat',
               'Lon',
               'label'
               ]


def get_distance(df, postalcode='00100'):
    """
    :param df: the data frame
    :param postalcode: string, the postal code with respect to which the distance is computed
    :return: the data frame, with a new column named 'Distance' that stores the geographical distance
            in km between 'postalcode' and each postal code in the data frame
    """

    target = df[df['Postal code'] == postalcode][['Lat', 'Lon']].values[0]

    df['Distance'] = [0] * len(df.index)
    for i, row in df.iterrows():
        # pc = row['Postal code']
        lat = row['Lat']
        lon = row['Lon']
        coord = (lat, lon)
        dist = geopy.distance.distance(coord, target).km
        df.at[i, 'Distance'] = dist

    return df


def dataframe():
    """
    Open the data frame and return it.
    :return: the data frame
    """
    # Open sample
    df = pd.read_csv(Path("dataframes/") / 'final_dataframe.tsv', sep='\t', skiprows=0, encoding='utf-8',
                     dtype={'Postal code': object})

    # Correctly assign data types
    column_dic = dict.fromkeys(df.columns)
    for key in column_dic.keys():
        # print(key)
        if key in ['Postal code', 'Area', 'text']:
            column_dic[key] = 'object'
        else:
            column_dic[key] = 'float'
    df = df.astype(column_dic)

    if sum(df.isna().sum(axis=0)) > 0:
        print("WARNING: There are still missing values. They will be replaced with 0.")
        print(df.isna().sum(axis=0)[df.isna().sum(axis=0) > 0])
        df.fillna(0, inplace=True)
    return df[column_list]


def find_neighbor_of(df=None, weights=None, placename=None, postalcode=None):
    """
    Return the postal code of the place that is most similar to 'placename' or 'postalcode',
    given the data frame 'df'. Also set the weight list to compute the distance in the feature
    space using the weighted Euclidean distance.
    :param df: the data frame with places and features
    :param weights: list, the weights for the distance calculation
    :param placename: str, the name (can be partial) of the starting area
    :param postalcode: str, the postal code of the starting area
    :return: str, a postal code
    """
    if placename is None and postalcode is None:
        raise Exception
    elif placename is not None:
        myrow = df.loc[df['Area'].str.contains(placename)]
        myrow = myrow.values
    else:
        myrow = df.loc[df['Postal code'].str.contains(postalcode)]
        myrow = myrow.values[0]

    # Compute the distance between places in the feature space, sort it and return the second one
    # (because the first one is always the starting place)
    dist = {}
    for _, row in df.iterrows():
        dist[row['Postal code']] = distance.euclidean(np.ndarray.flatten(myrow[3:]), np.ndarray.flatten(row.values[3:]),
                                                      w=weights)

    dist = sorted(dist.items(), key=lambda x: x[1], reverse=False)
    print(len(dist))
    # Print the first 10 suggestions
    for count, elm in enumerate(dist):
        i = elm[0]
        print(str(df[df['Postal code'] == i][['Postal code', 'Area']].values[0]) + "\t" + str(elm[1]))
        if count >= 10:
            break
    return str(dist[1][0])


def get_cluster_of(postalcode=""):
    """
    Open the final data frame (it needs to have the column 'label') and
    read the id of the cluster for the given postal code. Filter the data frame
    to get all the postal codes that belong to the same cluster.
    :param postalcode: string, the postal code for which we want to retrieve the cluster
    :return: list of string, where each element is a postal code in the same cluster as
            the given 'postalcode' parameter. If no 'postalcode' is given, raise Exception.
    """
    df = dataframe()
    if postalcode != "":
        cluster = df[df['Postal code'].str.contains(postalcode)]['label'].values[0]
        cluster_members = df[df['label'] == cluster]
        if len(cluster_members) <= 1:
            cluster_members = df
        return cluster_members
    else:
        raise Exception


def apply_input(income, age, location, occupation, household_type, selection_radio):
    """
    Take the input from the UI and build an ideal place by modifying the current 'location'
    and boosting the values of Average income, Average age, Job places, Average household size
    so that they reflect the input of the user. Also, threshold the data frame based on the
    input given in 'selection_radio'.
    :param income: int, the annual average income of the user
    :param age: int, the age of the user
    :param location: str, the current place postal code
    :param occupation: str, the occupation from 'list_of_jobs'
    :param household_type: int, the size of the user's household. If household type is a string, it will
            be converted to 5.
    :param selection_radio: str, when equal to "change" the suggestion will be further away than 100 km,
            when equal to "nochange" the suggestion will be closer than 100 km.
    :return: call the function 'find_neighbor_of' which return the suggested postal code
    """
    print(income)
    print(age)
    print(location)
    print(occupation)
    print(household_type)
    print(selection_radio)

    df = get_cluster_of(location)
    df = get_distance(df=df, postalcode=location)
    d = 70
    if selection_radio == 'change':
        # Far away: consider more than 70 km away (if possible, otherwise closer)
        if len(df[(df['Distance'] == 0.0) | (df['Distance'] >= d)].index > 1):
            df = df[(df['Distance'] == 0.0) | (df['Distance'] >= d)]
        else:
            print("WARNING: the result was empty. We will set a different threshold")
            while len(df[(df['Distance'] == 0.0) | (df['Distance'] >= d)].index) <= 1:
                d -= 10
                df = df[(df['Distance'] == 0.0) | (df['Distance'] >= d)]
    elif selection_radio == 'nochange':
        # Close: consider closer than 70 km (if possible, otherwise a bit further away)
        if len(df[df['Distance'] <= d].index > 1):
            df = df[df['Distance'] <= d]
        else:
            print("WARNING: the result was empty. We will set a different threshold")
            while len(df[df['Distance'] <= d].index) <= 1:
                d += 10
                df = df[df['Distance'] <= d]
    else:
        # No restriction on distance
        df = df

    if occupation == "Student":
        print("Student")
        weights = [3, 1,  # Academic degree, Employment rate
                   1, 3,  # Avg income, Avg age
                   1, 2, 1, 1,  # Age distribution
                   2,  # Avg size household
                   0,  # Density
                   4,  # Students
                   1, 1, 1,  # Primary, Processing, Services
                   1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                   2, 1, 2, 1, 1, 2, 2, 1, 1, 1,
                   1,
                   1, 1,  # Forest, Water
                   1, 1, 2, 1,  # Bus stops, Sell price, Rent price with ARA, Rent price without ARA
                   0, 0, 0,  # Lat, Lon, label
                   0]  # Distance
        occupation = "Students"
    else:
        print("Working")
        weights = [3, 1,
                   3, 1,
                   1, 1, 1, 1,
                   3,
                   1,
                   3,
                   1, 1, 1,
                   2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                   2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                   2,
                   2, 2,
                   1, 1, 1, 1,
                   0, 0, 0,
                   0]
        jobs_input = ['Agriculture, forestry, fishing',
                      'Mining and quarrying',
                      'Manufacturing',
                      'Electricity, gas, steam, air conditioning supply',
                      'Water supply, sewerage, waste management',
                      'Construction',
                      'Wholesale, retail, repair of vehicles',
                      'Transportation and storage',
                      'Accommodation and food service',
                      'Information and communication',
                      'Financial and insurance',
                      'Real estate',
                      'Professional, scientific, technical activities',
                      'Administrative and support service',
                      'Public administration, defence, social security',
                      'Education',
                      'Human health and social work',
                      'Arts, entertainment and recreation',
                      'Other service',
                      'Activities of households as employers',
                      'Extraterritorial organisations and bodies']
        occupation = jobs_input.index(occupation) + 16
        print(occupation)

    household_type = household_type if type(household_type) is str else 5
    inputs = [income, household_type]
    column_names = ['Average income of inhabitants', 'Average size of households']
    ages = ['0-15 years scaled', '16-34 years scaled', '35-64 years scaled', '65 years or over scaled']

    if age <= 15:
        print("Child")
        age_group = ages[0]
    elif age <= 34:
        print("Young")
        age_group = ages[1]
    elif age <= 64:
        print("Adult")
        age_group = ages[2]
    else:
        print("Superadult")
        age_group = ages[3]

    i = df[df['Postal code'] == location].index.to_list()[0]

    for col in df.columns:
        if col in column_names:
            df.at[i, col] = inputs[column_names.index(col)]
        elif col == occupation:
            df.at[i, col] = df[col].max() if df[col].max() > df[df['Postal code'] == location][col].values[0] \
                else df[df['Postal code'] == location][col].values[0]
        elif col == age_group:
            df.at[i, col] = df[col].max() if df[col].max() > df[df['Postal code'] == location][col].values[0] \
                else df[df['Postal code'] == location][col].values[0]

    df.reset_index(inplace=True)
    return find_neighbor_of(df=df, weights=weights, postalcode=location)


if __name__ == '__main__':
    df = pd.read_csv(Path("dataframes/") / 'final_dataframe.tsv', sep='\t', skiprows=0, encoding='utf-8',
                     dtype={'Postal code': object})
    df = get_distance(df)
    print(df['Distance'])

    # 20540 Nummi-Ylioppilaskylä   (Turku)
    # 40740 Kortepohja   (Jyväskylä)
    # 33720 Hervanta   (Tampere)
    # 53850 Skinnarila   (Lappeenranta)
    n = apply_input(income=10000, age=22, location="02150",
                    occupation="Student",
                    household_type=1, selection_radio="whatever")
    print(n)
    m = apply_input(income=10000, age=22, location="02150",
                    occupation="Education",
                    household_type=1, selection_radio="whatever")
    print(m)