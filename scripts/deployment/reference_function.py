import numpy as np
import pandas as pd
from dash import html
# import requests
# from toolkits import *

# Requires UTF-8, Tab-seperated, name of postal code column = 'Postal code'
paavo_df = pd.read_table("./dataframes/final_dataframe.tsv",
                         dtype={"Postal code": object})  # The dtype CANNOT be removed!
traffic_df = pd.read_csv("./data/transportation/final_transportation.tsv",
                         sep="\t", dtype={"Postal code": object})
tax_df = pd.read_csv("./data/taxation/final_tax.tsv", sep="\t",
                     dtype={"Postal code": object})
zip_name_dict = dict(zip(paavo_df['Postal code'], map(
    lambda x: x.split("(")[0].strip(), paavo_df['Area'])))
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
location_dropdown = [{'label': i + ", " + zip_name_dict[i],
                      'value': i} for i in paavo_df['Postal code']]
occupation_dropdown = [{'label': i, 'value': i} for i in list_of_jobs]
household_type_dropdown = [{'label': i, 'value': i}
                           for i in list_of_household_type]


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


def make_dash_table(old_code, new_code):
    # Line 2
    old_income = get_attribute(old_code, 'Average income of inhabitants')
    new_income = get_attribute(new_code, 'Average income of inhabitants')
    result_income = float(new_income) / float(old_income) - 1
    if result_income > 0:
        analysis_income = f"↗ {result_income:.2%} potential increase"
    elif result_income > - 0.15:
        analysis_income = "Similar income"
    else:
        analysis_income = f"↘ {result_income:.2%} easier life"

    # Line 3
    attribute_name = 'Academic degree - Higher level university degree scaled'
    old_education = float(get_attribute(old_code, attribute_name))
    new_education = float(get_attribute(new_code, attribute_name))
    result_education = new_education - old_education
    analysis_education = "↗ Find more skilled fellows" if result_education > 0 else "↘ Less competitions"

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
    return html.Table([
        html.Thead(
            html.Tr([html.Th(), html.Th("Current Location"),
                    html.Th("New Location"), html.Th("Significance")])
        ),
        html.Tbody([
            html.Tr([html.Td("Income"), html.Td(old_income),
                    html.Td(new_income), html.Td(analysis_income)]),
            html.Tr([html.Td("Education index"), html.Td(f"{old_education:.2%}"),
                    html.Td(f"{new_education:.2%}"), html.Td(analysis_education)]),
            # html.Tr([html.Td("Number of companies"), html.Td(old_company_num),
            #         html.Td(new_company_num), html.Td(analysis_company_num)])
        ])
    ], id="insight_table")


def age_model(code):
    perc = paavo_df["65 years or over"] / paavo_df['Inhabitants, total']
    perc = np.nan_to_num(perc)
    perc[perc >= 1] = 0.5
    perc[perc <= 0] = 0.5
    # a[a > 70] = 70
    # plt.hist(a, bins=30)
    # plt.show()
    code_situation = float(get_attribute(
        code, "65 years or over")) / float(get_attribute(code, 'Inhabitants, total'))
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


# def tax_model(tax_rate=20):
#     taxes = pd.read_csv("./data/taxation/municipality_tax.tsv", sep="\t")['Tax']
#     # plt.hist(taxes, bins=10)
#     # plt.show()
#     if tax_rate < np.percentile(taxes, 20):
#         return "High"
#     elif tax_rate < np.percentile(taxes, 40):
#         return "Slightly higher"
#     elif tax_rate < np.percentile(taxes, 60):
#         return "Super high"
#     elif tax_rate < np.percentile(taxes, 80):
#         return "Ultra High"
#     else:
#         return "Extremely high"


def get_transportation_icons(code):
    string = ""
    location_info = traffic_df[traffic_df['Postal code'] == code]
    if location_info["Bus"].values[0] > 0:
        string += "🚌 "
    if location_info["Train"].values[0] > 0:
        string += "🚂 "
    if location_info["Tram"].values[0] > 0:
        string += "🚋 "
    if location_info["Metro"].values[0] > 0:
        string += "🚇 "
    if location_info["Ferry"].values[0] > 0:
        string += "🚢 "
    return string


def get_about_html():
    text = """
           This is the implementation of our Data Science Project. The aim of this project is to provide 
           suggestions on suitable relocation areas in Finland, based on housing prices and demographics.
           """
    return html.Div([
        html.H1("About"),
        html.H3(text, id="about_text"),
        html.H1("Team"),
        html.Table([
            html.Thead(
                html.Tr([html.Th("Letizia"), html.Th("Taige"), html.Th(
                        "Roope"), html.Th("Trang"), html.Th("Thong")])
            ),
            html.Tbody(
                html.Tr([
                    html.Td(
                        html.A(
                            html.Img(src="https://avatars1.githubusercontent.com/u/45148109?s=200&amp;v=4",
                                     alt="Letizia"),
                            href="https://github.com/letiziaia"
                        )
                    ),
                    html.Td(
                        html.A(
                            html.Img(src="https://avatars2.githubusercontent.com/u/16875716?s=200&amp;v=4",
                                     alt="Taige"),
                            href="https://github.com/xiaoxiaobt"
                        )
                    ),
                    html.Td(
                        html.A(
                            html.Img(src="https://avatars2.githubusercontent.com/u/43811718?s=200&amp;v=4",
                                     alt="Roope"),
                            href="https://github.com/rooperuu"
                        )
                    ),
                    html.Td(
                        html.A(
                            html.Img(src="https://avatars3.githubusercontent.com/u/55182434?s=200&amp;v=4",
                                     alt="Trang"),
                            href="https://github.com/trangmng"
                        )
                    ),
                    html.Td(
                        html.A(
                            html.Img(src="https://avatars0.githubusercontent.com/u/32213097?s=200&amp;v=4",
                                     alt="Thong"),
                            href="https://github.com/trananhthong"
                        )
                    )])
            )], id="team_table"
        )
    ], id="about_info")


def get_instructions():
    return html.Ul(
        children=[
            html.Li("An App that provides suggestions for relocation in Finland"),
            html.Li("Fill the form below and click 'Recommend'"),
            html.Li("Alternatively, click on one area")
        ],
        className="instructions_sidebar"
    )
