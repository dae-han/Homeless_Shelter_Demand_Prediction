#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sqlalchemy as db
import numpy as np

import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from app import app
from dash.dependencies import Input, Output

from sklearn.model_selection import train_test_split
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error

if 'DYNO' in os.environ:
    app_name = os.environ['DASH_APP_NAME']
else:
    app_name = 'dash-timeseriesplot'

"""Data Query Start"""
# Load your PostgreSQL credential to `database_creds`
database_creds_file = open('../database_cred.json', 'r')
database_creds = json.loads(database_creds_file.read())

# Sign into your database
engine = db.create_engine(database_creds['url'])
connection = engine.connect()
metadata = db.MetaData()

# Run query and return the dataset as Pandas dataframe
sql = """
SELECT *
FROM ny_dhs_weekly
"""
weekly_df = pd.read_sql_query(sql, engine)

# Set 'date_of_census' column as datetime index
weekly_df.index = pd.to_datetime(weekly_df['date_of_census'])
weekly_df = weekly_df.drop('date_of_census', axis = 1)
"""Data Query Done--------------------------------------"""


"""Fit the model"""
# Train / Test dataset split. Test size is 0.25.
train_test_cut = round(weekly_df.shape[0] * 0.75)
train = weekly_df['total_individuals_in_shelter'].iloc[:train_test_cut]
test = weekly_df['total_individuals_in_shelter'].iloc[train_test_cut:]

# Fit the model
model = SARIMAX(endog = train,
                order = (0, 1, 0),              # (p, d, q)
                seasonal_order = (2, 2, 0, 51), # (P, D, Q, S)
                freq = 'W-SUN').fit()
"""Fit the model Done--------------------------------------"""


app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}])

"""Describe the layout/ UI of the app"""
# Add dropdown options
option_list = []
for col in weekly_df.columns:
    elem = {'label': col.replace("_"," "), 'value': col}
    option_list.append(elem)

app.layout = html.Div([
            html.H1("Sheltered Homeless Population Forecast in New York",style={'textAlign': 'center','fontFamily':'georgia'}),

            dcc.Dropdown(id='my-dropdown',
                        options = option_list,
                        multi=True,
                        value=['total_individuals_in_shelter'],
                        style={"display": "block",
                               "margin-left": "auto",
                               "margin-right": "auto",
                               "width": "60%",
                               'fontFamily':'georgia'}),

            html.H3(id = 'message', style={'textAlign': 'center','fontFamily':'georgia'}),

            dcc.Graph(id='my-graph'),

            html.H3 ("Number of weeks to forecast", style={'textAlign': 'center','fontFamily':'georgia', 'margin-top': '0em'}),

            dcc.Slider(id='week-slider',
                       min=0,
                       max=52,
                       value=0,
                       marks={str(week):str(week) for week in range(0,52,5)},
                       updatemode ='drag')

                       ], className="container")
"""Describe the layout/ UI of the app Done----------------------------"""

# Prepare dropdown list
dropdown_dict = {}
for option in option_list:
    dropdown_dict[option['value']] = option['label']

@app.callback([Output('my-graph', 'figure'),
               Output('message', 'children')],
              [Input('my-dropdown', 'value'),
               Input('week-slider','value')])
def update_graph(selected_dropdown_value, num_week_to_predict):
    dropdown = dropdown_dict
    actual = []
    prediction = []
    score = None

    if num_week_to_predict == 0:
        for col_name in selected_dropdown_value:
            actual.append(
            go.Scatter(x = weekly_df.index, \
                       y = weekly_df.loc[:,col_name],
                       mode='lines',
                       opacity=0.7,
                       name=f'Actual {dropdown[col_name]}',
                       textposition='bottom center'))

    elif num_week_to_predict > 0 and len(selected_dropdown_value) == 1:
        for col_name in selected_dropdown_value:
            actual.append(
            go.Scatter(x = weekly_df.index, \
                       y = weekly_df.loc[:,col_name],
                       mode='lines',
                       opacity=0.7,
                       name=f'Actual {dropdown[col_name]}',
                       textposition='bottom center'))

            # Generate predictions based on test set.
            preds = model.predict(start=test.index[0], # X_test data range
                                  end=pd.date_range(start=test.index[-1], periods=num_week_to_predict, freq = 'W-SUN')[-1])

            prediction.append(
            go.Scatter(x = preds.index,
                       y = preds.values,
                       mode='lines',
                       opacity=0.6,
                       name=f'Forecasted number of individuals in shelter',
                       textposition='bottom center'))

        score = f"The forecast has an error range of {int(np.sqrt(mean_squared_error(test, preds[:len(test)])))} people. [Metric: Root mean square error]"

    else:
        prediction = []
        score = "Forecasting is available only for the number of total individuals in shelter at the moment"
        for col_name in selected_dropdown_value:
            actual.append(
            go.Scatter(x = weekly_df.index, \
                       y = weekly_df.loc[:,col_name],
                       mode='lines',
                       opacity=0.7,
                       name=f'Actual {dropdown[col_name]}',
                       textposition='bottom center'))


    traces = [actual, prediction]
    data = [val for sublist in traces for val in sublist]

    figure = {'data': data,
              'layout': go.Layout(
                colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],

                height=600,

                title=f"{', '.join(str(dropdown[i]) for i in selected_dropdown_value)} Over Time",

                xaxis={"title":"Date",
                     'rangeselector': {'buttons': list([{'count': 1, 'label': '1M', 'step': 'month', 'stepmode': 'backward'},{'count': 6, 'label': '6M', 'step': 'month', 'stepmode': 'backward'},{'step': 'all'}])},
                     'rangeslider': {'visible': True},
                     'type': 'date'},

                yaxis={"title":"Population"})}

    return figure, score

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
