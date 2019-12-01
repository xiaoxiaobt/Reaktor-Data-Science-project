import dash
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
# from toolkits import *
from reference_function import *
from similar_postialue import apply_input

print("Loading data...")
name_geojson = "./data/finland_2019_p4_utf8_simp_wid.geojson"
name_paavo_dataframe = "./dataframes/final_dataframe.tsv"  # Requires UTF-8, Tab-separated, name of postal code column ='Postal code'

# Initialize variables
polygons = json.load(open(name_geojson, "r"))  # It needs to contain "id" feature outside "description"
paavo_df = pd.read_table(name_paavo_dataframe, dtype={"Postal code": object})  # The dtype CANNOT be removed!


def get_instructions():
    return html.P(
        children=[
            """
            - An App that provides suggestions for relocation in Finland
            - Fill the form below and click "Recommend"
            - Alternatively, click on one area
            """
        ],
        className="instructions-sidebar"
    )


def get_polar_html(old_code="02150", new_code="00100"):
    categories = ['Education', 'Services', 'Public Transportation', 'Average Income', 'Population Density']

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(r=radar_attribute(old_code), theta=categories, fill='toself', name='Current location'))
    fig.add_trace(go.Scatterpolar(r=radar_attribute(new_code), theta=categories, fill='toself', name='New location'))

    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=True)

    return html.Div(
        children=[
            html.Div(children=get_analysis(old_code, new_code)),
            dcc.Graph(figure=fig, style={"height": "400px"}, config={'displayModeBar': False})
        ],
        id="analysis_info"
    )


def get_about_html():
    text = """
           This is the implementation of our Data Science Project. The aim of this project is to provide 
           suggestions on suitable relocation areas in Finland, based on housing prices and demographics.
           """
    return html.Div(text)


def get_side_analysis(zip="02150"):
    return [
        html.H2("Area: " + zip_name_dict[zip] + ", " + zip, id="code_title", style={'color': 'black'}),
        html.H2(get_transportation_icons(zip), style={"font-size": "4rem"}),
        html.H2("Municipality tax rate: " + str(zip_tax_dict[zip]) + "%"),
        html.H2("Forest coverage: " + format_2f(get_attribute(zip, "Forest")) + " %"),
        html.H2("Water coverage: " + format_2f(get_attribute(zip, "Water")) + " %")

        # dcc.Graph(figure=get_pie(zip), config={'displayModeBar': False})
        # html.H4("🛈 Greetings from Tiger :D", id="code_info"),
        # html.H4(str(get_amount_of_service()), id="main_info")
    ]


def get_analysis(old_code="02150", new_code="00100"):
    # H1
    location_string = "Hey, how about this one? " + zip_name_dict[new_code] + ", " + new_code
    # H2
    sell_price_string = get_attribute(postalcode=new_code, column="Sell price")
    sell_price_string = format_2f(sell_price_string) if sell_price_string != "0.0" else "--"
    rent_ara_price_string = get_attribute(postalcode=new_code, column="Rent price with ARA")
    rent_ara_price_string = format_2f(rent_ara_price_string) if rent_ara_price_string != "0.0" else "--"
    rent_noara_price_string = get_attribute(postalcode=new_code, column="Rent price without ARA")
    rent_noara_price_string = format_2f(rent_noara_price_string) if rent_noara_price_string != "0.0" else "--"
    trend_near_future_string = "{:+.2f}".format(100 * float(get_attribute(new_code, column="Trend near future")))

    # H3
    # income_string = get_attribute(postalcode=new_code, column="Average income of inhabitants")
    average_age_string = get_attribute(postalcode=new_code, column="Average age of inhabitants")
    # percentage_degree = format_2f(100 * float(get_attribute(postalcode=new_code, column="Academic degree - Higher level university degree scaled")))
    # TODO: Add more relevant info

    text = [html.H1(location_string),
            html.H2("🛈 Last 12 months sell price: " + sell_price_string + " €/m²"),
            html.H2("🛈 Last 12 months rent price: " + rent_ara_price_string + " €/m² (including ARA), "
                    + rent_noara_price_string + " €/m² (private only)"),
            html.H3("Trend of price: \t" + trend_near_future_string + " %"),
            html.H3("Average age: \t" + average_age_string + " years"),
            # html.H3(percentage_degree + "% of the people has a higher university degree")
            ]

    table = make_dash_table(old_code, new_code)
    return text + table


def get_map_html(lat=65.361064, lon=26.985940, zoom=4.0):
    map_plot = go.Choroplethmapbox(geojson=polygons,
                                   text=paavo_df.text,
                                   locations=paavo_df['Postal code'],
                                   z=paavo_df['Trend near future'],
                                   colorscale="Viridis",
                                   marker_opacity=0.7,
                                   marker_line_width=0,
                                   showscale=False
                                   )
    map_layout = go.Layout(width=360,
                           height=600,
                           mapbox_style="carto-positron",
                           mapbox_zoom=zoom,
                           mapbox_center={"lat": lat, "lon": lon},
                           margin={"r": 0, "t": 0, "l": 0, "b": 0}
                           )
    graph = dcc.Graph(id='main_plot',
                      config={'displayModeBar': False},
                      figure={'layout': map_layout, 'data': [map_plot]},
                      style={'display': 'inline-block'},
                      className="left_zone"
                      )
    text_block = html.Div(children=get_side_analysis(), className="side_analysis", id="side_info")
    map_html = html.Div(children=[graph, text_block], id="map_html")
    return map_html


def get_pie(code):
    labels = ['0-15 years', '16-34 years', '35-64 years', '65 years or over']
    nofages = [get_attribute(code, x) for x in labels]
    return go.Figure(go.Pie(labels=labels, values=nofages, showlegend=False, hole=0.6),
                     layout_annotations=[dict(text=age_model(code), x=0.5, y=0.5, font_size=24, showarrow=False)])


print("Loading app...")
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Kodimpi - Data Science Project"
app.layout = html.Div(
    children=[
        html.Div(
            [
                html.Img(src=app.get_asset_url('Kodimpi.png'),
                         style={"height": "113px", "width": "200px", "margin-left": "50px"}),
                # html.H1(children="Kodimpi (BETA)"),
                get_instructions(),
                html.Div(
                    [
                        html.Button("LEARN MORE", className="button_instruction", id="learn-more-button"),
                        html.A(
                            html.Button(
                                "GITHUB", className="demo_button", id="demo"
                            ), href="https://github.com/xiaoxiaobt/Reaktor-Data-Science-project")
                    ],
                    className="mobile_buttons"
                ),
                # Empty child function for the callback
                html.Div(id="demo-explanation", children=[]),
                # TODO: Add callback for instructions
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
                                    id="occupation",
                                    clearable=False,
                                    value="Student",
                                    options=occupation_dropdown(),
                                    className='dropdown'
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Household Size"),
                                dcc.Dropdown(
                                    id="household_type",
                                    clearable=False,
                                    value=1,
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
                html.Div(id="counter", className="0"),
                html.Button("Recommend", id="button-stitch", className="button_submit"),
                # TODO: Disable the button when input is erroneous.
                html.Img(src=app.get_asset_url('logos.png'), style={"height": "162px", "width": "400px"})
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


@app.callback([Output("analysis_info", "children"), Output("stitching-tabs", "value"), Output("counter", "className")],
              [Input("button-stitch", "n_clicks"), Input("main_plot", "clickData")],
              [State('income', 'value'), State('age', 'value'), State('location', 'value'),
               State('occupation', 'value'), State('household_type', 'value'), State('selection_radio', 'value'),
               State("analysis_info", "children"), State("stitching-tabs", "value"), State("counter", "className")])
def change_focus(button_click, map_click, income, age, location, occupation, household_type, selection_radio,
                 analysis_old, tab_old, button_counter):
    if button_click is None:
        button_click = 0
    if int(button_counter) + 1 == button_click:
        if income <= 0 or ~isinstance(income, int):
            income = 10000
        if (age <= 0) or (age >= 120) or ~isinstance(age, int):
            age = 22
        if (location == "") or (location is None) or (location not in list(paavo_df['Postal code'])):
            location = "00930"
        if occupation not in map(dict.keys, occupation_dropdown()):
            occupation = "Student"
        if household_type not in map(dict.keys, household_type_dropdown()):
            household_type = 1
        prediction = str(apply_input(income, age, location, occupation, household_type,
                                     selection_radio))  # get_prediction_model(income, age, location, occupation, household_type, selection_radio)
        print(prediction)
        # This should return a postal code ↑↑↑↑↑↑
        if prediction is None:
            prediction = "00120"
        return get_polar_html(location, prediction), "result-tab", str(int(button_counter) + 1)
    elif map_click is not None:
        pc = map_click['points'][0]['location']
        return get_polar_html("02150", pc), "result-tab", button_counter
    else:
        return analysis_old, tab_old, button_counter


@app.callback(Output('side_info', 'children'), [Input('main_plot', 'hoverData')])
def return_side_analysis(hover_point):
    try:
        pc = hover_point['points'][0]['location']
    except Exception:
        pc = '02150'
    return get_side_analysis(pc)


if __name__ == "__main__":
    app.run_server(debug=False)
