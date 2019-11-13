import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import json
from temp.classifier_dict import return_dict


def main():
    """Run the main interface in web browser"""

    # Initialize file path
    name_geojson = "./data/finland_2016_p4_utf8_simp_wid.geojson"
    name_paavo_dataframe = "./data/paavo_9_koko.tsv"  # Require UTF-8, Tab-seperated, name of postal code column ='id'

    # Initialize variables
    polygons = json.load(open(name_geojson, "r"))  # It needs to contain "id" feature outside "description"
    paavo_df = pd.read_table(name_paavo_dataframe, dtype={"id": str})  # The dtype CANNOT be removed!
    paavo_df['text'] = '<b>' + paavo_df.location.astype(str) + '</b><br>' + \
                       "Workplaces: " + paavo_df['Workplaces, 2016 (TP)'].astype(str) + '<br>' + \
                       "Average Income: " + paavo_df['Average income of inhabitants, 2016 (HR)'].astype(str) + \
                       '<br>' + "Students: " + paavo_df['Students, 2016 (PT)'].astype(str)
    zip_name_dict = dict(zip(paavo_df.id, paavo_df.location))
    cluster_dict = return_dict()

    def find_similar(code):
        for item in cluster_dict:
            if code in cluster_dict[item]:
                return " ".join(cluster_dict[item][:min(5, len(cluster_dict[item]))])
        return "Not Found"

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])  # Create an app

    navbar = html.Div([dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Github", href="https://github.com/xiaoxiaobt/Reaktor-Data-Science-project"))
        ],
        brand="DS Project Demo",
        sticky="top"
    )])

    title = html.H3("Finland Database")

    neighbor_block = html.Div(children='Similar places: ', id='neiblock')

    geograph_block = html.Div([
        dcc.Graph(
            id='main_graph',
            config={'displayModeBar': False}
        )
    ], style={'width': 400, 'height': 700, 'display': 'inline-block'})

    dropdown_block = html.Div([
        dcc.Dropdown(
            id='drop_down_menu',
            options=[{'label': _, 'value': _} for _ in paavo_df.columns[3:]],
            value="Surface area"
        )
    ], style={'width': 400, 'opacity': 0.5, '-webkit-backdrop-filter': "blur(5px)"})

    info = html.Div(children=html.H3('Summary of area 02150, Otaniemi'), id='info_block')

    radar_block = html.Div([
        dcc.Graph(
            id='radar_plot',
            config={'displayModeBar': False}
        )
    ], style={'padding': '0 20', 'size': '3'})

    app.layout = html.Div([
        navbar,
        html.Div([title, geograph_block, dropdown_block], style={'display': 'inline-block', 'padding': '0 20'}),
        html.Div([info, radar_block, neighbor_block], style={'display': 'inline-block', 'padding': '0 20'})])

    @app.callback(
        dash.dependencies.Output('main_graph', 'figure'),
        [dash.dependencies.Input('drop_down_menu', 'value')]
    )
    def update(val):
        data = [go.Choroplethmapbox(geojson=polygons,
                                    text=paavo_df.text,
                                    locations=paavo_df.id,
                                    z=paavo_df[val] if val in paavo_df.columns else paavo_df['Surface area'],
                                    colorscale="Viridis",
                                    marker_opacity=0.5,
                                    marker_line_width=0,
                                    showscale=False)]
        layout = go.Layout(width=400,
                           height=700,
                           mapbox_style="carto-positron",
                           mapbox_zoom=4,
                           mapbox_center={"lat": 65.5, "lon": 25},
                           margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return {'data': data, 'layout': layout}

    @app.callback(
        [dash.dependencies.Output('info_block', 'children'),
         dash.dependencies.Output('neiblock', 'children'),
         dash.dependencies.Output('radar_plot', 'figure')],
        [dash.dependencies.Input('main_graph', 'hoverData')]
    )
    def update(val):
        try:
            pc = val['points'][0]['location']
        except Exception:
            pc = '02150'
        children = html.H3("Summary of area " + pc + ", " + zip_name_dict[pc])
        neighbors = "Similar places: " + find_similar(pc)
        data = [go.Scatterpolar(r=[int(_) for _ in pc],
                                theta=['Education index', 'Price', 'Environment', 'Average Income', 'Transportation'],
                                fill='toself')]
        layout = go.Layout()
        return children, neighbors, {"data": data, "layout": layout}

    app.title = "Data Science Project"
    app.run_server(debug=False)


if __name__ == '__main__':
    main()
