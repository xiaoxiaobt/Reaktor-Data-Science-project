import numpy as np
import os
import pandas as pd
from pathlib import Path
import re
from sklearn.preprocessing import MinMaxScaler


def scale(df):
    """
    This function scales all the attributes according to
    their properties with respect to other variables.
    :param df: the data frame to scale
    """

    labels_scale_by = {}

    labels_scale_by["Labour force"] = [
        "Employed", "Unemployed"
    ]
    labels_scale_by["Persons outside the labour force"] = [
        "Children aged 0 to 14", "Pensioners", "Others"
    ]
    labels_scale_by["Inhabitants, total"] = [
        "Males", "Females", "Average age of inhabitants",
        "0-15 years", "16-34 years", "35-64 years", "65 years or over", "Aged 18 or over, total",
        "Basic level studies", "With education, total", "Matriculation examination",
        "Vocational diploma", "Academic degree - Lower level university degree",
        "Academic degree - Higher level university degree",
        "Inhabintants belonging to the lowest income category",
        "Inhabitants belonging to the middle income category",
        "Inhabintants belonging to the highest income category",
        "Labour force", "Persons outside the labour force", "Students"
    ]
    labels_scale_by["Households, total"] = [
        "Average size of households", "Young single persons", "Young couples without children, ",
        "Households with children", "Households with small children",
        "Households with children under school age", "Households with school-age children",
        "Households with teenagers", "Adult households", "Pensioner households",
        "Households living in owner-occupied dwellings", "Households living in rented dwellings",
        "Households living in other dwellings", "Households belonging to the lowest income category",
        "Households belonging to the middle income category",
        "Households belonging to the highest income category"
    ]
    labels_scale_by["Buildings, total"] = [
        "Free - time residences", "Other buildings", "Residential buildings"
    ]
    labels_scale_by["Dwellings"] = [
        "Dwellings in small houses", "Dwellings in blocks of flats"
    ]

    for scale_by, to_scale_list in labels_scale_by.items():
        for to_scale in to_scale_list:
            if scale_by in df.columns and to_scale in df.columns:
                df[to_scale + " scaled"] = df[to_scale] / df[scale_by]

    labels_combine_scale_by = {}

    labels_combine_scale_by["Inhabitants, total"] = [
        "Primary production", "Processing", "Services"
    ]
    labels_combine_scale_by["Workplaces"] = [
        "A Agriculture, forestry and fishing",
        "B Mining and quarrying", "C Manufacturing", "D Electricity, gas, steam and air conditioning supply",
        "E Water supply; sewerage, waste management and remediation activities", "F Construction",
        "G Wholesale and retail trade; repair of motor vehicles and motorcycles", "H Transportation and storage",
        "I Accommodation and food service activities", "J Information and communication",
        "K Financial and insurance activities", "L Real estate activities",
        "M Professional, scientific and technical activities", "N Administrative and support service activities",
        "O Public administration and defence; compulsory social security", "P Education",
        "Q Human health and social work activities", "R Arts, entertainment and recreation",
        "S Other service activities", "T Activities of households as employers; " +
        "undifferentiated goods- and services-producing activities of households for own use",
        "U Activities of extraterritorial organisations and bodies"
    ]

    labels_combine = ["Postal code"] + list(labels_combine_scale_by.keys()) +\
                [item for items in labels_combine_scale_by.values() for item in items]
    labels_combine = list(filter(lambda x: x in df.columns, labels_combine))

    # Sum the selected attributes for each area with the similar postal code
    # In other words, postal codes with the same first 3 digits
    df_combine = df[labels_combine].copy()
    df_combine["Postal code"] = df_combine["Postal code"].map(lambda x: x[:-2])
    df_combine = df_combine.groupby("Postal code", as_index=False).agg("sum")

    # Scale the combined columns
    for scale_by, to_scale_list in labels_combine_scale_by.items():
        for to_scale in to_scale_list:
            if scale_by in df_combine.columns and to_scale in df_combine.columns:
                df_combine[to_scale + " combine scaled"] = df_combine[to_scale] / df[scale_by]

    # Replace the combined and scaled values into the original dataframe
    for _, row in df_combine.iterrows():
        code = row["Postal code"]
        df_rows = df["Postal code"].str.startswith(code)
        # Postal code, Inhabitants and workplaces remain unchanged
        columns = row.index.drop(labels_combine)
        for column in columns:
            df.loc[df_rows, column] = row[column]

    df.replace({np.inf: np.nan}, inplace=True)

    return df


def scale_min_max(df):
    """
    This function scales all the attributes according to
    their properties with respect to itself.
    :param df: the data frame to scale
    """

    # Strip out postal code and area
    columns = list(df.columns)
    columns.remove("Postal code")
    columns.remove("Area")

    # Compute the scaled values
    scaler = MinMaxScaler(feature_range=(0, 1), copy=False)
    values = scaler.fit_transform(df[columns].to_numpy())

    # Place the scaled values back in the data frame.
    for i, column in enumerate(columns):
        df[column] = values[:, i]

    return df


def load_scale_save():

    ys = ["2012", "2013", "2014", "2015", "2016", "2017"]

    # Construct the initial variable-postal code data frames for each year
    df_vp_by_y = {}
    for y in ys:
        # Read the data frame
        df = pd.read_csv(f"dataframes/df{y}.tsv", sep="\t")
        # Remove the year and extra comma
        df.columns = [re.sub(r", \d{4}\s*$", "", column) for column in df.columns]
        # Fix the postal code (5 digits and string)
        df["Postal code"] = df["Postal code"].astype(str).str.pad(5, fillchar='0')
        df_vp_by_y[y] = df

    # Do the scaling
    for y in ys:
        print("Scaling " + str(y))
        df_vp_by_y[y] = scale(df_vp_by_y[y])
        # df_vp_by_y[y] = scale_min_max(df_vp_by_y[y])

    folder = 'dataframes_scaled'
    if not os.path.exists(folder):
        os.makedirs(folder)

    for y, df_vp in df_vp_by_y.items():
        filename = 'df' + str(y) + '.tsv'
        df_vp.to_csv(Path(folder) / filename, sep='\t', index=False, encoding='utf-8')


if __name__ == '__main__':
    load_scale_save()
