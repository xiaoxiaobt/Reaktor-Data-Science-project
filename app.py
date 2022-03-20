import json
import plotly.graph_objs as go
from dash import dcc, html, Dash
from dash.dependencies import Input, Output, State
from scripts.deployment.reference_function import *
from scripts.deployment.find_similar_postal_area import apply_input

print("Loading data...")
name_geojson = "./data/geographic/finland_2019_p4_utf8_simp_wid.geojson"

# Initialize variables
# It needs to contain "id" feature outside "description"
polygons = json.load(open(name_geojson, "r"))
# paavo_df = pd.read_table("./dataframes/final_dataframe.tsv",
#                          dtype={"Postal code": object})  # Read in reference_function

dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-geo-2.11.0.min.js'


def get_side_analysis(zip="02150"):
    return [
        html.H2(f"Area: {zip_name_dict[zip]}, {zip}", id="code_title"),
        html.H2(get_transportation_icons(zip), id="transportation_icons"),
        html.H2(f"🏢 Municipality tax rate: {zip_tax_dict[zip]}%"),
        html.H2(
            f"🌲 Forest coverage: {float(get_attribute(zip, 'Forest')):.2f}%"),
        html.H2(
            f"🌊 Water coverage: {float(get_attribute(zip, 'Water')):.2f}%")
        # dcc.Graph(figure=get_pie(zip), config={'displayModeBar': False})
        # html.H4(str(get_amount_of_service()), id="main_info")
    ]


def get_polar_html(old_code="02150", new_code="00100"):
    # H1
    location_string = f"Hey, how about this one? {zip_name_dict[new_code]}, {new_code}"
    # H2
    sell_price_string = get_attribute(postalcode=new_code, column="Sell price")
    sell_price_string = f"{float(sell_price_string):.2f}" if sell_price_string != "0.0" else "--"
    rent_ara_price_string = get_attribute(
        postalcode=new_code, column="Rent price with ARA")
    rent_ara_price_string = f"{float(rent_ara_price_string):.2f}" if rent_ara_price_string != "0.0" else "--"
    rent_noara_price_string = get_attribute(
        postalcode=new_code, column="Rent price without ARA")
    rent_noara_price_string = f"{float(rent_noara_price_string):.2f}" if rent_noara_price_string != "0.0" else "--"
    trend_near_future_string = f"{float(get_attribute(new_code, column='Trend near future')):+.2%}"

    # H3
    average_age_string = get_attribute(
        postalcode=new_code, column="Average age of inhabitants")

    categories = ['Education', 'Services', 'Public Transportation',
                  'Average Income', 'Population Density']
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=radar_value(old_code),
                  theta=categories, fill='toself', name='Current location'))
    fig.add_trace(go.Scatterpolar(r=radar_value(new_code),
                  theta=categories, fill='toself', name='New location'))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])),
                      margin={"r": 20, "t": 50, "l": 20, "b": 20})

    return html.Div(
        children=[
            html.H1(location_string),
            html.H2(
                f"🛈 Last 12 months sell price: {sell_price_string} €/m²", id="sell_12"),
            html.H2(
                f"🛈 Last 12 months rent price: {rent_ara_price_string} €/m² (including ARA), {rent_noara_price_string} €/m² (private only)", id="rent_12"),
            html.H3(f"Trend of price: {trend_near_future_string}"),
            html.H3(f"Average age: {average_age_string} years"),
            # html.H3(percentage_degree + "% of the people has a higher university degree"),
            make_dash_table(old_code, new_code),
            dcc.Graph(figure=fig, id="polar_graph",
                      config={'displayModeBar': False})
        ],
        id="analysis_info"
    )


def get_map_html():
    map_plot = go.Choroplethmapbox(geojson=polygons,
                                   hovertemplate=paavo_df.text,
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
                           mapbox_zoom=4.0,
                           mapbox_center={"lat": 65.361064, "lon": 26.985940},
                           margin={"r": 0, "t": 0, "l": 0, "b": 0}
                           )
    graph = dcc.Graph(id='main_plot',
                      config={'displayModeBar': False},
                      figure={'layout': map_layout, 'data': [map_plot]},
                      className="map_main_plot"
                      )
    text_block = html.Div(children=get_side_analysis(),
                          className="side_analysis", id="side_info")
    map_html = html.Div(children=[graph, text_block], id="map_html")
    return map_html


def get_pie(code):
    labels = ['0-15 years', '16-34 years', '35-64 years', '65 years or over']
    nofages = [get_attribute(code, x) for x in labels]
    return go.Figure(go.Pie(labels=labels, values=nofages, showlegend=False, hole=0.6),
                     layout_annotations=[dict(text=age_model(code), x=0.5, y=0.5, font_size=24, showarrow=False)])


print("Loading app...")
app = Dash(__name__,
           suppress_callback_exceptions=True,
           compress=True,
           serve_locally=False,
           title="Kodimpi - Data Science Project",
           meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0, viewport-fit=cover"},
                      {"name": "theme-color", "content": "rgb(78,112,138)"}])
app.server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.index_string = '''
    <!DOCTYPE html>
    <html lang="en">
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
server = app.server  # Required by Heroku

app.layout = html.Div(
    children=[
        html.Div(
            [
                html.Img(src=app.get_asset_url('Kodimpi.png'),
                         id="logo", alt="Kodimpi logo"),
                get_instructions(),
                html.Div(
                    [
                        html.A(
                            html.Button(
                                "PRESENTATION", className="button_instruction"
                            ), href="https://docs.google.com/presentation/d/1UxK_5VFOWXF3Ni_3pTustceeMWMWMBmiT3ZiNMB7xNs/edit?usp=sharing"),
                        html.A(
                            html.Button(
                                "GITHUB", className="github_button"
                            ), href="https://github.com/xiaoxiaobt/Reaktor-Data-Science-project")
                    ],
                    className="mobile_buttons"
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Yearly income", htmlFor="income"),
                                dcc.Input(
                                    id="income",
                                    type="number",
                                    value=10000,
                                    min=10000,
                                    step=1000
                                )
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Age", htmlFor="age"),
                                dcc.Input(
                                    id="age",
                                    type="number",
                                    value=22,
                                    min=1
                                )
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Current Location",
                                           htmlFor="location"),
                                dcc.Dropdown(
                                    id="location",
                                    clearable=False,
                                    value="02150",
                                    options=location_dropdown,
                                    className='dropdown'
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Occupation", htmlFor="occupation"),
                                dcc.Dropdown(
                                    id="occupation",
                                    clearable=False,
                                    value="Student",
                                    options=occupation_dropdown,
                                    className='dropdown'
                                )
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Household Size",
                                           htmlFor="household_type"),
                                dcc.Dropdown(
                                    id="household_type",
                                    clearable=False,
                                    value=1,
                                    options=household_type_dropdown,
                                    className='dropdown'
                                )
                            ]
                        ),
                        html.Div([
                            html.Label("Moving options",
                                       htmlFor="selection_radio"),
                            dcc.RadioItems(
                                options=[
                                    {'label': 'Faraway from current location',
                                        'value': 'change'},
                                    {'label': 'Close to current location',
                                        'value': 'nochange'},
                                    {'label': 'Whatever', 'value': 'whatever'}
                                ],
                                value='whatever',
                                id="selection_radio"
                            )
                        ]),
                        html.Br(),
                        html.Div(id="counter", className="0"),
                        html.Button("Recommend", id="button-stitch",
                                    className="button_submit")
                    ],
                    className="mobile_forms"
                )
            ],
            className="four columns instruction"
        ),
        html.Div(
            dcc.Tabs(
                children=[
                    dcc.Tab(label="MAP", value="canvas-tab",
                            children=[get_map_html()]),
                    dcc.Tab(label="ANALYSIS", value="result-tab",
                            children=[get_polar_html()]),
                    dcc.Tab(label="ABOUT", value="about-tab",
                            children=[get_about_html()])
                ],
                id="stitching-tabs",
                value="canvas-tab",
                className="tabs"
            ),
            className="eight columns result"
        )
    ],
    className="row twelve columns"
)


@app.callback([Output("analysis_info", "children"), Output("stitching-tabs", "value"),
               Output("counter", "className")],
              [Input("button-stitch", "n_clicks"),
               Input("main_plot", "clickData")],
              [State('income', 'value'), State('age', 'value'), State('location', 'value'),
               State('occupation', 'value'), State('household_type', 'value'),
               State('selection_radio', 'value'), State(
                   "analysis_info", "children"),
               State("stitching-tabs", "value"), State("counter", "className")])
def change_focus(button_click, map_click, income, age, location, occupation, household_size,
                 selection_radio, analysis_old, tab_old, button_counter):
    if button_click is None:
        button_click = 0
    if int(button_counter) + 1 == button_click:
        if income is None or income <= 0:
            income = 10000
        if 0 < age < 120:
            age = round(age)
        else:
            age = 22
        if (location is None) or (location == "") or (location not in list(paavo_df['Postal code'])):
            location = "00930"
        if occupation not in list_of_jobs:
            occupation = "Student"
        if household_size not in list_of_household_type:
            household_size = 1
        prediction = str(apply_input(income, age, location,
                         occupation, household_size, selection_radio))
        # This should return a postal code ↑↑↑↑↑↑
        if prediction is None:
            prediction = "00120"
            print("WARNING: NO PREDICTION GIVEN")
        print(f"Prediction: {prediction}")
        return get_polar_html(location, prediction).children, "result-tab", str(int(button_counter) + 1)
    elif map_click is not None:
        pc = map_click['points'][0]['location']
        return get_polar_html("02150", pc).children, "result-tab", button_counter
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
