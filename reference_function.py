import pandas as pd
import dash_html_components as html
import numpy as np
# import requests
# import matplotlib.pyplot as plt
# from toolkits import *

name_paavo_dataframe = "./dataframes/final_dataframe.tsv"  # Requires UTF-8, Tab-seperated, name of postal code column = 'Postal code'
paavo_df = pd.read_table(name_paavo_dataframe, dtype={"Postal code": object})  # The dtype CANNOT be removed!
traffic_df = pd.read_csv("./data_transportation/final_transportation.tsv", sep="\t", dtype={"Postal code": object})
tax_df = pd.read_csv("./data/final_tax.tsv", sep="\t", dtype={"Postal code": object})
zip_name_dict = dict(zip(paavo_df['Postal code'], map(lambda x: x.split("(")[0].strip(), paavo_df['Area'])))
zip_tax_dict = dict(zip(tax_df["Postal code"], tax_df["Tax"]))
list_of_jobs = ['Student',
                'Agriculture, forestry, fishing',
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
                'Extraterritorial organisations and bodies'
                ]
list_of_household_type = [1, 2, 3, 4, "5 or more"]
location_dropdown = [{'label': i + ", " + zip_name_dict[i], 'value': i} for i in paavo_df['Postal code']]
occupation_dropdown = [{'label': i, 'value': i} for i in list_of_jobs]
household_type_dropdown = [{'label': i, 'value': i} for i in list_of_household_type]


def get_attribute(postalcode="02150", column=None):
    """
    Read from the data frame: find the value of the given column for the given postal code.
    :param postalcode: str, a valid postal code
    :param column: str, a valid complete column name
    :return: a string with the value of the column, or raise Exception
    """
    if column is not None:
        return str(paavo_df[paavo_df['Postal code'] == postalcode][column].values[0])
    else:
        raise Exception


def radar_value(postalcode="02150"):
    """
    Read from the data frame: find the value of the given column for the given postal code,
    and normalize it from 0 to 1 if needed.
    :param postalcode: str, a valid postal code
    :param column: str, a valid complete column name
    :return: a float with the value of the column, or raise Exception
    """

    def find_data(column_name):
        value = float(get_attribute(postalcode, column=column_name))
        if "scaled" in column_name:
            return value
        else:
            return (value - paavo_df[column_name].min()) / (paavo_df[column_name].max() - paavo_df[column_name].min())

    column_names = ["Academic degree - Higher level university degree scaled", "Services", "Bus stops",
                    "Average income of inhabitants", "Density"]
    return [find_data(name) for name in column_names]


def format_2f(string):
    """
    Format a number to show only 2 decimal digits.
    :param string: the string with the number
    :return: the formatted string
    """
    return "{:.2f}".format(float(string))


def make_dash_table(old_code, new_code):
    def four_row_list(name, first, second, third):
        return html.Tr([html.Td([name], style={"width": "160px"}), html.Td([first], style={"width": "100px"}),
                        html.Td([second], style={"width": "100px"}), html.Td([third], style={"width": "300px"})],
                       style={"margin-left": "9%", "display": "block"})

    """ Return a dash definition of an HTML table for a Pandas dataframe """
    # Line 1
    row_title = four_row_list("", "Current Location", "New Location", "Significance")

    # Line 2
    old_income = get_attribute(old_code, 'Average income of inhabitants')
    new_income = get_attribute(new_code, 'Average income of inhabitants')
    result_income = float(new_income) / float(old_income) - 1
    if result_income > 0:
        analysis_income = "↗ {:.2f}% potential increase".format(result_income * 100)
    elif result_income > - 0.15:
        analysis_income = "Similar income"
    else:
        analysis_income = "↘ {:.2f}% easier life".format(result_income * 100)
    row_income = four_row_list("Income", old_income, new_income, analysis_income)

    # Line 3
    old_education = format_2f(
        float(get_attribute(old_code, 'Academic degree - Higher level university degree scaled')) * 100)
    new_education = format_2f(
        float(get_attribute(new_code, 'Academic degree - Higher level university degree scaled')) * 100)
    result_education = float(new_education) - float(old_education)
    analysis_education = "↗ Find more skilled fellows" if result_education > 0 else "↘ Less competitions"
    row_education = four_row_list("Education index", old_education, new_education, analysis_education)
    table = [row_title, row_income, row_education]
    # for x in old_dict.keys():
    #    table.append(four_row_list(x, old_dict[x], new_dict[x], ""))

    # Line 4

    # url = "https://avoindata.prh.fi/bis/v1?totalResults=true&maxResults=1&resultsFrom=10000" + \
    #       "&streetAddressPostCode={:s}&companyRegistrationFrom=1950-01-01"
    # print("This part takes time (~10s). Comment this part to accelerate. \n(From line 100, reference_function.py)")
    # old_company_num = eval(requests.get(url.format(old_code)).text.split(',"previous')[0] + '}')['totalResults']
    # new_company_num = eval(requests.get(url.format(new_code)).text.split(',"previous')[0] + '}')['totalResults']
    # result_company_num = int(new_company_num) - int(old_company_num)
    # analysis_company_num = "↗ Big town with more opportunities" if result_company_num > 0 else "↘ Peaceful life"
    # row_company_num = four_row_list("Number of companies", old_company_num, new_company_num, analysis_company_num)

    return table


def age_model(code):
    perc = paavo_df["65 years or over"] / paavo_df['Inhabitants, total']
    perc = np.nan_to_num(perc)
    perc[perc >= 1] = 0.5
    perc[perc <= 0] = 0.5
    # a[a > 70] = 70
    # plt.hist(a, bins=30)
    # plt.show()
    code_situation = float(get_attribute(code, "65 years or over")) / float(get_attribute(code, 'Inhabitants, total'))
    if code_situation <= np.percentile(perc, 20):
        return "Very Young"
    elif code_situation <= np.percentile(perc, 30):
        return "Young"
    elif code_situation <= np.percentile(perc, 45):
        return "Moderate"
    elif code_situation <= np.percentile(perc, 60):
        return "Youngest-old"
    else:
        return "Old"


def tax_model(tax_rate=20):
    taxes = pd.read_csv("../data/municipality_tax.tsv", sep="\t")['Tax']
    # plt.hist(taxes, bins=10)
    # plt.show()
    if tax_rate < np.percentile(taxes, 20):
        return "High"
    elif tax_rate < np.percentile(taxes, 40):
        return "Slightly higher"
    elif tax_rate < np.percentile(taxes, 60):
        return "Super high"
    elif tax_rate < np.percentile(taxes, 80):
        return "Ultra High"
    else:
        return "Extremely high"


def get_transportation_icons(code):
    string = ""
    if traffic_df[traffic_df['Postal code'] == code]["Bus"].values[0] > 0:
        string += "🚌 "
    if traffic_df[traffic_df['Postal code'] == code]["Train"].values[0] > 0:
        string += "🚂 "
    if traffic_df[traffic_df['Postal code'] == code]["Tram"].values[0] > 0:
        string += "🚋 "
    if traffic_df[traffic_df['Postal code'] == code]["Metro"].values[0] > 0:
        string += "🚇 "
    if traffic_df[traffic_df['Postal code'] == code]["Ferry"].values[0] > 0:
        string += "🚢 "
    return string
