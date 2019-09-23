import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import json


def main():
    app = dash.Dash(__name__, external_stylesheets=["template.css"])
    posti_alue = json.load(open("idchanged.json", "r"))
    dfe = pd.read_csv("paavo_9_koko.tsv", sep="\t", dtype={"id": str})
    loc_id = dfe.id
    app.layout = html.Div([

        html.Div([
            html.H3("Finland Database"),
            dcc.Graph(
                id='main_graph'
            )
        ], style={'width': 410, 'height': 700, 'mapbox_style': "carto-positron", 'mapbox_zoom': 4,
                  'mapbox_center': {"lat": 65.5, "lon": 25}, 'margin': {"r": 0, "t": 0, "l": 0, "b": 0}}),
        html.Div([
            dcc.Dropdown(
                id='drop_down_menu',
                options=[{'label': i, 'value': i} for i in dfe.columns[3:]],
                value="Surface area"
            )
        ], style={'width': 300, 'opacity': 0.5, '-webkit-backdrop-filter': "blur(5px)"}),
    ])

    @app.callback(
        dash.dependencies.Output('main_graph', 'figure'),
        [dash.dependencies.Input('drop_down_menu', 'value')]
    )
    def update(val):
        return {'data': [go.Choroplethmapbox(geojson=posti_alue, locations=loc_id, z=dfe[val],
                                             colorscale="Viridis", marker_opacity=0.5, marker_line_width=0)],
                'layout': go.Layout(
                    width=410,
                    height=700,
                    mapbox_style="carto-positron",
                    mapbox_zoom=4,
                    mapbox_center={"lat": 65.5, "lon": 25},
                    margin={"r": 0, "t": 0, "l": 0, "b": 0}
                )
                }

    app.run_server(debug=True)


if __name__ == '__main__':
    main()
