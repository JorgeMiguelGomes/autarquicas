# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import os, re, time, json
import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from flask_caching import Cache


BASE_PATH = os.path.dirname(os.path.dirname(__file__))
ALL_YEARS = list(range(2009,2023,4))

app = dash.Dash(__name__)

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': os.path.join(BASE_PATH, 'dash_plotly','cache'),
})


TIMEOUT = 60

@cache.memoize(timeout=TIMEOUT)
def dataframe():
    dfs = {}
    for yr in ALL_YEARS:
        dfs[yr] = pd.read_csv(
            os.path.join(BASE_PATH,f"final_csv/autarquicas_{yr}_treated.csv"),
            index_col='Unnamed: 0'
        ) 
    return pd.concat([dfs[yr] for yr in ALL_YEARS], ignore_index=True)

gped_df = dataframe().groupby(['party','year']).sum()

gped_df = pd.DataFrame([[
    ia,ib,v] for (ia,ib),v in zip(gped_df.index,gped_df['votes.mandates'])],
    columns=['party', 'year','votes.mandates'])

fig = px.bar(gped_df, x="year", y="votes.mandates", color="party")

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
