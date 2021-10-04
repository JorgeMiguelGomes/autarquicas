# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import os
import re
import time
import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
from flask_caching import Cache


BASE_PATH = os.path.dirname(os.path.dirname(__file__))
ALL_YEARS = list(range(2009, 2023, 4))

app = dash.Dash(__name__)

cache = Cache(app.server, config={
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": os.path.join(BASE_PATH, "dash", "cache"),
})

DROPDOWN_OPTIONS = [
    {"label": "Has Absolute Majority",
        "value": "votesAbsoluteMajority", "canColor": True},
    {"label": "Mandate votes", "value": "votesMandates", "canY": True},
    {"label": "Votes in %", "value": "votesPercentage",
        "canY": True},
    {"label": "is President vote", "value": "votesPresidents", "canColor": True},
    {"label": "Votes", "value": "votesVotes", "canY": True},
    {"label": "County", "value": "county", "canX": True, "canColor": True},
    {"label": "District", "value": "district", "canX": True, "canColor": True},
    {"label": "Has available mandates?",
        "value": "availableMandates", "canColor": True},
    {"label": "Blank votes", "value": "blankVotes", "canY": True},
    {"label": "Blank votes %", "value": "blankVotesPercentage", "canY": True},
    {"label": "Null votes", "value": "nullVotes", "canY": True},
    {"label": "Null votes %", "value": "nullVotesPercentage", "canY": True},
    {"label": "Number of Parishes", "value": "numberParishes", "canY": True},
    {"label": "Number of Voters", "value": "numberVoters", "canY": True},
    {"label": "Percentage of Voters", "value": "percentageVoters", "canY": True},
    {"label": "Candidate", "value": "candidate", "canX": True},
    {"label": "Year", "value": "year", "canX": True, "canColor": True},
    {"label": "Valid votes in %", "value": "votesValidVotesPercentage", "canY": True},
    {"label": "Coalition", "value": "coalition", "canX": True, "canColor": True},
    {"label": "Parties", "value": "parties", "canX": True, "canColor": True}
]

TIMEOUT = None  # data won't change


@cache.memoize(timeout=TIMEOUT)
def dataframe():
    return pd.read_csv(os.path.join(
        BASE_PATH, "cleaning/autarquicas_treated.csv"
    ))


app.layout = html.Div(children=[
    html.H1(children="Portugal Local Election Results"),

    html.Div(children="""
        Plots of Portugal local election results from 2009 to 2021.
    """),

    html.Div([
        html.Div([
            html.P("X axis attribute"),
            dcc.Dropdown(
                id="xAxis",
                options=[
                    {"label": r["label"], "value":r["value"]}
                    for r in DROPDOWN_OPTIONS if "canX" in r
                ],
                value="year")],
            style={'width': '33%', 'display': 'inline-block'}
        ),
        html.Div([
            html.P("Y axis attribute"),
            dcc.Dropdown(
                id="yAxis",
                options=[
                    {"label": r["label"], "value":r["value"]}
                    for r in DROPDOWN_OPTIONS if "canY" in r
                ],
                value="numberVoters")],
            style={'width': '33%', 'display': 'inline-block'}
        ),
        html.Div([
            html.P("Color/Group attribute"),
            dcc.Dropdown(
                id="colorGroup",
                options=[
                    {"label": r["label"], "value":r["value"]}
                    for r in DROPDOWN_OPTIONS if "canColor" in r and r["value"] != "year"
                ],
                value="county")],
            style={'width': '33%', 'display': 'inline-block'}
        )
    ]),

    dcc.Graph(
        id="main-graph",
    )
])


@app.callback(
    Output("colorGroup", "options"),
    Input("xAxis", "value")
)
def update_color_group(x_col_name):
    new_color_options = [
        {"label": r["label"], "value":r["value"]}
        for r in DROPDOWN_OPTIONS if "canColor" in r and r["value"] != x_col_name
    ]
    return new_color_options


@app.callback(
    Output("main-graph", "figure"),
    [Input("xAxis", "value"),
     Input("yAxis", "value"),
     Input("colorGroup", "value")]
)
def update_graph(x_col_name, y_col_name, color_col_name):
    gped_df = dataframe().groupby([x_col_name, color_col_name]).sum()

    gped_df = pd.DataFrame([[
        ia, ib, v] for (ia, ib), v in zip(gped_df.index, gped_df[y_col_name])],
        columns=[x_col_name, color_col_name, y_col_name])

    fig = px.bar(gped_df, x=x_col_name, y=y_col_name, color=color_col_name,
                 labels={r['value']: r['label'] for r in DROPDOWN_OPTIONS})
    if x_col_name == 'year':
        fig.update_layout(
            xaxis=dict(
                tickmode='linear',
                tick0=2009,
                dtick=4
            )
        )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
