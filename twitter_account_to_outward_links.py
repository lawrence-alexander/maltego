#================================================================================================#
#         Maltego Transform to return a Twitter account's top outward links for all tweets       #
#              by Lawrence Alexander 2017 @LawrenceA_UK la2894@my.open.ac.uk                     #
#================================================================================================#

import requests, json, time
from requests_oauthlib import OAuth1
from MaltegoTransform import MaltegoTransform
from MaltegoTransform import MaltegoEntity
import sys
import re
import pickle

# Tokens and keys

client_key = ''
client_secret =''
token = ''
token_secret =''

# Base for Twitter calls

base_twitter_url = "https://api.twitter.com/1.1/"

# Auth setup

oauth = OAuth1(client_key,client_secret,token,token_secret)

tform = MaltegoTransform()

# Pass in account to query
target_account = sys.argv[1]

#
# Download tweets from user
#
def download_tweets(screen_name,number_of_tweets,max_id=None):
    
    api_url = "%s/statuses/user_timeline.json?" % base_twitter_url
    api_url += "screen_name=%s&" % screen_name
    api_url += "count=%d" % number_of_tweets
    
    if max_id is not None:
        api_url += "&max_id=%d" % max_id
        
    # Make request  
    
    response = requests.get(api_url,auth=oauth)
    
    if response.status_code == 200:
        tweets = json.loads (response.content)
        return tweets
    else:
        tform.addException("Problem connecting to API - returned error code %d" % response.status_code)
        tform.throwExceptions()


#
# Download tweets for passed username
#

def download_all_tweets(username):
    full_tweet_list = []
    max_id = 0
    
    # Get first 200 tweets
    
    tweet_list = download_tweets(username, 200)
    
    # Get oldest tweet
    
    oldest_tweet = tweet_list[::-1][0]
    
    # Continue getting tweets
    while max_id != oldest_tweet['id']:
        
        # Add each batch to full list
        full_tweet_list.extend(tweet_list) 
        
        # set max_id to latest max_id retrieved
        max_id=oldest_tweet['id']        
               
        # Sleep for rate limiting
        time.sleep(3)
        
        # Send next request with max_id set
        tweet_list = download_tweets(username,200,max_id-1)
        
        # Get the oldest tweet
        if len(tweet_list):
            oldest_tweet = tweet_list[-1]
    # Add few last tweets
    full_tweet_list.extend(tweet_list)
    
    # Return full list
    return full_tweet_list

# Check for cached tweets file to avoid issuing superfluous API requests
full_tweet_list =[]
try:
    full_tweet_list = pickle.load(open("%s-tweets.pkl" % target_account))
except:    
    pass

# If we don't have cached results, hit the Twitter API and download all tweets
if not full_tweet_list:    
    full_tweet_list = download_all_tweets(target_account)
    # Cache results to a local pickle file
    fd = open("%s-tweets.pkl" % target_account, "wb")
    pickle.dump(full_tweet_list, fd)
    fd.close()    

# Build list of client links for all tweets
links= []
tweet_url=[]
domain_list = []
domain =''
for tweet in full_tweet_list:   
    profile_url = tweet ['user']['url']
    # If there's a profile link, add that as entity
    if profile_url:
        tform.addEntity("maltego.Website", profile_url)
    # Get URL and separate domain entities from tweets    
    try:    
        tweet_url = tweet['entities'] ['urls'] [0]['expanded_url']
        domain = re.search('[://][a-z0-9-_~.]+',tweet_url)
    except:
        pass
    
    if domain:
        try:
            domain = domain.group().replace(":","").replace("/","").replace("www.","")
            domain_list.append(domain)
        except:
            pass
    if tweet_url:
        links.append(tweet_url) 
        
# Calculate link percentages and return top links tweeted
def get_top_entities(entity_type,links):
    count = 0
    link_percentages = {}
    for the_link in links:
        for countapp in links:
            if countapp == the_link:
                count += 1 
        if count >= 1:                
            link_percentages[the_link] = 100.0 * count / len (links)                                   
        count =0
    for link, percentage in link_percentages.iteritems():
        # Set minimum percentage of link usage to return
        if percentage >= 2:
            tform.addEntity(entity_type, link)

get_top_entities(entity_type="maltego.url", links=links)
get_top_entities(entity_type="maltego.Domain", links=domain_list)

# Return XML data for Maltego to process
tform.returnOutput()    
