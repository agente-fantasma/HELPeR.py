from datetime import datetime
import requests
import json
from utils import default

class TweetScraper(object):
    """docstring for TweetScraper"""

    def __init__(self):
        super(TweetScraper, self).__init__()
        self.config = default.config()
        self.headers = self.config["twitter_data"]["bearer_token"]
        self.base_url = self.config["twitter_data"]["base_url"]


    def get_tweet_data(self, tweet_id):

        tweet_data = False
        
        try:
            self._request_token()
            final_url = self.base_url + \
                f"statuses/show.json?id={tweet_id}&tweet_mode=extended"

            # We make a GET requeswt to the tweet url.
            with requests.get(final_url, headers=self.headers) as tweet_response:
                tweet_data = self._scrape_tweet(tweet_response.text)
        except Exception as e:
            print(e)
        finally:
            return tweet_data


    def _scrape_tweet(self, data):
        """Extracts data from the tweet JSON file.

        Parameters
        ----------
        data : str
            The tweet JSON string.

        Returns
        -------
        dict
            A dictionary Containing several important values.

        """

        # We init the BeautifulSoup object and begin extracting values.
        tweet = json.loads(data)

        timestamp = datetime.strptime(
            tweet["created_at"], "%a %b %d %H:%M:%S +0000 %Y").timestamp()

        tweet_id = tweet["id"]
        fullname = tweet["user"]["name"]
        username = tweet["user"]["screen_name"]
        permalink = f"https://twitter.com/status/{username}/{tweet_id}"

        favorites = tweet["favorite_count"]
        retweets = tweet["retweet_count"]

        # We extract all the images and video links.
        image_links = list()
        video_links = list()

        if "extended_entities" in tweet:

            for item in tweet["extended_entities"]["media"]:

                if item["type"] == "photo":
                    image_links.append(
                        item["media_url_https"]+"?format=jpg&name=4096x4096")
                elif item["type"] == "video":
                    video_links.append(item["video_info"]["variants"][0]["url"])

        # We add a little padding for the other links inside the tweet message.
        tweet_text = tweet["full_text"].replace("http", " http").strip()
        tweet_text = tweet["full_text"].split(
            "https://t.co")[0].split("http://t.co")[0].replace("\n", "").replace("  ", " ").strip()

        return {
            "permalink": permalink,
            "timestamp": timestamp,
            "fullname": fullname,
            "username": username,
            "favorites": favorites,
            "retweets": retweets,
            "images": image_links,
            "videos": video_links,
            "text": tweet_text
        }


    def _request_token(self):
        """Gets a Guest Token from the API."""

        print("Requesting token...")

        with requests.post(self.base_url + "guest/activate.json", headers=self.headers) as response:
            guest_token = response.json()["guest_token"]
            self.headers["x-guest-token"] = guest_token
            print("Token received.")
