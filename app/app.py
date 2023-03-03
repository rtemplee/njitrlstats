import base64
import json
from datetime import datetime
import time

import dash
from dash import html, dcc, Input, Output, no_update
import dash_bootstrap_components as dbc
import pandas as pd

from rank_test import get_ranks
import dbaction as dba

def format_img(img):
    b64encoded_img=base64.b64encode(open(f'{img}', 'rb').read())
    return f'data:image/png;base64,{b64encoded_img.decode()}'

app = dash.Dash(__name__)

players_dict = json.load(open('app/players.json'))

ranks_page = [
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
                                    **{'data-teamtype':'Default'}), 
                'value': 'active'},
                {'label': html.Span('INACTIVE', 
                                    className='team-button',
                                    **{'data-teamtype':'Default'}), 
                'value': 'inactive'},
                {'label': html.Span('All NJIT', 
                                    className='team-button',
                                    **{'data-teamtype':'NJIT'}), 
                'value': 'all'}
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
]

app.layout = html.Div([
    # Ranks store
    dcc.Store(
        id='refresh-timestamp-store',
        storage_type='local'
    ),
    
    html.Div(
        ranks_page,
        id='page', 
        className='center light'
    )
],
    className='content'                          
)

rank_columns = ('name', '3v3', '2v2', '1v1')
rank2index = {mode: i for i, mode in enumerate(('1v1', '2v2', '3v3'))}
position2png = {i: f'assets/resources/{medal}.png' for i, medal in enumerate(('gold', 'silver', 'bronze'), 1)}
@dash.callback(
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
    [Input('{}-filter'.format(mode), 'n_clicks') for mode in rank_columns],
    running=[
        (Output("refresh", "style"), {'cursor': 'default'}, {}),
    ]
)
def select_team(value, timestamp, *args):
    t0 = time.time()
    # Get id of clicked value
    clicked_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    clicked_id_f = clicked_id.split('.')[0].split('-')[0]
    
    print(f'clicked id: -{clicked_id}-')
    print(f'clicked id f: -{clicked_id_f}-')
    print(f'clicked id type: -{type(clicked_id_f)}-')
    print(f'value: -{value}-')
    
    # Preset values
    value2title = {'1': 'Division 1', 
                   '2': 'Division 2',
                   'active': 'Active',
                   'inactive': 'Inactive', 
                   'all': 'NJIT'}
    
    value2style = {'1': {'background-color': '#426985'}, 
                   '2': {'background-color': '#d34467'},
                   'active': {'color': '#FFFFFF'},
                   'inactive': {'color': '#FFFFFF'},
                   'all': {'background-color': '#ed3636'}}
    
    filters = {column: {} for column in rank_columns}
    
    current_timestamp = f'Last updated: {timestamp}'
    
    if value == 'all':
        team_title = html.Span([
            html.Img(src=('assets/resources/highlander-logo.png'),
                     className='highlander'),
            value2title[value].upper()
        ])
    else:
        team_title = html.Span(value2title[value].upper())
    
    # If refresh or initial load, get ranks and initialize db
    if clicked_id_f in ['refresh', '']: 
        try:
            get_ranks(players_dict)
            
            now = datetime.now()
            dt_string = now.strftime("%b %d %Y • %I:%M %p")
            current_timestamp = f'Last updated: {dt_string}'
            timestamp = dt_string
            
        except Exception:
            # If there's an error getting the names
            pass
    
    # Get player dicts
    con = dba.create_connection('app/players_rank.db')
    player2ranks = {}
    for player, info in players_dict.items():
        try:
            if value == 'all': pass
            elif value == 'active':
                if info['division'] not in ('1', '2'):
                    continue
            elif value == 'inactive':
                if info['division'] in ('1', '2'):
                    continue
            else:
                if info['division'] != value:
                    continue
                    
            player2ranks[player] = pd.read_sql(f'SELECT * FROM {player}', con)
            
        except Exception:
            # If name in table is not found
            pass
    
    # Sort names (Alphabetical by default)
    if clicked_id_f in ['1v1', '2v2', '3v3']:
        player2rank = {}
        for player, df in player2ranks.items():
            player2rank[player] = df.loc[rank2index[clicked_id_f]]['MMR']
        player2rank_sorted = sorted(player2rank.items(), 
                                    key=lambda x:x[1],
                                    reverse=True)
        sortednames = dict(player2rank_sorted).keys()
        
        filters[clicked_id_f] = {'border-bottom': '2px solid white',
                                    'font-weight': 'bold',
                                    'color': 'white',
                                    'cursor': 'default'}
    else:
        sortednames = sorted(player2ranks.keys(), 
                                key=lambda x:x.lower())
        
        filters['name'] = {'color': 'white', 
                            'font-weight': 'bold',
                            'cursor': 'default'}
        
    # Add ranks of names to table
    players_table = []
    for position, player in enumerate(sortednames, 1):
        player_row = []
        
        # Iterate through ranks in each game mode
        for i, mode_row in player2ranks[player].iterrows():
            # Set style if selected
            selected_style = ''
            if clicked_id_f in ['1v1', '2v2', '3v3']:
                selected_style = 'selected' if str(i + 1) in clicked_id_f else ''
            
            
            mmr_span = html.Span(mode_row['MMR'], 
                                 className='mmr',
                                 title='{} Games'.format(mode_row['Matches']))
            
            # If unranked
            if mode_row['Matches'] < 10:
                mmr_span.style = {'color': '#727272'}
            
            # Insert rank item into row
            player_row.insert(0,
                html.Span([
                    html.Img(src=mode_row['IconUrl'],
                             title=mode_row['Rank']),
                    mmr_span
                ], 
                    className='rank-item',
                    **{'data-theme': f'{selected_style}'}
                )
            )
        
        # Add position or medal
        position_span = html.Span(position, className='position')
        if clicked_id_f in ('1v1', '2v2', '3v3'):
            if position <= 3:
                position_span = html.Span(html.Img(src=position2png[position],
                                                className='position-top'), 
                                        className='position')
        
        # Get TRN link of player
        platform = players_dict[player]['platform']
        userid = players_dict[player]['userid']
        trn_link = f'https://rocketleague.tracker.network/rocket-league/profile/{platform}/{userid}/'
        
        pp = html.Span([
                position_span,
                html.A(player,
                       href=trn_link,
                       target='_blank',
                       title='TRN Page')
            ], 
                className='name'
            )
        # Link player name to TRN, insert into row
        player_row.insert(0,
            pp
        )
        
        # Add row to table
        players_table.append(
            html.Div(player_row, 
                     className='row')
        )
        
    t1 = time.time()
    
    timer = t1 - t0
    print(timer)
    
    return team_title, value2style[value], value2style[value], players_table, html.Div('Refresh', id='refresh1'), filters['name'], filters['3v3'], filters['2v2'], filters['1v1'], current_timestamp, timestamp

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
    app.run_server(debug=True,
                   host='0.0.0.0')