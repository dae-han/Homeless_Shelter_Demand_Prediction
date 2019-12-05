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

if 'DYNO' in os.environ:
    app_name = os.environ['DASH_APP_NAME']
else:
    app_name = 'dash-timeseriesplot'

"""Data Query Start--------------------------------------"""
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

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}])

"""Describe the layout/ UI of the app----------------------------"""
# Add dropdown options
option_list = []
for col in weekly_df.columns:
    elem = {'label': col.replace("_"," "), 'value': col}
    option_list.append(elem)

app.layout = html.Div([
            html.H1("Sheleterd Homeless Population Forecast in New York",style={'textAlign': 'center','fontFamily':'georgia'}),

            dcc.Dropdown(id='my-dropdown',
                        options = option_list,
                        multi=True,
                        value=['total_individuals_in_shelter'],
                        style={"display": "block",
                               "margin-left": "auto",
                               "margin-right": "auto",
                               "width": "60%",
                               'fontFamily':'georgia'}),

            dcc.Graph(id='my-graph'),
            html.H3("Number of weeks to forecast", style={'textAlign': 'center','fontFamily':'georgia', 'margin-top': '0em'}),
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

@app.callback(Output('my-graph', 'figure'),
              [Input('my-dropdown', 'value')])
def update_graph(selected_dropdown_value):
    dropdown = dropdown_dict
    actual = []
    # prediction = []
    for col_name in selected_dropdown_value:
        actual.append(
        go.Scatter(x = weekly_df.index, \
                   y = weekly_df.loc[:,col_name],
                   mode='lines',
                   opacity=0.7,
                   name=f'Actual {dropdown[col_name]}',
                   textposition='bottom center'))

        # trace2.append(
        # go.Scatter(x=df[df["Stock"] == stock]["Date"],
        #            y=df[df["Stock"] == stock]["Close"],
        #            mode='lines',
        #            opacity=0.6,
        #            name=f'Predicted {dropdown[stock]}',
        #            textposition='bottom center'))

    traces = [actual]
    data = [val for sublist in traces for val in sublist]

    figure = {'data': data,
              'layout': go.Layout(
                colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],

                height=600,

                title=f"Population of {', '.join(str(dropdown[i]) for i in selected_dropdown_value)} Over Time",

                xaxis={"title":"Date",
                     'rangeselector': {'buttons': list([{'count': 1, 'label': '1M', 'step': 'month', 'stepmode': 'backward'},{'count': 6, 'label': '6M', 'step': 'month', 'stepmode': 'backward'},{'step': 'all'}])},
                     'rangeslider': {'visible': True},
                     'type': 'date'},

                yaxis={"title":"Population"})}
    return figure

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
