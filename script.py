import os
import random
import redis
import requests
import tweepy
import urllib

from bs4 import BeautifulSoup

REQUEST_HEADER = {
    'User-Agent': 'WikipediaBits Twitter Bot',
    'From': os.environ.get('EMAIL_ADDRESS')
}
BASE_URL = 'http://en.wikipedia.org/w/api.php?format=json&action=query&'
EXCEPTIONS = ['list','refer','these','things']
ODDS = 3 if os.environ.get("ON_HEROKU", False) else 1

auth = tweepy.OAuthHandler(
	os.environ.get('TWITTER_CONSUMER_KEY'),
	os.environ.get('TWITTER_CONSUMER_SECRET')
)
auth.set_access_token(
	os.environ.get('TWITTER_ACCESS_TOKEN'),
	os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
)
api = tweepy.API(auth)

r = redis.from_url(os.environ.get("REDIS_URL"))

def get_random_page_id():
	rand_url = BASE_URL + '&list=random&rnnamespace=0'
	rand_response = requests.get(rand_url, headers=REQUEST_HEADER).json()
	rand_id = rand_response['query']['random'][0]['id']
	return rand_id

def get_page_content_if_under_char_limit(id):	
	params = {
		'prop': 'extracts',
		'redirects': 'true',
		'exlimit': 'max',
		'pageids': str(id),
	}
	page_url = BASE_URL + urllib.urlencode(params)
	page_response = requests.get(page_url, headers=REQUEST_HEADER).json()
	page_data = page_response['query']['pages'][str(id)]
	text = get_page_text(page_data['extract'])
	print("Checking: '{}'".format(page_data['title'].encode('utf-8')))
	if fits_in_tweet(text):
		content = text.split('\n')[0].strip('\n')
		return (content.encode('utf8'), page_data)
	else:
		return False, page_data

def get_page_text(extract):
	return BeautifulSoup(extract).get_text()

def fits_in_tweet(text):
	chars = len(text)
	if chars > 140:
		return False
	else:
		if any(phrase in text for phrase in EXCEPTIONS):
			return False
		else:
			return True

def post_tweet(content):
	status = api.update_status(status=content)
	print("TWEETED: " + content)
	return status

def save_to_redis(content, page_data, status):
	data = {
	    'title': page_data['title'].encode('utf-8'),
	    'wikipedia_id': page_data['pageid'],
	    'content': content,
	    'twitter_id': status.id,
	    'time_tweeted': status.created_at.strftime("%Y-%m-%d %H:%M:%S")
	}
	r.hmset(wikipedia_id, data)
	print("SAVED TO REDIS")

def main():
	found_page = False
	while not found_page:
		page_id = get_random_page_id()
		content, page_data = get_page_content_if_under_char_limit(page_id)
		if content:
			found_page = True
			status = post_tweet(content)
			save_to_redis(content, page_data, status)

if __name__ == "__main__":
	if random.choice(range(ODDS)) == 0:
		main()
	else:
		print("SKIPPING")