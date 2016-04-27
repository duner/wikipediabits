import os
import urllib
import requests
import tweepy
from bs4 import BeautifulSoup

REQUEST_HEADER = {
    'User-Agent': 'WikipediaBits Twitter Bot',
    'From': os.environ.get('EMAIL_ADDRESS')
}

BASE_URL = 'http://en.wikipedia.org/w/api.php?format=json&action=query&'
EXCEPTIONS = ['list','refer','these','things']

auth = tweepy.OAuthHandler(
	os.environ.get('TWITTER_CONSUMER_KEY'),
	os.environ.get('TWITTER_CONSUMER_SECRET')
)
auth.set_access_token(
	os.environ.get('TWITTER_ACCESS_TOKEN'),
	os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
)
api = tweepy.API(auth)


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
	page = requests.get(page_url, headers=REQUEST_HEADER).json()
	extract = page['query']['pages'][str(id)]['extract']
	text = get_page_text(extract)
	if fits_in_tweet(text):
		content = text.split('\n')[0].strip('\n')
		return content.encode('utf8')
	else:
		return False

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
	api.update_status(status=content)
	print("TWEETED: " + content)

def main():
	found_page = False
	while not found_page:
		page_id = get_random_page_id()
		content = get_page_content_if_under_char_limit(page_id)
		if content:
			found_page = True
			post_tweet(content)

if __name__ == "__main__":
	main()