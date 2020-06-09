# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 20:03:10 2020
"""

import datetime
import os
import time

import matplotlib.pyplot as plt  # data visualization
import pandas as pd  # data frame & csv manipulation
import tweepy  # twitter scraping
from textblob import TextBlob  # sentiment analysis


def create_bar_chart(figure, ct, category, xlab, ylab, title, filePth):
    plt.figure(figure)
    # create bar chart
    plt.bar(range(len(ct)), ct)
    # provide complaint categories for the x-axis ticks
    plt.xticks(range(len(ct)), category, rotation=35)
    # labels x and y axis
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    # title for table
    plt.title(title)
    name = 'figure' + str(figure) + '_' + week_start_date + '.png'
    plt.savefig(os.path.join(filePth, name), dpi=300, format='png', bbox_inches='tight')
    return figure+1


# Authentication keys & tokens
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''

# Set up API with keys and tokens
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# Set up dates for queries
week_start_date = str((datetime.datetime.now() - datetime.timedelta(days=7)).date())
week_end_date = str(datetime.datetime.now().date())

# dict of category and its associated query
queries = {"availability": "(availability OR available OR unavailable)",
           "billing": "(billing OR cost OR bills OR bill OR price OR money)",
           "speed": "(speed OR slow OR slowed OR slower OR lag OR lags OR lagging"
                    " OR sluggish OR quick OR fast OR faster)",
           "equipment": "(equipment OR router OR modem OR tower OR ethernet)",
           "interference": "(interference OR interfere OR interfered)",
           "privacy": "(privacy OR private)"}

# source: https://broadbandnow.com/All-Providers
subscriberCounts = {"AT&T": 429311070, "CenturyLink": 49300155, "Charter": 102726027, "Comcast": 111564376,
                    "Cox": 21154000, "Optimum": 12437931, "Spectrum": 102726027, "Sprint": 279984122,
                    "Verizon": 388940855, "Windstream": 13721234}

# provider names from subscriberCounts
providers = list(subscriberCounts.keys())

# csv columns
cols = ["created_at", "provider", "complaint", "location", "text", "subjectivity", "polarity"]

# path and name for csv
folder_path = ''+week_start_date
csv_name = 'twitter_data_week_'+week_start_date+'.csv'
csv_path = folder_path+"/"+csv_name

# list of lists of tweet info
tweets_matrix = []
# max count per query of 100
count = 100

# Pulling individual location-based tweets from each query
for provider in providers:
    for keyword in queries:
        # create query of provider and keyword
        full_query = provider+" "+queries[keyword]+" since:"+week_start_date+" until:"+week_end_date
        for tweet in api.search(q=full_query, count=count):
            # cast tweet to string & remove \n and \r
            text = str(tweet.text).replace("\n", " ").replace("\r", "")
            # check for text duplicates
            repeat = False
            try:
                for tweets_list in tweets_matrix:
                    if text in tweets_list:
                        repeat = True
                        break
                if not repeat:  # if not a duplicate
                    # get location, if it exists
                    try:
                        location = tweet.place.full_name
                    except AttributeError as e:
                        location = "None"
                    # create subjectivity and polarity rating
                    sentiment = TextBlob(text.lower()).sentiment
                    sub = sentiment.subjectivity
                    pol = sentiment.polarity
                    # add variables tweet matrix, must match cols
                    tweets_matrix.append([tweet.created_at, provider, keyword, location, text, sub, pol])
            except BaseException as e:
                print('failed on_status,', str(e))
                time.sleep(3)

# create a database out of tweet matrix with column names
df = pd.DataFrame(data=tweets_matrix, columns=cols)

# check for existing folder path
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# check for existing csv
if not os.path.isfile(csv_path):
    # create file from data frame
    df.to_csv(csv_path, index=False)
else:
    # add data frame to existing csv without duplicates
    pd.read_csv(csv_path).append(df).drop_duplicates().to_csv(csv_path, index=False)

# CREATE CHARTS

figNum = 0

# bar chart per capita
providerCount = df.provider.value_counts().to_dict()
providerCountPerMil = []
for c in providerCount:
    tweetCount = providerCount.get(c)
    subCount = subscriberCounts[c]
    perMil = tweetCount/subCount * 1000000
    providerCountPerMil.append(perMil)
figNum = create_bar_chart(figNum, providerCountPerMil, providers, "Providers",
                          "Number of Tweets per Million subscribers", "Tweets Per Provider For "
                          + week_start_date + " - " + week_end_date, folder_path)

# bar chart per capita with sentiment analysis

indices_to_drop = []
for i in range(len(df)):
    if df.subjectivity[i] < 0.5 or df.polarity[i] < -0.5:
        indices_to_drop.append(i)
print(len(indices_to_drop))

dropped_df = df.drop(indices_to_drop)
print(len(df), "to", len(dropped_df))  # testing

droppedProviderCount = dropped_df.provider.value_counts().to_dict()
droppedProviderCountPerMil = []
for c in providerCount:
    tweetCount = droppedProviderCount.get(c)
    subCount = subscriberCounts[c]
    perMil = tweetCount/subCount * 1000000
    droppedProviderCountPerMil.append(perMil)
figNum = create_bar_chart(figNum, droppedProviderCountPerMil, providers, "Providers",
                          "Tweets Per Million Subscribers", "Tweets Per Provider For Week of "
                          + week_start_date + " (sentiment filtered)", folder_path)

sentiment_csv_name = 'twitter_data_sentiment_week_'+week_start_date+'.csv'
dropped_csv_name = sentiment_csv_name+"_sentiment"

dropped_df.to_csv(csv_path+sentiment_csv_name, index=False)


# display graphs
# plt.show()
