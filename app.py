import pandas as pd
import json
import dash
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
# from toolkits import *
from temp.reference_function import *

print("Loading data...")
name_geojson = "./data/finland_2019_p4_utf8_simp_wid.geojson"
name_paavo_dataframe = "./dataframes/final_dataframe.tsv"  # Requires UTF-8, Tab-separated, name of postal code column ='Postal code'
# Initialize variables

polygons = json.load(open(name_geojson, "r"))  # It needs to contain "id" feature outside "description"
paavo_df = pd.read_table(name_paavo_dataframe, dtype={"Postal code": object})  # The dtype CANNOT be removed!


def instructions():
    return html.P(
        children=[
            """
            - An App that provides suggestions for relocation in Finland
            - Otaniemi is the best place to relocate, right?
            - Fill the form below and click "Estimate"
            - Alternatively, search an area by its name or postal code
            """
        ],
        className="instructions-sidebar"
    )


def get_polar_html(code=None):
    if code is None:
        code = "02150"
    r = [radar_attribute(postalcode=code, column="Academic degree - Higher level university degree scaled"),
         radar_attribute(postalcode=code, column="Services"),
         radar_attribute(postalcode=code, column="Bus stops"),
         radar_attribute(postalcode=code, column="Average income of inhabitants"),
         radar_attribute(postalcode=code, column="Density")]
    polar_plot = go.Scatterpolar(r=r,
                                 theta=['Education', 'Services', 'Public Transportation', 'Average Income',
                                        'Population Density'],
                                 fill='toself')
    return html.Div(
        children=[
            html.Div(children=get_analysis(code, "00100"), id="info_text"),
            # TODO: Get the new code from prediction
            dcc.Graph(
                id='radar_plot',
                config={'displayModeBar': False},
                figure={
                    'layout': go.Layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'),
                    'data': [polar_plot]
                }
            )
        ]
    )


def get_about_html():
    text = """
                    This is the implementation of our Data Science Project. The aim of this project is to provide 
                    suggestions on suitable relocation areas in Finland, based on housing prices and demographics.
                    """
    return html.Div(text)


def get_side_analysis():
    return [
        html.H2("Area: Otaniemi, 02150", id="code_title", style={'color': 'black'}),
        html.H4("🛈 Greetings from Tiger :D ", id="code_info"),
        html.H2(get_transportation_icons("02150"), style={"font-size": "4rem"})
        # html.H4(str(get_amount_of_service()), id="main_info")
    ]


def get_analysis(old_code="02150", new_code="00100"):
    # H1
    location_string = "Hey, how about this one? " + zip_name_dict()[new_code] + ", " + new_code
    # H2
    sell_price_string = get_attribute(postalcode=new_code, column="Sell price")
    sell_price_string = format_2f(sell_price_string) if sell_price_string != "0.0" else "--"
    rent_ara_price_string = get_attribute(postalcode=new_code, column="Rent price with ARA")
    rent_ara_price_string = format_2f(rent_ara_price_string) if rent_ara_price_string != "0.0" else "--"
    rent_noara_price_string = get_attribute(postalcode=new_code, column="Rent price without ARA")
    rent_noara_price_string = format_2f(rent_noara_price_string) if rent_noara_price_string != "0.0" else "--"
    # H3
    income_string = get_attribute(postalcode=new_code, column="Average income of inhabitants")
    average_age_string = get_attribute(postalcode=new_code, column="Average age of inhabitants")
    percentage_degree = format_2f(
        100 * float(
            get_attribute(postalcode=new_code, column="Academic degree - Higher level university degree scaled")))
    # TODO: Add more relevant info

    text = [html.H1(location_string),
            html.H2("🛈 Last 12 months sell price: " + sell_price_string + " €/m²"),
            html.H2("🛈 Last 12 months rent price: " + rent_ara_price_string + " €/m² (including ARA), "
                    + rent_noara_price_string + " €/m² (private only)"),
            html.H3("Average income: \t" + income_string + " €/year"),
            html.H3("Average age: \t" + average_age_string + " years"),
            # html.H3(percentage_degree + "% of the people has a higher university degree")
            ]

    table = make_dash_table(old_code, new_code)
    return text + table


def get_map_html():
    map_plot = go.Choroplethmapbox(geojson=polygons,
                                   text=paavo_df.text,
                                   locations=paavo_df['Postal code'],
                                   z=paavo_df['Surface area'],
                                   # TODO: Replace representation
                                   colorscale="Viridis",
                                   marker_opacity=0.7,
                                   marker_line_width=0,
                                   showscale=False,
                                   )
    map_layout = go.Layout(width=360,
                           height=600,
                           mapbox_style="carto-positron",
                           mapbox_zoom=4,
                           mapbox_center={"lat": 65.361064, "lon": 26.985940},
                           margin={"r": 0, "t": 0, "l": 0, "b": 0}
                           )
    graph = dcc.Graph(id='main_plot',
                      config={'displayModeBar': False},
                      figure={'layout': map_layout, 'data': [map_plot]},
                      style={'display': 'inline-block'},
                      className="left_zone"
                      )
    text_block = html.Div(children=get_side_analysis(), className="side_analysis", id="side_info")
    # test_DONOTREMOVE = html.Div(children=[html.H1("dfnsjkbfjds")], style={'display': 'inline-block'})
    map_html = html.Div(children=[graph, text_block])
    return map_html


height, width = 200, 500
canvas_width = 800
scale = canvas_width / width
canvas_height = round(height * scale)
list_columns = ["length", "width", "height", "left", "top"]
columns = [{"name": i, "id": i} for i in list_columns]

print("Loading app...")
app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
server = app.server
app.title = "Kodimpi - Data Science Project"
app.config.suppress_callback_exceptions = False
app.layout = html.Div(
    children=[
        html.Div(
            [
                html.H1(children="Kodimpi (BETA)"),
                instructions(),
                html.Div(
                    [
                        html.Button(
                            "LEARN MORE",
                            className="button_instruction",
                            id="learn-more-button"
                        ),
                        html.A(
                            html.Button(
                                "GITHUB", className="demo_button", id="demo"
                            ), href="https://github.com/xiaoxiaobt/Reaktor-Data-Science-project")
                    ],
                    className="mobile_buttons"
                ),
                html.Div(
                    # Empty child function for the callback
                    html.Div(id="demo-explanation", children=[])
                    # TODO: Add callback for instructions
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Yearly income"),
                                dcc.Input(
                                    id="income",
                                    type="number",
                                    value=10000,
                                    name="number of rows",
                                    min=10000,
                                    step=1000
                                )
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Age"),
                                dcc.Input(
                                    id="age",
                                    type="number",
                                    value=22,
                                    name="number of rows",
                                    min=1
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Current Location"),
                                dcc.Dropdown(
                                    id="location",
                                    clearable=False,
                                    value="02150",
                                    options=location_dropdown(),
                                    className='dropdown'
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Occupation"),
                                dcc.Dropdown(
                                    id="Occupation",
                                    clearable=False,
                                    value="Student",
                                    options=occupation_dropdown(),
                                    className='dropdown'
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Household type"),
                                dcc.Dropdown(
                                    id="household_type",
                                    clearable=False,
                                    value="Single",
                                    options=household_type_dropdown(),
                                    className='dropdown'
                                ),
                            ]
                        ),
                        html.Div([
                            html.Label("Moving options"),
                            dcc.RadioItems(
                                options=[
                                    {'label': 'Faraway from current location', 'value': 'change'},
                                    {'label': 'Close to current location', 'value': 'nochange'},
                                    {'label': 'Whatever', 'value': 'whatever'}
                                ],
                                value='whatever',
                                id="selection_radio"
                            )
                        ])
                    ],
                    className="mobile_forms"
                ),
                html.Br(),
                html.Button("Estimate", id="button-stitch", className="button_submit"),
                # TODO: Disable the button when input is erroneous.
                html.Img(src=app.get_asset_url('logos.png'))
            ],
            className="four columns instruction"
        ),
        html.Div(
            [
                dcc.Tabs(
                    id="stitching-tabs",
                    value="canvas-tab",
                    children=[
                        dcc.Tab(label="MAP", value="canvas-tab", children=[get_map_html()]),
                        dcc.Tab(label="ANALYSIS", value="result-tab", children=[get_polar_html()]),
                        dcc.Tab(label="ABOUT", value="help-tab", children=[get_about_html()]),
                        dcc.Tab(label="TEAM", value="team-tab",
                                children=[html.Div("Roope, Trang, Thong, Letizia, Taige")])
                    ],
                    className="tabs"
                )
            ],
            className="eight columns result"
        )
    ],
    className="row twelve columns"
)


@app.callback(Output("stitching-tabs", "value"), [Input("button-stitch", "n_clicks")])
def change_focus(click):
    return "result-tab" if click else "canvas-tab"


"""
@app.callback(Output("stitching-tabs", "value"), [Input("button-stitch", "n_clicks")])
def predict():
    pass
"""

if __name__ == "__main__":
    app.run_server(debug=True)
