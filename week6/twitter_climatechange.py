import tweepy
from config import Twitter # storage for authentification
from tweepy import Stream
from tweepy.streaming import StreamListener
import json
import logging as log
import pymongo
import re

print(Twitter)

##### SECTION 1: Authentication #######
#######################################
consumer_key = Twitter['consumer_key']
consumer_secret = Twitter['consumer_secret']
access_token = Twitter['access_token']
access_token_secret = Twitter['access_token_secret']

AUTH = tweepy.OAuthHandler(consumer_key, consumer_secret)

# user authentification
AUTH.set_access_token(Twitter['access_token'], Twitter['access_token_secret'])

### SECTION 2: ACCESSING REST API #####
#######################################
# access to REST Api (no streaming)
api = tweepy.API(AUTH, wait_on_rate_limit=True)
user = api.me()
log.critical("connection established with user: " + user.name)


### SECTION 3: SETTING UP MONGO #####
#####################################
client = pymongo.MongoClient("mongodb")
db = client.tweets
collection = db.tweet_data_climate
collection.remove({})

### SECTION 4: DEFINE FUNCTIONS #####
#######################################
tweet_count = 1000

def clean_tweet(text):
    text = re.sub('@[A-Za-z0–9]+', '', text) #Removing @mentions
    text = re.sub('#', '', text) # Removing '#' hash tag
    text = re.sub('RT[\s]+', '', text) # Removing RT
    text = re.sub('https?:\/\/\S+', '', text) # Removing hyperlink
    text = re.sub('[^0-9A-Za-z \t]', ' ', text)
    return text

def collect_tweets_by_hashtag(hashtag):
    cursor = tweepy.Cursor(api.search, q=hashtag, count=tweet_count, lang = "en", tweet_mode="extended")

    for status in cursor.items(tweet_count):
        cleaned_tweet = clean_tweet(status.full_text)
        tweet = {
            'username': status.user.screen_name,
            'text': cleaned_tweet,
            'hashtag': hashtag,
            'date': status.created_at,
            'userlocation': status.user.location,
            'followers': status.user.followers_count
        }       
        if ( collection.count({ 'text': cleaned_tweet }) == 0 ):
            collection.insert_one(tweet)

### SECTION 5: GET THE DATA #####
##################################
twitter_hashtag_list = ['#globalwarming','#climatechange', '#climatechangeisreal', 
                        '#climateaction', '#climatechangehoax', '#climatedeniers', 
                        '#climatechangeisfalse', '#globalwarminghoax', '#climatechangenotreal', 
                        'climate change', 'global warming']

for hashtag in twitter_hashtag_list:
    collect_tweets_by_hashtag(hashtag)


