import pandas as pd
import json
import dash
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import toolkits

print("Loading data...")
name_geojson = "./data/finland_2019_p4_utf8_simp_wid.geojson"
name_paavo_dataframe = "./data/paavo_9_koko.tsv"  # Require UTF-8, Tab-seperated, name of postal code column ='id'
# Initialize variables

polygons = json.load(open(name_geojson, "r"))  # It needs to contain "id" feature outside "description"
paavo_df = pd.read_table(name_paavo_dataframe, dtype={"id": str})  # The dtype CANNOT be removed!
paavo_df['text'] = '<b>' + paavo_df.location.astype(str) + '</b><br>' + \
                   "Workplaces: " + paavo_df['Workplaces, 2016 (TP)'].astype(str) + '<br>' + \
                   "Average Income: " + paavo_df['Average income of inhabitants, 2016 (HR)'].astype(str) + \
                   '<br>' + "Students: " + paavo_df['Students, 2016 (PT)'].astype(str)


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
        className="instructions-sidebar",
    )


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
                        dcc.Tab(label="MAP", value="canvas-tab"),
                        dcc.Tab(label="ANALYSIS", value="result-tab"),
                        dcc.Tab(label="ABOUT", value="help-tab"),
                        dcc.Tab(label="TEAM", value="team-tab")
                    ],
                    className="tabs"
                ),
                html.Div(
                    id="tabs-content-example",
                    className="canvas",
                    style={"text-align": "left", "margin": "auto", "opacity": 0.8, 'paper_bgcolor': 'rgba(0,0,0,0)',
                           "plot_bgcolor": 'rgba(0,0,0,0)'}
                ),
                html.Div(className="upload_zone", id="upload-stitch", children=[]),
                html.Div(id="sh_x", hidden=False),
                html.Div(id="stitched-res", hidden=False),
                dcc.Store(id="memory-stitch")
            ],
            className="eight columns result"
        ),
    ],
    className="row twelve columns"
)


@app.callback(Output("stitching-tabs", "value"), [Input("button-stitch", "n_clicks")])
def change_focus(click):
    return "result-tab" if click else "canvas-tab"


@app.callback(
    Output("tabs-content-example", "children"), [Input("stitching-tabs", "value")]
)
def fill_tab(tab):
    if tab == "result-tab":
        polar_plot = go.Scatterpolar(r=[0, 2, 1, 5, 0],
                                     theta=['Education', 'Services', 'Transportation', 'Average Income',
                                            'Population Density'],
                                     fill='toself')
        polar_html = html.Div(
            children=[
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

        return polar_html
    elif tab == "canvas-tab":
        map_plot = go.Choroplethmapbox(geojson=polygons,
                                       text=paavo_df.text,
                                       locations=paavo_df.id,
                                       z=paavo_df['Surface area'],
                                       colorscale="Viridis",
                                       marker_opacity=0.5,
                                       marker_line_width=0,
                                       showscale=False,
                                       )
        map_layout = go.Layout(  # width=300,
            height=600,
            mapbox_style="carto-positron",
            mapbox_zoom=7,
            mapbox_center={"lat": 60.552778, "lon": 24.966389},
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
        map_html = html.Div(
            children=[
                dcc.Graph(
                    id='main_plot',
                    config={'displayModeBar': False},
                    figure={
                        'layout': map_layout,
                        'data': [map_plot]
                    }
                )
            ]
        )
        return map_html
    elif tab == "help-tab":
        text = """
                This is the implementation of Data Science Project. The aim of this project is to 
                visualize and get insights on Finland demographics.
                """
        return [html.Div(text)]
    else:
        return [html.Div("Roope, Trang, Thong, Letizia, Taige")]


if __name__ == "__main__":
    app.run_server(debug=True)
