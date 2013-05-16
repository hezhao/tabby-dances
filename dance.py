import os
import sys
import time
import random
from subprocess import Popen
import tweepy
from config import TWITTER_SETTINGS, APP_SETTINGS
import groove_dl.groove as groove


mpg123_path = APP_SETTINGS['mpg123_path']

class TabbyPlayer():
    def __init__(self):
        self.api = None
        self.proc = None
        self.tag = None
        self.mention_from = None
        self.in_reply_to_status_id = None
        self.artist = None
        self.title = None

    def tabbyLogger(self, msg, level='INFO'):
        '''
        Python logging module sucks, I only print simple messages
        with timestamp in console
        '''
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print '[%s %s] %s' % (level, timestamp, msg)

    def tweetCurrentSong(self):
        '''
        Post tweet of current playing song 
        '''
        tweet = None
        try:
            verbs =['dancing','jamming', 'shaking']
            tweet = '@' + self.mention_from + ' I am ' + verbs[random.randint(0,2)] + ' to ' + self.title + ' by ' + self.artist + ' right meow!'
            self.api.update_status(tweet, self.in_reply_to_status_id)
        except Exception, e:
            self.tabbyLogger(str(e), 'ERROR')
            return
        self.tabbyLogger(tweet)

    def play(self, songUrl):
        '''
        Play song with mpg123 asynchronously
        '''
        self.proc = Popen([mpg123_path, songUrl])
        self.tabbyLogger('Playing...' + songUrl)

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
            self.tabbyLogger(query)
            self.mention_from = tweet.user.screen_name
            self.in_reply_to_status_id = tweet.id
            self.grooveStream(query)

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
                self.api.update_status(tweet, self.in_reply_to_status_id)
            except Exception, e:
                self.tabbyLogger(str(e), 'ERROR')
                return
            self.tabbyLogger(tweet)

    def playLastestMentionSong(self, tweet):
        '''
        Parse tweet and play song
        '''
        self.tabbyLogger(':playLastestMentionSong')
        if self.api == None:
            self.api = tweepy.API(auth)
        self.parseTweet(tweet)



class TwitterStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        print('@' + status.user.screen_name + ' ' + status.text)
        player = TabbyPlayer()
        player.playLastestMentionSong(status)
        
    def on_error(self, status_code):
        print >> sys.stderr, 'Encountered error with status code:', status_code
        return True # Don't kill the stream

    def on_timeout(self):
        print >> sys.stderr, 'Timeout...'
        return True # Don't kill the stream


if __name__ == '__main__':
        
    ### 1. Authentication setup ###
    
    auth = tweepy.OAuthHandler(TWITTER_SETTINGS['consumer_key'], TWITTER_SETTINGS['consumer_secret'])
    auth.set_access_token(TWITTER_SETTINGS['access_token_key'], TWITTER_SETTINGS['access_token_secret'])
    
    ### 2. Listener to search and process twitter @mention ###

    sapi = tweepy.streaming.Stream(auth, TwitterStreamListener())
    sapi.filter(track=['@wktabby'])
