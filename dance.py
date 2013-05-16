import os
import sys
import time
import logging
from subprocess import Popen
import tweepy
from config import TWITTER_SETTINGS, APP_SETTINGS
import groove_dl.groove as groove


db = APP_SETTINGS['db']
log = APP_SETTINGS['log']
mpg123_path = APP_SETTINGS['mpg123_path']

def printUnicode(str):
    '''
    Print debug information, by default python 2 is ascii encoded in xbmc 
    '''
    print str.encode('utf-8')


class TabbyPlayer(tweepy.StreamListener):
    def __init__(self):
        self.api = None
        self.proc = None
        self.tag = None
        self.mention_from = None
        self.in_reply_to_status_id = None
        self.artist = ''
        self.title = ''

    def tweetCurrentSong(self):
        '''
        Post tweet of current playing song 
        '''
        tweet = None
        try:
            #if self.in_reply_to_status_id and self.mention_from:
            # streaming from grooveshark (in response to twitter)
            verbs =['dancing','jamming', 'shaking']
            tweet = '@' + self.mention_from + ' I am ' + verbs[random.randint(0,2)] + ' to ' + self.title + ' by ' + self.artist + ' right meow!'
            self.api.update_status(tweet, self.in_reply_to_status_id)
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
            print query
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
                logger.error(str(e))
                return
            logger.info(tweet)

    def searchLatestAtMention(self, tweets):
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


    def playLastestMentionSong(self, tweets):
        '''
        Parse tweet and play song
        '''
        logger.info(':playLastestMentionSong')
        if self.api == None:
            auth = tweepy.OAuthHandler(TWITTER_SETTINGS['consumer_key'], TWITTER_SETTINGS['consumer_secret'])
            auth.set_access_token(TWITTER_SETTINGS['access_token_key'], TWITTER_SETTINGS['access_token_secret'])
            self.api = tweepy.API(auth)
        for tweet in tweets:
            print tweet.id, tweet.text
            tweet = self.searchLatestAtMention(tweets)
            self.parseTweet(tweet)

    def on_status(self, status):
        self.playLastestMentionSong(status);

    def on_error(self, status_code):
        print >> sys.stderr, 'Encountered error with status code:', status_code
        return True # Don't kill the stream

    def on_timeout(self):
        print >> sys.stderr, 'Timeout...'
        return True # Don't kill the stream


if __name__ == '__main__':
    
    ### 0. Logger setup

    logger = logging.getLogger('TabbyDances')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(log)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    
    ### 1. Listener to search and process twitter @mention ###
    
    # player = TabbyPlayer()
    # player.start()

    sapi = tweepy.streaming.Stream(auth, TabbyPlayer())
    sapi.filter(track=['@wktabby'])
