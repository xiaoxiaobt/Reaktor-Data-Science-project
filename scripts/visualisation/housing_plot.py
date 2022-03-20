import numpy as np
import plotly.graph_objects as go

def housing_plot(housing_data_df, housing_prediction_df, code):
    observation_df = housing_data_df
    prediction_df = housing_prediction_df

    # Extract the row of the postal code, format the postal code values
    def prepare_df(df):
        df = df.astype({'Postal code': str})
        for i in list(df.index):
            df.at[i, 'Postal code'] = '0' * (5 - len(df.at[i, 'Postal code'])) + df.at[i, 'Postal code']
        df.set_index('Postal code', inplace=True)
        df = df.loc[[code]]
        return df

    observation_df = prepare_df(observation_df)
    prediction_df = prepare_df(prediction_df)

    # Group data columns
    lower_10_columns = prediction_df.columns[prediction_df.columns.str.startswith('Lower_10')]
    upper_10_columns = prediction_df.columns[prediction_df.columns.str.startswith('Upper_10')]
    lower_25_columns = prediction_df.columns[prediction_df.columns.str.startswith('Lower_25')]
    upper_25_columns = prediction_df.columns[prediction_df.columns.str.startswith('Upper_25')]
    prediction_columns = prediction_df.columns[prediction_df.columns.str.startswith('20')]

    # Create different data arrays for plotting
    lower_10_df = prediction_df[lower_10_columns]
    upper_10_df = prediction_df[upper_10_columns]
    lower_25_df = prediction_df[lower_25_columns]
    upper_25_df = prediction_df[upper_25_columns]
    prediction_df = prediction_df[prediction_columns]

    # Create time arrays for the x axis
    observation_time = np.arange(2005, 2018, 0.25)
    prediction_time = np.arange(2005.25, 2021, 0.25)
    forecast_time = np.arange(2018, 2021, 0.25)

    # Extract the data as np.array for the plot
    observation = observation_df.loc[code].values
    prediction = prediction_df.loc[code].values
    lower_10 = lower_10_df.loc[code].values
    upper_10 = upper_10_df.loc[code].values
    lower_25 = lower_25_df.loc[code].values
    upper_25 = upper_25_df.loc[code].values

    # Create time tags for the hover text
    hover_text=[]
    for year in range(2005, 2021):
        for quarter in range(1,5):
            hover_text.append(str(year) + 'Q' + str(quarter))

    hover_text_obs = hover_text[:len(observation_time)]
    hover_text_prediction = hover_text[1:(len(prediction_time)+1)]
    hover_text_forecast = hover_text[:-(len(forecast_time))]

    # Template for hover text
    hover_template = '<b>%{text}</b>' + '<br><i>Price</i>: €%{y:.2f}<br>'

    # Create features for the plot
    observation_line = go.Scatter(x=observation_time, y=observation, mode='lines', hovertemplate = hover_template,  text = hover_text_obs, name='Observation')
    prediction_line = go.Scatter(x=prediction_time, y=prediction, mode='lines', hovertemplate = hover_template, text = hover_text_prediction, name='Prediction')
    lower_10_bound = go.Scatter(x=forecast_time, y=lower_10, mode='lines', hovertemplate = hover_template, text = hover_text_forecast, marker=dict(color="#444"), line=dict(width=0), showlegend=False, name='90% Confidence')
    upper_10_bound = go.Scatter(x=forecast_time, y=upper_10, mode='lines', hovertemplate = hover_template, text = hover_text_forecast, marker=dict(color="#444"), line=dict(width=0), showlegend=False, fillcolor='rgba(68, 68, 68, 0.3)', fill='tonexty', name='90% Confidence')
    lower_25_bound = go.Scatter(x=forecast_time, y=lower_25, mode='lines', hovertemplate = hover_template, text = hover_text_forecast, marker=dict(color="#444"), line=dict(width=0), showlegend=False, name='75% Confidence')
    upper_25_bound = go.Scatter(x=forecast_time, y=upper_25, mode='lines', hovertemplate = hover_template, text = hover_text_forecast, marker=dict(color="#444"), line=dict(width=0), showlegend=False, fillcolor='rgba(68, 68, 68, 0.3)', fill='tonexty', name='75% Confidence')

    features = [observation_line, prediction_line, lower_25_bound, upper_25_bound, lower_10_bound, upper_10_bound]

    # Create the plot object, adjust axes
    fig = go.Figure(data=features)
    fig.update_xaxes(range=[2004, 2022], title_text='Year')
    fig.update_yaxes(title_text='Price')

    return fig
