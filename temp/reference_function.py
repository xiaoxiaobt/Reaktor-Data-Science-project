import pandas as pd
import dash_html_components as html
import requests

name_paavo_dataframe = "./dataframes/final_dataframe.tsv"  # Requires UTF-8, Tab-seperated, name of postal code column ='Postal code'
paavo_df = pd.read_table(name_paavo_dataframe, dtype={"Postal code": object})  # The dtype CANNOT be removed!


def zip_name_dict():
    zip_name_dict = dict(zip(paavo_df['Postal code'], map(lambda x: x.split("(")[0].strip(), paavo_df['Area'])))
    return zip_name_dict


def location_dropdown():
    return [{'label': i + ", " + zip_name_dict()[i], 'value': i} for i in paavo_df['Postal code']]


def occupation_dropdown():
    list_of_jobs = ("Student;Computer Science;Natural Science;Social Science;Business;Law;Health-related;"
                    + "Entrepreneur;Looking for one;Actor").split(";")
    return [{'label': i, 'value': i} for i in list_of_jobs]


def household_type_dropdown():
    list_of_household_type = ["Single", "Couple", "Couple with children", "One parent family", "Group"]
    return [{'label': i, 'value': i} for i in list_of_household_type]


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


def radar_attribute(postalcode="02150", column=None):
    """
    Read from the data frame: find the value of the given column for the given postal code,
    and normalize it from 0 to 1 if needed.
    :param postalcode: str, a valid postal code
    :param column: str, a valid complete column name
    :return: a float with the value of the column, or raise Exception
    """
    value = float(get_attribute(postalcode=postalcode, column=column))
    max = paavo_df[column].max()
    min = paavo_df[column].min()
    if "scaled" in column:
        return value
    else:
        return (value - min) / (max - min)


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
    result_income = 100 * float(new_income) / float(old_income)
    if result_income > 0:
        analysis_income = "↗ {:.2f}% potential increase".format(result_income)
    else:
        analysis_income = "↘ {:.2f}% easier life".format(result_income)
    row_income = four_row_list("Income", old_income, new_income, analysis_income)

    # Line 3
    old_education = "{:.2f}".format(
        float(get_attribute(old_code, 'Academic degree - Higher level university degree scaled')) * 100)
    new_education = "{:.2f}".format(
        float(get_attribute(new_code, 'Academic degree - Higher level university degree scaled')) * 100)
    result_education = float(new_education) - float(old_education)
    analysis_education = "↗ Find more skilled fellows" if result_education > 0 else "↘ Less competitions"
    row_education = four_row_list("Education index", old_education, new_education, analysis_education)

    # Line 4

    # url = "https://avoindata.prh.fi/bis/v1?totalResults=true&maxResults=1&resultsFrom=10000" + \
    #       "&streetAddressPostCode={:s}&companyRegistrationFrom=1950-01-01"
    # print("This part takes time (~10s). Comment this part to accelerate. \n(From line 100, reference_function.py)")
    # old_company_num = eval(requests.get(url.format(old_code)).text.split(',"previous')[0] + '}')['totalResults']
    # new_company_num = eval(requests.get(url.format(new_code)).text.split(',"previous')[0] + '}')['totalResults']
    # result_company_num = int(new_company_num) - int(old_company_num)
    # analysis_company_num = "↗ Big town with more opportunities" if result_company_num > 0 else "↘ Peaceful life"
    # row_company_num = four_row_list("Number of companies", old_company_num, new_company_num, analysis_company_num)

    # Final result
    table = [row_title, row_income, row_education]  # , row_company_num]
    return table
