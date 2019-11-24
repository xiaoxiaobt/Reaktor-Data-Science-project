import numpy as np
import pandas as pd
import os
from statsmodels.tsa.arima_model import ARIMA


def housing_data_predict(destination_directory, paavo_housing_quarterly):
    years = range(2005, 2021)
    housing_obs = pd.read_csv(paavo_housing_quarterly, sep='\t')
    housing_obs = housing_obs.astype({'Postal code': str})
    for i in list(housing_obs.index):
        housing_obs.at[i, 'Postal code'] = '0' * (5 - len(housing_obs.at[i, 'Postal code'])) + housing_obs.at[i, 'Postal code']

    # Create initial data frame for storing the prediction
    housing_pred = housing_obs[['Postal code']]

    housing_obs.set_index('Postal code', inplace=True)
    housing_pred.set_index('Postal code', inplace=True)

    housing_obs = housing_obs.transpose()

    # Add columns to the prediction data frame
    for year in years:
        for quarter in range(1, 5):
            ncolumns = len(housing_pred.columns)
            housing_pred.insert(ncolumns, str(year) + 'Q' + str(quarter), np.nan)
            if year > 2017:
                housing_pred.insert(ncolumns + 1, 'Lower_10 ' + str(year) + 'Q' + str(quarter), np.nan)
                housing_pred.insert(ncolumns + 2, 'Upper_10 ' + str(year) + 'Q' + str(quarter), np.nan)
                housing_pred.insert(ncolumns + 3, 'Lower_25 ' + str(year) + 'Q' + str(quarter), np.nan)
                housing_pred.insert(ncolumns + 4, 'Upper_25 ' + str(year) + 'Q' + str(quarter), np.nan)

    # Use ARIMA(0, 1, 1) for prediction, fill the data frame with predictions and prediction intervals of 90% and 75%
    for code in housing_obs.columns:
        X = housing_obs[code].values
        X = X.astype('float32')
        model = ARIMA(X, order=(0, 1, 1))
        model_fit = model.fit(disp=-1, start_ar_lags=2)

        # Calculate in-sample predictions
        in_sample = model_fit.predict(end=len(X))
        for i in range(0, len(in_sample)):
            if i < len(X):
                in_sample[i] = in_sample[i] + X[i]
            else:
                in_sample[i] = in_sample[i] + in_sample[i - 1]

        # Prediction intervals for forecast values
        forecast_result_10 = model_fit.forecast(12, alpha=0.1)
        forecast_result_25 = model_fit.forecast(12, alpha=0.25)

        forecast = np.array(forecast_result_10[0])
        predictions = np.concatenate([in_sample, forecast])

        # Filling the data frame
        for year in years:
            for quarter in range(1,5):
                pos = (year - 2005) * 4 + quarter - 1
                housing_pred.at[code, str(year) + 'Q' + str(quarter)] = int(predictions[pos])
                if year > 2017:
                    forecast_pos = (year - 2018) * 4 + quarter - 1
                    housing_pred.at[code, 'Lower_10 ' + str(year) + 'Q' + str(quarter)] = int(forecast_result_10[2][forecast_pos][0])
                    housing_pred.at[code, 'Upper_10 ' + str(year) + 'Q' + str(quarter)] = int(forecast_result_10[2][forecast_pos][1])
                    housing_pred.at[code, 'Lower_25 ' + str(year) + 'Q' + str(quarter)] = int(forecast_result_25[2][forecast_pos][0])
                    housing_pred.at[code, 'Upper_25 ' + str(year) + 'Q' + str(quarter)] = int(forecast_result_25[2][forecast_pos][1])

    # Export to tsv file
    housing_pred.to_csv(os.path.join(destination_directory, 'paavo_housing_quarterly_prediction.tsv'), sep='\t')
