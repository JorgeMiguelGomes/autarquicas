# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import os
import re
import time
import pandas as pd
import json

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

TIMEOUT = None  # data won't change


@cache.memoize(timeout=TIMEOUT)
def dropdown_options():
    with open(os.path.join(BASE_PATH, "dash/dropdown_options.json"), "r") as f:
        jsn = json.load(f)
    return jsn


@cache.memoize(timeout=TIMEOUT)
def dataframe():
    df = pd.read_csv(os.path.join(
        BASE_PATH, "cleaning/autarquicas_treated.csv"
    ), index_col=0)
    for c in df.columns:
        if c == 'parties':
            df[c] = df[c].apply(lambda x: x.replace(
                "'", '"')).apply(json.loads)
        elif set(df[c].unique()) == set(['True', 'False']):
            df[c] = df[c].astype(bool)
    return df


@cache.memoize(timeout=TIMEOUT)
def distrct_dataframe():
    df = dataframe()
    df['population'] = df['numberVoters'] / df['percentageVoters'] * 100
    gped_df = df.groupby(['year', 'district']).sum()[['votesVotes']]
    atts_df = df.drop_duplicates(subset=['year', 'district'])[
        ['year', 'district', 'numberVoters', 'numberParishes', 'blankVotes', 'nullVotes', 'population']]
    del df
    gped_df = gped_df.reset_index()  # makes year, district column reappear
    gped_df = pd.merge(gped_df, atts_df, on=['year', 'district'])
    gped_df['votesPercentage'] = gped_df['votesVotes'] / \
        gped_df['numberVoters'] * 100
    gped_df['blankVotesPercentage'] = gped_df['blankVotes'] / \
        gped_df['numberVoters'] * 100
    gped_df['nullVotesPercentage'] = gped_df['nullVotes'] / \
        gped_df['numberVoters'] * 100
    gped_df['votesValidVotesPercentage'] = gped_df['votesVotes'] / \
        (gped_df['numberVoters'] -
         gped_df['blankVotes'] - gped_df['nullVotes']) * 100
    gped_df['percentageVoters'] = gped_df['numberVoters'] / \
        gped_df['population'] * 100
    return gped_df


@cache.memoize(timeout=TIMEOUT)
def all_parties():
    df = dataframe()
    ps = set([]).union(*list(map(set, df.parties)))
    ps = list(ps)
    ps.sort(key=lambda x: x)
    return ps


@cache.memoize(timeout=TIMEOUT)
def all_districts():
    df = dataframe()
    ps = list(df.district.unique())
    ps.sort(key=lambda x: x)
    return ps


@cache.memoize(timeout=TIMEOUT)
def counties_df():
    df = dataframe()
    df = df.drop_duplicates(subset=['district', 'county'])[
        ['district', 'county']]
    return df


@cache.memoize(timeout=TIMEOUT)
def x_y_color_dropdowns(id_prefix: str = "") -> html.Div:
    return html.Div([
        html.Div([
            html.P("X axis attribute", style={
                   'display': 'inline-block', 'margin': 'auto'}),
            dcc.Dropdown(
                id=id_prefix + "xAxis",
                options=[
                    {"label": r["label"], "value":r["value"]}
                    for r in dropdown_options() if "canX" in r
                ],
                value="year", style={'display': 'inline-block', 'width': '60%', 'margin': 'auto'})],
            style={'width': '33%', 'display': 'inline-block'}
        ),
        html.Div([
            html.P("Y axis attribute", style={
                   'display': 'inline-block', 'margin': 'auto'}),
            dcc.Dropdown(
                id=id_prefix + "yAxis",
                options=[
                    {"label": r["label"], "value":r["value"]}
                    for r in dropdown_options() if "canY" in r or (id_prefix == "county-" and "canCountyY" in r)
                ],
                value="numberVoters", style={'display': 'inline-block', 'width': '60%', 'margin': 'auto'})],
            style={'width': '33%', 'display': 'inline-block'}
        ),
        html.Div([
            html.P("Color/Group attribute",
                   style={'display': 'inline-block', 'margin': 'auto'}),
            dcc.Dropdown(
                id=id_prefix + "colorGroup",
                options=[
                    {"label": r["label"], "value":r["value"]}
                    for r in dropdown_options() if "canColor" in r
                ],
                value="coalition", style={'display': 'inline-block', 'width': '60%', 'margin': 'auto'})],
            style={'width': '33%', 'display': 'inline-block'}
        )
    ])


app.layout = html.Div(children=[
    html.H1(children="Portugal Local Election Results"),

    html.Div(children="""
        Plots of Portugal local election results from 2009 to 2021.
    """),

    html.Div([
        html.H2("Pick-your-own Plot"),
        x_y_color_dropdowns(),
        dcc.Graph(
            id="main-graph",
        )
    ]),

    html.Div([
        html.H2("Plot by Parties/Coalition"),
        html.Div([
            html.Div([
                html.P("Involved Parties/Coalition"),
            ], style={'width': '15%', 'display': 'inline-block'}),
            html.Div([
                dcc.Dropdown(
                    id="parties",
                    options=[
                        {"label": p, "value": p}
                        for p in all_parties()
                    ],
                    value=["PCP-PEV"],
                    multi=True)
            ], style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Checklist(
                    id="coalitionOnly",
                    options=[{"label": "Coalition only?", "value": "Yes"}],
                    value=[]
                )
            ], style={'width': '20%', 'display': 'inline-block'}),
        ]),
        x_y_color_dropdowns("parties-"),
        dcc.Graph(
            id="parties-graph",
        )
    ]),

    html.Div([
        html.H2("Plot by District/County"),
        html.Div([
            html.Div([
                html.P("District"),
            ], style={'width': '15%', 'display': 'inline-block'}),
            html.Div([
                dcc.Dropdown(
                    id="county-district",
                    options=[
                        {"label": d, "value": d}
                        for d in all_districts()
                    ],
                    value="Aveiro")
            ], style={'width': '35%', 'display': 'inline-block'}),
            html.Div([
                html.P("County"),
            ], style={'width': '15%', 'display': 'inline-block'}),
            html.Div([
                dcc.Dropdown(
                    id="county-county",
                    options=[{"label": "(All)", "value": "(All)"}]+[
                        {"label": c, "value": c}
                        for c in counties_df()[counties_df().district == "Aveiro"].county
                    ],
                    value="Águeda")
            ], style={'width': '35%', 'display': 'inline-block'}),
        ]),
        x_y_color_dropdowns("county-"),
        dcc.Graph(
            id="county-graph",
        )
    ])

])


@ app.callback(
    Output("colorGroup", "options"),
    Input("xAxis", "value")
)
def update_color_group(x_col_name):
    new_color_options = [
        {"label": r["label"], "value": r["value"]}
        for r in dropdown_options() if "canColor" in r and r["value"] != x_col_name
    ]
    return new_color_options


def group_df(x_col_name, y_col_name, color_col_name, df=dataframe()):
    temp_df = df.copy(deep=True)
    if color_col_name == "year":
        temp_df["year"] = temp_df["year"].apply(str)
        # hack to make it show as categories instead of colormap
    if "parties" in [x_col_name, color_col_name]:
        temp_df['parties'] = temp_df['parties'].apply(str)
    group_cols = [x_col_name]+([color_col_name] if color_col_name else [])
    gped_df = temp_df.groupby(group_cols).sum()

    gped_df = pd.DataFrame([([t] if type(t) == int else list(t))+[v] for t, v in zip(gped_df.index, gped_df[y_col_name])],
                           columns=group_cols+[y_col_name])
    return gped_df


def gen_bar_graph(gped_df, x_col_name, y_col_name, color_col_name):
    kwargs = dict(x=x_col_name, y=y_col_name, color=color_col_name,
                  labels={r['value']: r['label'] for r in dropdown_options()})
    if color_col_name is None:
        kwargs.pop("color")
    fig = px.bar(gped_df, **kwargs)
    if x_col_name == 'year':
        fig.update_layout(
            xaxis=dict(
                tickmode='linear',
                tick0=min(gped_df.year),
                dtick=4
            )
        )
    else:
        fig.update_xaxes(categoryorder='total descending')
    return fig


@app.callback(
    Output("main-graph", "figure"),
    [Input("xAxis", "value"),
     Input("yAxis", "value"),
     Input("colorGroup", "value")]
)
def update_graph(x_col_name, y_col_name, color_col_name):
    gped_df = group_df(x_col_name, y_col_name, color_col_name)
    fig = gen_bar_graph(gped_df, x_col_name, y_col_name, color_col_name)
    return fig


@app.callback(
    Output("parties-graph", "figure"),
    [Input("parties-xAxis", "value"),
     Input("parties-yAxis", "value"),
     Input("parties-colorGroup", "value"),
     Input("parties", "value"),
     Input("coalitionOnly", "value"), ]
)
def update_parties_graph(x_col_name, y_col_name, color_col_name, parties, coalition_only):
    temp_df = dataframe()
    if len(coalition_only) > 0:
        temp_df = temp_df[[all(p in ps for p in parties)
                           for ps in temp_df.parties]]
        if len(temp_df) == 0:
            fig = px.scatter(
                x=[0], y=[0],
                text=["No coalitions have all these parties:\n" +
                      ",".join(parties)]
            )
            fig.update_traces(textposition="top center")
            return fig
    else:
        temp_df = temp_df[[any(p in ps for p in parties)
                           for ps in temp_df.parties]]
    gped_df = group_df(x_col_name, y_col_name, color_col_name, temp_df)
    fig = gen_bar_graph(gped_df, x_col_name, y_col_name, color_col_name)

    return fig


@ app.callback(
    [Output("county-county", "options"),
     Output("county-county", "value")],
    Input("county-district", "value")
)
def update_county_dropdown(district):
    new_county_options = [{"label": "(All)", "value": "(All)"}] + [
        {"label": c, "value": c}
        for c in counties_df()[counties_df().district == district].county
    ]
    new_county_val = new_county_options[1]['value']
    return new_county_options, new_county_val


# @ app.callback(
#     [Output("county-xAxis", "options"),
#      Output("county-yAxis", "options"),
#      Output("county-yAxis", "options")],
#     Input("county-district", "value")
# )
# def update_x_y_color_dropdown(district):
#     if district == "(All)":

#     return new_county_options, new_county_val


@app.callback(
    Output("county-graph", "figure"),
    [Input("county-xAxis", "value"),
     Input("county-yAxis", "value"),
     Input("county-colorGroup", "value"),
     Input("county-district", "value"),
     Input("county-county", "value"), ]
)
def update_county_graph(x_col_name, y_col_name, color_col_name, district, county):
    if county == "(All)" and not "county" in [x_col_name, color_col_name]:
        temp_df = distrct_dataframe()
        temp_df = temp_df[temp_df.district == district]
        color_col_name = None
    else:
        temp_df = dataframe()
        if county == "(All)":
            temp_df = temp_df[temp_df.district == district]
        else:
            temp_df = temp_df[temp_df.county == county]

    gped_df = group_df(x_col_name, y_col_name, color_col_name, temp_df)
    fig = gen_bar_graph(gped_df, x_col_name, y_col_name, color_col_name)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
