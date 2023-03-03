import requests
from bs4 import BeautifulSoup
import pandas as pd

from dbaction import *

url = "https://ballchasing.com/replay/ce6fc1e4-03d0-435e-8cfd-b1e83c0b55aa?g=njit-vs-msu-be4lb5jp17#overview"
# url_test_2 = "https://ballchasing.com/replay/303fe9ef-becf-46f0-96b2-a7f3550b3ecf?g=mst-vs-sly-ovb6czhnzc"

page = requests.get(url)

soup = BeautifulSoup(page.content, "html.parser")

results = soup.find(id='details-overview')

trs = results.find_all('tr')

column_headers = ['Player', 'Score', 'Goals', 'Assists', 'Saves', 'Shots']

rows = []
for tr in trs:
    name = tr.find('a')
    if name is not None:
        row = []
        name_f = str(name.text.strip().strip('PRO').strip())
        row.append(name_f)
        tds = tr.find_all('td')
        for td in tds:
            if td.text.isnumeric() is True:
                row.append(td.text)
        rows.append(row)

njit_names = ['Chi', 'apena', 'Tactician']
njit = rows[:3] if rows[0][0] in njit_names else rows[3:] 

print(njit)

df = pd.DataFrame(njit, columns=column_headers)

print(df)



