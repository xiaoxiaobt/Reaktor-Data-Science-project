import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
import numpy as np


# Experiment subset
use_postal_code = "00100"
use_years = ["2013", "2014", "2015", "2016"]
use_variables = ["Density", "Average age of inhabitants",
                 "Primary production", "Processing", "Services",
                 "Inhabitants, total", "Households, total", "Buildings, total", "Dwellings"]
use_scale_min_max_variables = ["Density", "Average age of inhabitants",
                 "Primary production", "Processing", "Services",
                 "Inhabitants, total", "Households, total", "Buildings, total", "Dwellings"]


def scale(df):
    """
    This function scales all the attributes according to
    their properties with respect to other variables.
    :param df: the data frame to scale
    """
    labels_scale_by_labour_force = {
        "Employed", "Unemployed"
    }
    labels_scale_by_outside_labour = {
        "Children aged 0 to 14", "Pensioners", "Others"
    }

    # Labels scaled by labour force and outside labour force are scaled first
    # labour force and outside labour force are later modified
    for key in use_variables:  # df.columns
        if key in labels_scale_by_labour_force:
            df[key] = df[key] / df["Labour force"]
        elif key in labels_scale_by_outside_labour:
            df[key] = df[key] / df["Persons outside the labour force"]

    labels_scale_by_inhabitants = {
        "Males", "Females", "Average age of inhabitants",
        "0 - 2 years", "3 - 6 years",
        "7 - 12 years", "13 - 15 years", "16 - 17 years", "18 - 19 years", "20 - 24 years",
        "25 - 29 years", "30 - 34 years", "35 - 39 years", "40 - 44 years", "45 - 49 years",
        "50 - 54 years", "55 - 59 years", "60 - 64 years", "65 - 69 years, ", "70 - 74 years, ",
        "75 - 79 years", "80 - 84 years", "85 years or over", "Aged 18 or over, total",
        "Basic level studies", "With education, total", "Matriculation examination",
        "Vocational diploma", "Academic degree - Lower level university degree",
        "Academic degree - Higher level university degree",
        "Inhabintants belonging to the lowest income category",
        "Inhabitants belonging to the middle income category",
        "Inhabintants belonging to the highest income category",
        "Labour force", "Persons outside the labour force", "Students"
    }
    labels_scale_by_households = {
        "Average size of households", "Young single persons", "Young couples without children, ",
        "Households with children", "Households with small children",
        "Households with children under school age", "Households with school-age children",
        "Households with teenagers", "Adult households", "Pensioner households",
        "Households living in owner-occupied dwellings", "Households living in rented dwellings",
        "Households living in other dwellings", "Households belonging to the lowest income category",
        "Households belonging to the middle income category",
        "Households belonging to the highest income category"
    }
    labels_scale_by_buildings = {
        "Free - time residences", "Other buildings", "Residential buildings"
    }
    labels_scale_by_dwellings = {
        "Dwellings in small houses", "Dwellings in blocks of flats"
    }

    # Scale the four sets above
    for key in use_variables:  # df.columns
        if key in labels_scale_by_inhabitants:
            df[key] = df[key] / df["Inhabitants, total"]
        elif key in labels_scale_by_households:
            df[key] = df[key] / df["Households, total"]
        elif key in labels_scale_by_buildings:
            df[key] = df[key] / df["Buildings, total"]
        elif key in labels_scale_by_dwellings:
            df[key] = df[key] / df["Dwellings"]

    labels_combine_scale_by_inhabitants = {
        "Primary production", "Processing", "Services"
    }
    labels_combine_scale_by_workplaces = {
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
    }

    labels_combine_scale_by_inhabitants = [x for x in labels_combine_scale_by_inhabitants if x in use_variables]
    labels_combine_scale_by_workplaces = [x for x in labels_combine_scale_by_workplaces if x in use_variables]

    # Sum the selected attributes for each area with the similar postal code
    # In other words, postal codes with the same first 3 digits
    df_combine = df[
        ["Postal code", "Inhabitants, total", "Workplaces"] +
        list(labels_combine_scale_by_inhabitants) + list(labels_combine_scale_by_workplaces)
    ].copy()
    df_combine["Postal code"] = df_combine["Postal code"].map(lambda x: x[:-2])
    df_combine = df_combine.groupby("Postal code", as_index=False).agg("sum")

    # Scale the combined columns
    for key in df_combine.columns:
        if key in labels_combine_scale_by_inhabitants:
            df_combine[key] = df_combine[key] / df_combine["Inhabitants, total"]
        elif key in labels_combine_scale_by_workplaces:
            df_combine[key] = df_combine[key] / df_combine["Workplaces"]

    # Replace the combined and scaled values into the original dataframe
    for _, row in df_combine.iterrows():
        code = row["Postal code"]
        df_rows = df["Postal code"].str.startswith(code)
        # Postal code, Inhabitants and workplaces remain unchanged
        columns = row.index.drop(["Postal code", "Inhabitants, total", "Workplaces"])
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

    # Replace the columns with the testing subset
    columns = use_scale_min_max_variables

    # Compute the scaled values
    scaler = MinMaxScaler(feature_range=(0, 1), copy=False)
    values = scaler.fit_transform(df[columns].to_numpy())

    # Place the scaled values back in the data frame.
    for i, column in enumerate(columns):
        df[column] = values[:, i]

    return df


def plot_test():
    """
    This function plots the attributes with respect to time.
    """

    # y = year
    # v = variable
    # p = postal code

    ys = ["2012", "2013", "2014", "2015", "2016", "2017"]

    # Construct the initial variable-postal code data frames for each year
    df_vp_by_y = {}
    for y in ys:
        # Read the data frame
        df = pd.read_csv(f"dataframes/df{y}.tsv", sep="\t")
        # Remove the year and extra comma
        df.columns = [re.sub(r", \d{4} $", "", column) for column in df.columns]
        # Fix the postal code (5 digits and string)
        df["Postal code"] = df["Postal code"].astype(str).str.pad(5, fillchar='0')
        df_vp_by_y[y] = df

    # Replace the years with the testing subset
    ys = use_years

    # Do the scaling
    for y in ys:
        df_vp_by_y[y] = scale(df_vp_by_y[y])
        df_vp_by_y[y] = scale_min_max(df_vp_by_y[y])

    ps = df_vp_by_y["2017"]["Postal code"]

    # Replace the postal codes with the testing subset
    ps = [use_postal_code]

    # Find a list of variables common for each year
    vs = list(df_vp_by_y[ys[0]].columns)
    for y in ys[1:]:
        vs = list(filter(lambda x: x in list(df_vp_by_y[y].columns), vs))
    vs.remove("Postal code")
    vs.remove("Area")

    # Replace the variables with the testing subset
    vs = use_variables

    # Construct a variable-year data frame for each postal code
    df_vy_by_p = {}
    for p in ps:

        # Copy values into their corresponding cells
        df = pd.DataFrame(columns=vs, index=ys)
        for y in ys:
            for v in vs:
                df2 = df_vp_by_y[y]
                df[v][y] = df2.loc[df2["Postal code"] == p, v].iloc[0]
        df_vy_by_p[p] = df

        # Move year into a column
        df.insert(0, "Year", df.index)
        df.reset_index(drop=True, inplace=True)

    # Select the test data frame
    df_test = df_vy_by_p[use_postal_code]

    # Plot the test data frame
    df_test = df_test.melt("Year", var_name="cols", value_name="vals")
    sns.catplot(x="Year", y="vals", hue="cols", data=df_test, kind="point")
    plt.show()


plot_test()
