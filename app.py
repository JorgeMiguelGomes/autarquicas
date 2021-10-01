# -*- coding: utf-8 -*-

# import libraries 

import pandas as pd 
import json 

# Open json files 

	# 2009 

with open('json_files/autarquicas_2009.json') as f2009:
    data_2009 = json.load(f2009)

	# 2013

with open('json_files/autarquicas_2013.json') as f2013:
    data_2013 = json.load(f2013)

	# 2017

with open('json_files/autarquicas_2017.json') as f2017:
    data_2017 = json.load(f2017)

    # 2021

with open('json_files/autarquicas_2021.json') as f2021:
    data_2021 = json.load(f2021)



# Create lists 

	#2009
res_2009 = [{**z, **{'district': x, 'county': y}} for x, y in data_2009.items() for y, z in y.items()]

	# Normalize json on candidates for 2009
df_09 = pd.json_normalize(res_2009, record_path=['candidates'], meta=['total_votes', 'county', 'district'])

	# Expand total_votes dict for 2009 
df_2009 = pd.concat([df_09, pd.json_normalize(df_09['total_votes'])], axis=1)


	#2013
res_2013 = [{**z, **{'district': x, 'county': y}} for x, y in data_2013.items() for y, z in y.items()]

	# Normalize json on candidates for 2013
df_13 = pd.json_normalize(res_2013, record_path=['candidates'], meta=['total_votes', 'county', 'district'])

	# Expand total_votes dict for 2013
df_2013 = pd.concat([df_13, pd.json_normalize(df_13['total_votes'])], axis=1)

	#2017
res_2017 = [{**z, **{'district': x, 'county': y}} for x, y in data_2017.items() for y, z in y.items()]

	# Normalize json on candidates for 2017
df_17 = pd.json_normalize(res_2017, record_path=['candidates'], meta=['total_votes', 'county', 'district'])

	# Expand total_votes dict for 2017
df_2017 = pd.concat([df_17, pd.json_normalize(df_17['total_votes'])], axis=1)

	#2021
res_2021 = [{**z, **{'district': x, 'county': y}} for x, y in data_2021.items() for y, z in y.items()]

	# Normalize json on candidates for 2021
df_21 = pd.json_normalize(res_2021, record_path=['candidates'], meta=['total_votes', 'county', 'district'])

	# Expand total_votes dict for 2021
df_2021 = pd.concat([df_21, pd.json_normalize(df_21['total_votes'])], axis=1)


# Save resulting csv files (raw no data treatment)

df_2009.to_csv('raw_csv/autarquicas_2009_raw.csv')
df_2013.to_csv('raw_csv/autarquicas_2013_raw.csv')
df_2017.to_csv('raw_csv/autarquicas_2017_raw.csv')
df_2021.to_csv('raw_csv/autarquicas_2021_raw.csv')

# data treatment 

print(df_2021.info())



	# Define datasets list 
datasets = [df_2009,df_2013,df_2017,df_2021]


	# Create loop to drop total_values dict columnm, extract candidates name from candidates list, and drop other non relevant columns
for dataset in datasets:
	dataset.drop('total_votes', axis=1, inplace=True)
	dataset['candidatos'] = dataset['effectiveCandidates'].apply(pd.Series)
	dataset.drop('effectiveCandidates', axis=1, inplace=True)
	dataset.drop('votes.acronym', axis=1, inplace=True)


# Create Year Column for each dataframe

df_2009['year']='2009'
df_2013['year']='2013'
df_2017['year']='2017'
df_2021['year']='2021'

# Save treated dataframes to CSV 


df_2009.to_csv('final_csv/autarquicas_2009_treated.csv')
df_2013.to_csv('final_csv/autarquicas_2013_treated.csv')
df_2017.to_csv('final_csv/autarquicas_2017_treated.csv')
df_2021.to_csv('final_csv/autarquicas_2021_treated.csv')


# Last revison on 01OUT2021

