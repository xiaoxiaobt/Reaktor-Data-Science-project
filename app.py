import pandas as pd
import json
import dash
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
from toolkits import *

print("Loading data...")
name_geojson = "./data/finland_2019_p4_utf8_simp_wid.geojson"
name_paavo_dataframe = "./data/paavo_9_koko.tsv"  # Requires UTF-8, Tab-seperated, name of postal code column ='id'
# Initialize variables

polygons = json.load(open(name_geojson, "r"))  # It needs to contain "id" feature outside "description"
paavo_df = pd.read_table(name_paavo_dataframe, dtype={"id": object})  # The dtype CANNOT be removed!
paavo_df['text'] = '<b>' + paavo_df.location.astype(str) + '</b><br>' + \
                   "Workplaces: " + paavo_df['Workplaces, 2016 (TP)'].astype(str) + '<br>' + \
                   "Average Income: " + paavo_df['Average income of inhabitants, 2016 (HR)'].astype(str) + '<br>' + \
                   "Students: " + paavo_df['Students, 2016 (PT)'].astype(str)


def instructions():
    return html.P(
        children=[
            """
    - An App provides suggestions for relocation in Finland
    - Otaniemi is the best place to relocate, right?
    - Fill in relavent information below and click "Estimate"
    - Alternatively, search an area by its name or postal code
    """
        ],
        className="instructions-sidebar"
    )


def get_polar_html(r=None):
    if r is None:
        r = [0.84, 0.51, 0.40, 0.76, 0.80]
    polar_plot = go.Scatterpolar(r=r,
                                 theta=['Education', 'Services', 'Transportation', 'Average Income',
                                        'Population Density'],
                                 fill='toself')
    return html.Div(
        children=[
            html.H1("We suggest: Punavuori, 00120", id='suggestion_location_text'),
            html.H2("🛈 Sell price: 7934 €/m²", id="suggestion_price_text"),
            html.H3("Average income: \t39248 €/year", id="suggestion_income_text"),
            html.H3("Average age: \t40", id="suggestion_age_text"),
            html.H3("29.66% of the people has a higher university degree", id="suggestion_degree_text"),
            dcc.Graph(
                id='radar_plot',
                config={'displayModeBar': False},
                figure={
                    'layout': go.Layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    ),
                    'data': [polar_plot]
                }
            )
        ]
    )


def get_about_html():
    text = """
                    This is the implementation of Data Science Project. The aim of this project is to 
                    visualize and get insights on Finland demographics.
                    """
    return html.Div(text)


def get_map_html():
    map_plot = go.Choroplethmapbox(geojson=polygons,
                                   text=paavo_df.text,
                                   locations=paavo_df.id,
                                   z=paavo_df['Surface area'],
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
    text_block = html.Div([
        html.H2("Area: Otaniemi, 02150", id="code_title", style={'color': 'black'}),
        html.H4("🛈 Greetings from Tiger :D ", id="code_info"),
        # html.H4(str(get_amount_of_service()), id="main_info")
    ], style={'display': 'inline-block', 'width': 500}
    )
    map_html = html.Div(
        children=[graph, text_block]
    )
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
app.config.suppress_callback_exceptions = False
app.layout = html.Div(
    children=[
        html.Div(
            [
                html.H1(children="Relocation App (BETA)"),
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
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Income"),
                                dcc.Input(
                                    id="nrows-stitch",
                                    type="number",
                                    value=2000,
                                    name="number of rows",
                                    min=1,
                                    step=1
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
                                    min=1,
                                    step=1
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Family members"),
                                dcc.Input(
                                    id="family_situation",
                                    type="number",
                                    value=5,
                                    name="number of columns",
                                    min=1,
                                    step=1
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Occupation"),
                                dcc.Input(
                                    id="ncolumns-stitch",
                                    type="text",
                                    value="Poor coder",
                                    name="number of rows"
                                ),
                            ]
                        )
                    ],
                    className="mobile_forms",
                ),
                html.Br(),
                html.Button(
                    "Estimate", id="button-stitch", className="button_submit"
                ),
                html.Br(),
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


if __name__ == "__main__":
    app.run_server(debug=False)
