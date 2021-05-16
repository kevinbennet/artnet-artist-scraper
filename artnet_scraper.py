#######################################################################################################################
####################################################### IMPORTS #######################################################
#######################################################################################################################

import requests
import bs4
import string
from tqdm import tqdm

import pandas as pd
import re
from datetime import datetime

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

# Create Manufacturer column to distinguish from artists (person):
df['Manufacturer'] = df['Info'].apply(lambda x: "established" in x.lower())
df['manufacturer_helper'] = df['Artist'].apply(lambda x: "co." in x.lower() or "&" in x.lower() or "ltd." in x.lower() or \
                                                         "company" in x.lower() or "inc." in x.lower() or "factory" in x.lower() or \
                                                         "+" in x.lower() or "werkstätte" in x.lower() or "society" in x.lower())
df['Manufacturer'] = df[['Manufacturer','manufacturer_helper']].any(axis='columns')

# Drop helper columns and format dtypes:
df.fillna("",inplace=True)

df = df.drop('Info',axis=1)
df = df.drop('info_list',axis=1)
df = df.drop('info_helper_1',axis=1)
df = df.drop('info_helper_2',axis=1)
df = df.drop('info_helper_nationalities',axis=1)
df = df.drop('info_helper_years_1',axis=1)
df = df.drop('info_helper_years_2',axis=1)
df = df.drop('info_helper_years_merged',axis=1)
df = df.drop('manufacturer_helper',axis=1)

df['Born/established'] = pd.to_numeric(df['Born/established'].apply(lambda x: x.replace("?",""))).astype("Int64")
df['Died'] = pd.to_numeric(df['Died'].apply(lambda x: x.replace("?",""))).astype("Int64")

#######################################################################################################################
################################################# INFER ACTIVE YEARS ##################################################
#######################################################################################################################

### MUTUALLY EXCLUSIVE ACTIVE RANGE CONDITIONS:
## Both dates available:
# 1. if both available: start==born and end==died

## If manufacturer false and only one date:
# 2. if born/established available AND it's less than 110 years ago: start==born and end==today+1
# 3. if born/established available AND it's more than 110 years ago: start==born and end==start+110
# 4. if died available only: start==died-110 and end==died

## If manufacturer true and only one date:
# 5. if born/established available only: start==born and end==today+1
# 6. if died available only: start==0 and end==died

## All unavailable:
# 7. neither born/established nor died available: unknown range

condition_one = (df['Born/established'].apply(lambda x: type(x)==int) & df['Died'].apply(lambda x: type(x)==int))
condition_two = (~df['Manufacturer'] & df['Born/established'].apply(lambda x: x>datetime.now().year-110) & df['Died'].apply(lambda x: type(x)!=int))
condition_three = (~df['Manufacturer'] & df['Born/established'].apply(lambda x: x<=datetime.now().year-110) & df['Died'].apply(lambda x: type(x)!=int))
condition_four = (~df['Manufacturer'] & df['Born/established'].apply(lambda x: type(x)!=int) & df['Died'].apply(lambda x: type(x)==int))
condition_five = (df['Manufacturer'] & df['Born/established'].apply(lambda x: type(x)==int) & df['Died'].apply(lambda x: type(x)!=int))
condition_six = (df['Manufacturer'] & df['Born/established'].apply(lambda x: type(x)!=int) & df['Died'].apply(lambda x: type(x)==int))
condition_seven = (df['Born/established'].apply(lambda x: type(x)!=int) & df['Died'].apply(lambda x: type(x)!=int))

df_condition_one = df.loc[condition_one, ["Born/established", "Died"]]
df_condition_one['Active Years'] = [str(i)+" - "+str(j) for i,j in df.loc[condition_one, ["Born/established", "Died"]].values]
df_condition_one['Active Years Range List'] = [list((i,j+1)) for i,j in df.loc[condition_one, ["Born/established", "Died"]].values]

df_condition_two = df.loc[condition_two, ["Born/established", "Died"]]
df_condition_two['Active Years'] = [str(i)+" - present" for i,j in df.loc[condition_two, ["Born/established", "Died"]].values]
df_condition_two['Active Years Range List'] = [list((i,datetime.now().year+1)) for i,j in df.loc[condition_two, ["Born/established", "Died"]].values]

df_condition_three = df.loc[condition_three, ["Born/established", "Died"]]
df_condition_three['Active Years'] = [str(i)+" - "+str(i+110)+" (assumed)" for i,j in df.loc[condition_three, ["Born/established", "Died"]].values]
df_condition_three['Active Years Range List'] = [list((i,i+111)) for i,j in df.loc[condition_three, ["Born/established", "Died"]].values]

df_condition_four = df.loc[condition_four, ["Born/established", "Died"]]
df_condition_four['Active Years'] = [str(j-110)+" (assumed) - "+str(j) for i,j in df.loc[condition_four, ["Born/established", "Died"]].values]
df_condition_four['Active Years Range List'] = [list((j-110,j+1)) for i,j in df.loc[condition_four, ["Born/established", "Died"]].values]

df_condition_five = df.loc[condition_five, ["Born/established", "Died"]]
df_condition_five['Active Years'] = [str(i)+" - present (assumed)" for i,j in df.loc[condition_five, ["Born/established", "Died"]].values]
df_condition_five['Active Years Range List'] = [list((i,datetime.now().year+1)) for i,j in df.loc[condition_five, ["Born/established", "Died"]].values]

df_condition_six = df.loc[condition_six, ["Born/established", "Died"]]
df_condition_six['Active Years'] = [str(0)+" (assumed) - "+str(j) for i,j in df.loc[condition_six, ["Born/established", "Died"]].values]
df_condition_six['Active Years Range List'] = [list((0,j+1)) for i,j in df.loc[condition_six, ["Born/established", "Died"]].values]

df_condition_seven = df.loc[condition_seven, ["Born/established", "Died"]]
df_condition_seven['Active Years'] = ["unknown dates" for i,j in df.loc[condition_seven, ["Born/established", "Died"]].values]
df_condition_seven['Active Years Range List'] = [list((0,datetime.now().year+1)) for i,j in df.loc[condition_seven, ["Born/established", "Died"]].values]

# Combine conditional dataframes and merge with df
df_active_years = df_condition_one[['Active Years','Active Years Range List']].combine_first(df_condition_two[['Active Years','Active Years Range List']])\
.combine_first(df_condition_three[['Active Years','Active Years Range List']]).combine_first(df_condition_four[['Active Years','Active Years Range List']])\
.combine_first(df_condition_five[['Active Years','Active Years Range List']]).combine_first(df_condition_six[['Active Years','Active Years Range List']])\
.combine_first(df_condition_seven[['Active Years','Active Years Range List']])
df = pd.concat([df,df_active_years],axis=1)

#######################################################################################################################
####################################################### EXPORTS #######################################################
#######################################################################################################################

df.to_pickle("artist_list.pkl")
df.to_csv("artist_list.csv")
