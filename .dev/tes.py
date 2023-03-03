import json
from datetime import datetime

import dash
from dash import html, dcc, Input, Output, no_update
import dash_bootstrap_components as dbc
import dash_loading_spinners as dls
import pandas as pd

from rank_test import get_ranks
import dbaction as dba

app = dash.Dash()

players_dict = json.load(open('app/players.json'))

ranks_page = []

app.layout = html.Div([
    
    dcc.Store(id='refresh-timestamp-store',
              storage_type='local'),
    
    html.Div([
        html.Div(id='location'),
        
        # Navbar
        html.Div(
            dcc.RadioItems([
                {"label": html.Div("TEAMS", id='teams', className='nav-button'),
                    "value": "teams"},
                {"label": html.Div("MATCHES", id='matches', className='nav-button'),
                    "value": "matches"},
                {"label": html.Div("STATS", id='stats', className='nav-button'),
                    "value": "stats"},
                {"label": html.Div("RANKS", id='ranks', className='nav-button'),
                    "value": "ranks"}
            ], value='ranks',
               id='page-selector',
               inline=True,
            ), 
            className='navbar'
        ),
        
        html.Div([
        # Div to select team
            html.Div([
                dcc.RadioItems([
                    {'label': html.Span('DIVISION 1', 
                                        className='team-button',
                                        **{'data-teamtype':'1'}), 
                     'value': '1'},
                    {'label': html.Span('DIVISION 2', 
                                        className='team-button',
                                        **{'data-teamtype':'2'}), 
                     'value': '2'},
                    {'label': html.Span('ACTIVE', 
                                        className='team-button',
                                        **{'data-teamtype':'Active'}), 
                     'value': 'active'},
                    {'label': html.Span('All NJIT', 
                                        className='team-button',
                                        **{'data-teamtype':'NJIT'}), 
                     'value': 'other'},
                ], 
                   id='team-selector',
                   value='1',
                   labelClassName='team-button-label',
                   inline=True,
                   persistence=True,
                   persistence_type='session'
                ),
            ], 
                className='team-selector-container'
            ),
            
            html.Div(html.Span('Loading...'), id='team-title'),
            
            html.Div([
                html.Span('NAME', id='name-filter', className='name'),
                html.Span('3v3', id='3v3-filter', className='rank-item'),
                html.Span('2v2', id='2v2-filter', className='rank-item'),
                html.Span('1v1', id='1v1-filter', className='rank-item'),
            ], 
                className='row header',
                id='header'
            ),
            
            html.Div(id='table'),
            
            html.Div([
                html.Span('Last Updated:', id='refresh-timestamp'),
                html.Button(
                    dbc.Spinner(html.Div('Refresh', id='refresh-text'),
                                delay_show=250, 
                                spinner_style={"width": "1rem", 
                                            "height": "1rem",
                                            'border-width':'0.2em'}),
                    id='refresh'
                )
            ],
                className='rank-details'
            )
        ],
            className='rank-container'
        )
    ],
        id='page', 
        className='center light'
    ),
],
    className='content'                          
)

rank_columns = ('name', '3v3', '2v2', '1v1')
@app.callback(
    Output('team-title', 'children'),
    Output('team-title', 'style'),
    Output('header', 'style'),
    Output('table', 'children'),
    Output('refresh-text', 'children'),
    [Output(f'{mode}-filter', 'style') for mode in rank_columns],
    Output('refresh-timestamp', 'children'),
    Output('refresh-timestamp-store', 'data'),
    Input('team-selector', 'value'),
    Input('refresh-timestamp-store', 'data'),
    Input('refresh', 'n_clicks'),
    [Input('{}-filter'.format(mode), 'n_clicks') for mode in rank_columns]
)
def select_team(value, timestamp, *args):
    # Get id of clicked value
    clicked_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    clicked_id_f = clicked_id.split('.')[0].split('-')[0]
    
    print(f'clicked id: -{clicked_id_f}-')
    print(f'clicked id type: -{type(clicked_id_f)}-')
    print(f'value: -{value}-')

    # Preset values
    rank2index = {'1v1': 0, 
                  '2v2': 1, 
                  '3v3': 2}
    
    value2name = {'1': 'Division 1', 
                  '2': 'Division 2',
                  'active': 'active', 
                  'other': 'NJIT'}
    
    value2style = {'1': {'background-color': '#426985'}, 
                   '2': {'background-color': '#d34467'},
                   'active': {'color': '#FFFFFF'},
                   'other': {'background-color': '#ed3636'}}
    
    position2pic = {1: 'assets/resources/gold.png',
                    2: 'assets/resources/silver.png',
                    3: 'assets/resources/bronze.png'}
    
    filters = {'name': {},
               '3v3': {},
               '2v2': {},
               '1v1': {}}
    
    tables = []
    
    
                    
    
    # TODO: Fix
    # Get player dicts
    if clicked_id_f in ['refresh', '']:
        # Get all players
        all_players_ranks_dict = get_ranks(players_dict)
        players_ranks_dict = {}
        for k, v in players_dict.items():
            if value != 'other':
                if value == 'active':
                    if v['division'] in ['1', '2']:
                        players_ranks_dict[k] = all_players_ranks_dict[k]
                else:
                    if v['division'] == value:
                        players_ranks_dict[k] = all_players_ranks_dict[k]
            else:
                players_ranks_dict[k] = all_players_ranks_dict[k]   
    else:
        # Get names in selected team
        con = dba.create_connection('app/players_rank.db')
        players_ranks_dict = {}
        for k, v in players_dict.items():
            if value != 'other':
                if value == 'active':
                    if v['division'] in ['1', '2']:
                        players_ranks_dict[k] = pd.read_sql(f'SELECT * FROM {k}', con)
                else:
                    if v['division'] == value:
                        players_ranks_dict[k] = pd.read_sql(f'SELECT * FROM {k}', con)
            else:
                players_ranks_dict[k] = pd.read_sql(f'SELECT * FROM {k}', con)
    
    # Sort names by selected choice (name by default)
    if clicked_id_f in ['1v1', '2v2', '3v3']:
        player2rank = {}
        for player, df in players_ranks_dict.items():
            player2rank[player] = df.loc[rank2index[clicked_id_f]]['MMR']
        player2rank_sorted = sorted(player2rank.items(), key=lambda x:x[1], reverse=True)
        sortednames = dict(player2rank_sorted).keys()
        filters[clicked_id_f] = {'color': 'white', 
                                 'font-weight': 'bold',
                                 'border-bottom': '2px solid white'}
    else:
        sortednames=sorted(players_ranks_dict.keys(), key=lambda x:x.lower())
        filters['name'] = {'color': 'white', 
                           'font-weight': 'bold'}
    
    # Add ranks of names to table
    count = 1    
    for player in sortednames:
        player_rows = []
        for i, row in players_ranks_dict[player].iterrows():
            # Set style if selected
            selected_style = ''
            if clicked_id_f in ['1v1', '2v2', '3v3']:
                selected_style = 'selected' if str(i+1) in clicked_id_f else ''
            
            # Insert rank item into row
            player_rows.insert(0,
                html.Span([
                    html.Img(src=row['IconUrl'],
                             title=row['Rank']),
                    html.Span(row['MMR'], 
                              className='mmr',
                              title='{} Games'.format(row['Matches']))
                ], 
                    className='rank-item',
                    **{'data-theme': f'{selected_style}'}
                )
            )
        
        # Assign medals if needed
        if clicked_id_f in ['1v1', '2v2', '3v3']:
            if count <= 3:
                player_span = html.Span(html.Img(src=position2pic[count],
                                                className='position-top'), 
                                        className='position')
            else: 
                player_span = html.Span(count, className='position')
        else:
            player_span = html.Span(count, className='position')
        
        # Get TRN link of player
        platform = players_dict[player]['platform']
        userid = players_dict[player]['userid']
        trn_link = f'https://rocketleague.tracker.network/rocket-league/profile/{platform}/{userid}/'
        
        # Link player name to TRN, insert into row
        player_rows.insert(0,
            html.Span([
                player_span,
                html.A(player,
                       href=trn_link,
                       title='TRN Page',
                       target="_blank")
                ], className='name')
        )
        
        # Add row to table
        tables.append(html.Div(player_rows, className='row'))
        
        # Increment position
        count += 1
    
    # TODO: FIX
    f_timestamp = 'None'
    now = datetime.now()
    dt_string = now.strftime("%b %d %Y | %I:%M %p")
    
    if timestamp != '':
        f_timestamp = f'Last updated: {dt_string}'
        
    if value == 'other':
        team_title = html.Span([
            html.Img(src='assets/resources/highlander-logo.png',
                     className='highlander'),
            value2name[value].upper()
        ])
    else:
        team_title = html.Span(value2name[value].upper())

    
    return team_title, value2style[value], value2style[value], tables, html.Div('Refresh', id='refresh1'), filters['name'], filters['3v3'], filters['2v2'], filters['1v1'], f_timestamp, dt_string

@app.callback(
    Output('page', 'children'),
    [Output('{}'.format(page), 'style') for page in ['teams', 'matches', 'stats', 'ranks']],
    Input('page-selector', 'value'),
    prevent_initial_update = True
)
def select_page(page):
    filters = {'teams': {},
               'matches': {},
               'stats': {},
               'ranks': {}}
    
    filters[page] = {'color': 'white'}
    
    # TODO: Pages
    # match page:
    #     case 'teams':
    #     case 'matches':
    #     case 'stats':
    #     case 'ranks':
    
    return no_update, filters['teams'], filters['matches'], filters['stats'], filters['ranks']

if __name__ == '__main__':
    app.run_server(debug=True)