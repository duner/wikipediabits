import urllib
import requests
import tweepy
from bs4 import BeautifulSoup

BASE_URL = 'http://en.wikipedia.org/w/api.php?format=json&action=query&'
EXCEPTIONS = ['list','refer','these','things']

def get_random_page():
	rand_url = BASE_URL + '&list=random&rnnamespace=0'
	rand_response = requests.get(rand_url).json()
	rand_id = rand_response['query']['random'][0]['id']
	get_article(rand_id)

def get_article(id):
	params = {
		'prop': 'extracts',
		'redirects': 'true',
		'exlimit': 'max',
		'pageids': str(id),
	}
	page_url = BASE_URL + urllib.urlencode(params)
	page = requests.get(page_url).json()
	extract = page['query']['pages'][str(id)]['extract']
	text = get_page_text(extract)
	if fits_in_tweet(text):
		content = text.split('\n')[0].strip('\n')
		post_tweet(content)
	else:
		get_random_page()

def get_page_text(extract):
	soup = BeautifulSoup(extract)
	text = soup.get_text()
	return text

def fits_in_tweet(text):
	chars = len(text)
	if chars > 140:
		return False
	else:
		if any(phrase in text for phrase in EXCEPTIONS):
			return False
		else:
			return True

def post_tweet(tweet_content):
	print tweet_content




get_random_page()
