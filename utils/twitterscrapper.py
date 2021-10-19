import tweepy
import time

class TweetScraper(object):
    """docstring for TweetScraper"""
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        super(TweetScraper, self).__init__()
        
        try:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            self.api = tweepy.API(auth)
        except Exception as e:
            self.api = None
            raise e
        

    def scrape_tweet_media(self, id):
        """Extracts data from the tweet source.
        Parameters
        ----------
        id : str
            The tweet id
        Returns
        -------
        list
            A list containing several important values.
        """
        media = list()
        try:
            time.sleep(3)   # Delays for 3 seconds. to avoid exceed quota
            status = self.api.get_status(id, tweet_mode='extended')
            if 'media' in status.extended_entities:
                for image in status.extended_entities['media']:
                    media.append(image['media_url'])
            return media
        except Exception as e:
            raise e