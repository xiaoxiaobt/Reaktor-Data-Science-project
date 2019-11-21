import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns


# Experiment subset
use_postal_code = "00100"
use_years = ["2013", "2014", "2015", "2016"]
use_variables = ["Density", "Average age of inhabitants",
                 "Primary production", "Processing", "Services",
                 "Inhabitants, total", "Households, total", "Buildings, total", "Dwellings"]
use_scale_min_max_variables = ["Density", "Average age of inhabitants",
                 "Primary production", "Processing", "Services",
                 "Inhabitants, total", "Households, total", "Buildings, total", "Dwellings"]


def plot_test():
    """
    This function plots the attributes with respect to time.
    """

    # y = year
    # v = variable
    # p = postal code

    ys_test = ["2013", "2014", "2015", "2016"]
    ps_test = ["00100"]
    vs_test = ["Average age of inhabitants"]

    ys = ["2012", "2013", "2014", "2015", "2016", "2017"]

    # Construct the initial variable-postal code data frames for each year
    df_vp_by_y = {}
    for y in ys:
        # Read the data frame
        df = pd.read_csv(f"dataframes_scaled/df{y}.tsv", sep="\t")
        # Remove the year and extra comma
        df.columns = [re.sub(r", \d{4} $", "", column) for column in df.columns]
        # Fix the postal code (5 digits and string)
        df["Postal code"] = df["Postal code"].astype(str).str.pad(5, fillchar='0')
        df_vp_by_y[y] = df

    ps = df_vp_by_y["2017"]["Postal code"]

    ys = ys_test
    ps = ps_test

    # Find a list of variables common for each year
    vs = list(df_vp_by_y[ys[0]].columns)
    for y in ys[1:]:
        vs = list(filter(lambda x: x in list(df_vp_by_y[y].columns), vs))
    vs.remove("Postal code")
    vs.remove("Area")

    vs = vs_test

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
    df_test = df_vy_by_p[ps_test[0]]

    # Plot the test data frame
    df_test = df_test.melt("Year", var_name="cols", value_name="vals")
    sns.catplot(x="Year", y="vals", hue="cols", data=df_test, kind="point")
    plt.show()


plot_test()
