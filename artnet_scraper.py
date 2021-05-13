#######################################################################################################################
####################################################### IMPORTS #######################################################
#######################################################################################################################

import requests
import bs4
import string
from tqdm import tqdm

import pandas as pd
import re

#######################################################################################################################
################################################### SCRAPE URL LIST ###################################################
#######################################################################################################################

alphabet = string.ascii_lowercase
alphabet_list = [letter for letter in alphabet]

headers = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'}
base_url = "http://www.artnet.com{}"

artnet_page_list = []

for letter in alphabet_list:
    res = requests.get(base_url.format(f'/artists/artists-starting-with-{letter}'),headers=headers)
    soup = bs4.BeautifulSoup(res.text,'lxml')

    for link in soup.select('.alphabet-abbrs li a'):
        artnet_page_list.append(link.attrs['href'])

artist_list = []
info_list = []
for url in tqdm(artnet_page_list, desc='Scraping Progress: '):
    res_item = requests.get(base_url.format(url), headers=headers)
    soup_item = bs4.BeautifulSoup(res_item.text,'lxml')

    for item in soup_item.select('.alphabet-result li'):

        artist_list.append(item.text)

        if item.select('.info'):
            info_list.append(item.select('.info')[0].text)
        else:
            info_list.append("")

#######################################################################################################################
############################################### CREATE PANDAS DATAFRAME ###############################################
#######################################################################################################################

df = pd.DataFrame([artist_list,info_list],index=['Artist','Info']).transpose()
df['Artist'] = df['Artist'].apply(lambda x: x.replace('\xa0',' ').strip())
df['Artist'] = df.apply(lambda row : row['Artist'].replace(str(row['Info']), ''), axis=1)
df['Info'] = df['Info'].apply(lambda x: x.lstrip('(').rstrip(')'))
df['info_list'] = df['Info'].apply(lambda x: x.split(', '))
df = pd.concat([df, pd.DataFrame(df.info_list.tolist(),columns=['info_helper_1','info_helper_2'])], axis=1)
df.fillna("",inplace=True)
df['info_helper_nationalities'] = df['info_helper_1'].apply(lambda x: re.findall("^[A-Z][a-z]+\s?[A-Z]?[a-z]*\s?[A-Z]?[a-z]*\s?\/?\s?[A-Z]?[a-z]*\s?[A-Z]?[a-z]*\s?[A-Z]?[a-z]*",x))
def list_to_str(item):
    if item:
        return item[0]
    else:
        return ''
df['Country'] = df['info_helper_nationalities'].apply(list_to_str)
df['info_helper_years_1'] = df['info_helper_1'].apply(lambda x: re.findall("\?(?=[-–])|\d{4}|(?<=[-–])\?",x))
df['info_helper_years_2'] = df['info_helper_2'].apply(lambda x: re.findall("\?(?=[-–])|\d{4}|(?<=[-–])\?",x))
df['info_helper_years_2'] = df['info_helper_years_2'].apply(lambda x: pd.NA if len(x)==0 else x)
df['info_helper_years_merged'] = df['info_helper_years_2'].combine_first(df['info_helper_years_1'])
df = pd.concat([df, pd.DataFrame(df.info_helper_years_merged.tolist(),columns=['Born/established','Died'])], axis=1)
df.fillna("",inplace=True)
df = df.drop('Info',axis=1)
df = df.drop('info_list',axis=1)
df = df.drop('info_helper_1',axis=1)
df = df.drop('info_helper_2',axis=1)
df = df.drop('info_helper_nationalities',axis=1)
df = df.drop('info_helper_years_1',axis=1)
df = df.drop('info_helper_years_2',axis=1)
df = df.drop('info_helper_years_merged',axis=1)
df['Born/established'] = pd.to_numeric(df['Born/established'].apply(lambda x: x.replace("?",""))).astype("Int64")
df['Died'] = pd.to_numeric(df['Died'].apply(lambda x: x.replace("?",""))).astype("Int64")

#######################################################################################################################
####################################################### EXPORTS #######################################################
#######################################################################################################################

df.to_pickle("artist_list.pkl")
df.to_csv("artist_list.csv")
