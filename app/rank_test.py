import json

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import dbaction

def get_ranks(players: dict):
    """ Get ranks of players

    Args:
        players (dict): dict of players

    Returns:
        dict: player and df of ranks
    """
    
    # Initialize competitive ranks
    modes = ['Ranked Duel 1v1', 
             'Ranked Doubles 2v2', 
             'Ranked Standard 3v3']
    
    # Configure headless browser with user agent
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    chrome_options = Options()
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=chrome_options)

    player2ranks_df = {}
    for player, info in players.items():
        # Format url
        platform, userid = info['platform'], info['userid']
        url = f'https://api.tracker.gg/api/v2/rocket-league/standard/profile/{platform}/{userid}'
        
        # Get data from driver
        driver.get(url)
        content = driver.find_element(By.CSS_SELECTOR, 'pre')
        data = json.loads(content.text)
        
        # Get all ranks from competitive modes
        ranks = []
        for i in range(10):
            mode = data['data']['segments'][i]['metadata']['name']
            if mode in modes:
                stats = data['data']['segments'][i]['stats']
                
                rank = stats['tier']['metadata']['name']
                icon_url = stats['tier']['metadata']['iconUrl']
                mmr = stats['rating']['value']
                matches = stats['matchesPlayed']['value']
                
                rank_info = [mode, rank, mmr, matches, icon_url]
                ranks.append(rank_info)
                
                # 3s is always last mode
                if mode == 'Ranked Standard 3v3':
                    break
        
        # Format list of lists into df
        df = pd.DataFrame(ranks, columns=['Mode', 'Rank', 'MMR', 'Matches', 'IconUrl'])
        df.set_index('Mode')
        player2ranks_df[player] = df
        
    con = dbaction.create_connection('app/players_rank.db')
    
    for p, d in player2ranks_df.items():
        d.to_sql(p, con, if_exists='replace')
        pd.read_sql(f'SELECT * FROM {p}', con)
        
    return player2ranks_df






