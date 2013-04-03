import os
import sys
import time
import logging
from subprocess import Popen

rootDir = os.path.dirname(os.path.realpath(__file__))
if rootDir[-1] == ';':rootDir = rootDir[0:-1]
libGrooveDir = os.path.join(rootDir, 'groove-dl')
sys.path.append(libGrooveDir)

import tweepy
import groove

# Your App (Tabby Dances) 
consumer_key=<YOUR_CONSUMER_KEY_HERE>
consumer_secret=<YOUR_CONSUMER_SECRET_HERE>

# User (@wktabby)
access_token_key = <YOUR_ACCESS_TOKEN_KEY_HERE>
access_token_secret = <YOUR_ACCESS_TOKEN_SECRET_HERE>

# file paths (change them accordingly)
db = '/home/pi/tabby-dances/lastmentionid.txt'
log = '/home/pi/tabby-dances/tabby.log'
mpg123_path = '/usr/bin/mpg123'

def printUnicode(str):
	'''
	Print debug information, by default python 2 is ascii encoded in xbmc 
	'''
	print str.encode('utf-8')


class TabbyPlayer:
	def __init__(self):
		self.proc = None
		self.tag = None
		self.mention_from = None
		self.in_reply_to_status_id = None
		self.artist = ''
		self.title = ''
		self.last_mention_id = None
		self.readLastMentionId()
	
	def readLastMentionId(self):
		'''
		Read last mention id from database file, will create one if the file does not exist
		'''
		# create db file if not exist
		if not os.path.exists(db):
			f = open(db, 'w+')
			self.last_mention_id = 1
			f.close()
			return

		# read from db file
		f = open(db, 'r')
		s = f.readline()
		self.last_mention_id = int(s)
		f.close()

	def writeLastMentionId(self, last_mention_id):
		'''
		Write last mention id to database file
		'''
		self.last_mention_id = last_mention_id
		f = open(db, 'w+')
		f.write('%d\n' % last_mention_id)
		f.close()

	def tweetCurrentSong(self):
		'''
		Post tweet of current playing song 
		'''
		tweet = None
		try:
			#if self.in_reply_to_status_id and self.mention_from:
			# streaming from grooveshark (in response to twitter)
			tweet = '@' + self.mention_from + ' I am dancing to ' + self.title + ' by ' + self.artist + ' right meow! '
			api.update_status(tweet, self.in_reply_to_status_id)
		except Exception, e:
			logger.error(str(e))
			return
		logger.info(tweet)

	def play(self, songUrl):
		'''
		Play song with mpg123 asynchronously
		'''
		procLog = open(os.path.expanduser(log), 'w')
		self.proc = Popen([mpg123_path, songUrl], stderr = procLog, stdout = procLog)
		logger.info('Playing...' + songUrl)

	def isPlaying(self):
		'''
		Return True when there is music playing
		'''
		# process not started yet
		if self.proc is None:
			return False
		
		retcode = self.proc.poll()

		# process not finished, meaning music is playing
		if retcode is None:
			return True
		
		# return code received, meaning music is finished playing
		return False

	def parseTweet(self, tweet):
		'''
		Parse tweet and send query to GrooveShark
		'''
		if not tweet:
			return
		
		# split that tweet into list
		cmd = tweet.text.lower().split()
		
		# pass tweet and only match the following command(s)
		# play song: '@wktabby play <song/musician name>'
		if cmd[1] == 'play':
			query = ' '.join(cmd[2:])
			printUnicode(query)
			self.mention_from = tweet.user.screen_name
			self.in_reply_to_status_id = tweet.id
			self.grooveStream(query)
		
		# save the tweet id so that next time search from new tweet since here 
		self.writeLastMentionId(tweet.id)

	def grooveStream(self, query):
		'''
		Retrive URL, artist, title with query from GrooveShark
		'''
		songUrl, self.artist, self.title = groove.retrieveSongUrl(query)
		if songUrl:
			self.play(songUrl)
			self.tweetCurrentSong()
		else:
			tweet = '@' + self.mention_from + ' Sorry I didn\'t find ' + '"' + query + '"'
			try:
				api.update_status(tweet, self.in_reply_to_status_id)
			except Exception, e:
				logger.error(str(e))
				return
			logger.info(tweet)

	def searchLatestAtMention(self):
		'''
		Search the latest @mention tweets
		'''
		# reset tweet info
		self.mention_from = None
		self.in_reply_to_status_id = None
		
		# only check @mentions when player is idle
		if self.isPlaying():
			logger.info('Song is playing...')
			return None
		
		# get all @mention tweets from last mention
		try:
			tweets = api.mentions_timeline(since_id = self.last_mention_id)
			logger.info('last_mention_id = %d' % self.last_mention_id)
		except Exception, e:
			logger.exception(str(e))
			return
		
		# process tweets if there are any
		if len(tweets) > 0:
			
			# print all @mention tweets from last mention
			for t in tweets:
				logger.info(str(t.id) + ' :: ' + t.user.screen_name + ' :: ' + t.text)
			
			# find the latest tweet if there are more than one
			tweet = tweets[0]
			return tweet
		
		# no new tweets from last mention
		return None


if __name__ == '__main__':
	
	### 0. Logger setup
	logger = logging.getLogger('TabbyDances')
	logger.setLevel(logging.DEBUG)
	# create file handler which logs even debug messages
	fh = logging.FileHandler(log)
	fh.setLevel(logging.DEBUG)
	# create console handler with a higher log level
	ch = logging.StreamHandler()
	ch.setLevel(logging.ERROR)
	# create formatter and add it to the handlers
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)
	fh.setFormatter(formatter)
	# add the handlers to logger
	logger.addHandler(ch)
	logger.addHandler(fh)


	### 1. Authenticate with Twitter ###
	
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token_key, access_token_secret)
	api = tweepy.API(auth)
	logger.info('Ready to post to ' + api.me().name)

	### 2. While loop to search and process twitter @mention ###
	
	player = TabbyPlayer()
	
	while 1:
		
		# find latest tweet
		tweet = player.searchLatestAtMention()
		
		# process the tweet
		player.parseTweet(tweet)
		
		# rate limit is 350 per hour, thats every 11 second (3600s / 350 = 11s)
		# we use 15s just for safe
		time.sleep(15)
		
