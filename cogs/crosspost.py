import time
import discord
import psutil
import os
import re
import tempfile
from io import BytesIO
from urllib.request import urlopen

from expiringdict import ExpiringDict
from pixivpy3 import AppPixivAPI

from discord.ext import commands
from utils import default
from utils.tweetscrapper import TweetScraper

from discord import File, Message, TextChannel, Thread

CACHE = ExpiringDict(max_len=1000, max_age_seconds=172800)

class Crosspost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.config()
        self.process = psutil.Process(os.getpid())
        self.temp_dir = tempfile.gettempdir()
        self.twitter_scrapper = TweetScraper()
        self.twitter_regex = re.compile('twitter\.com\/(?:#!\/)?(\w+)\/status(es)?\/(\d+)')
        self.pixiv_regex = re.compile(
            r"https?://(?:www\.)?pixiv\.net/(?:member_illust\.php\?"
            r"[\w]+=[\w]+(?:&[\w]+=[\w]+)*|(?:\w{2}/)?artworks/\d+(?:#\w*)?)"
        )
        self.pixiv_api = AppPixivAPI()
    
    def _too_large(self, message: Message) -> bool:
        return message.content.startswith("Image too large to upload")

    async def _send(self, img_url, img_name, channel, local = False) -> None:
        if (local):
            print(img_url)
            with open(img_url, 'rb') as fin:
                image_data = BytesIO(fin.read())
        else:
            image_data = BytesIO(urlopen(img_url).read())
        print(img_name)
        file = File(image_data, img_name)

        msg = await channel.send(file=file)
        embedded = self._too_large(msg)
        if embedded:
            channel.send('File too large, sorry ;(')
        
        image_data.seek(0)
        image_data.truncate(0)


    async def _do_tweet_crosspost(self, id_of_tweet, channel)-> None:

        if cache_of_tweet := CACHE.get('twitter_{}'.format(id_of_tweet)):
            print("Cache : {}".format(cache_of_tweet))
            return
        else:
            try:
                tweet_data = self.twitter_scrapper.get_tweet_data(id_of_tweet)
                tweet_media = tweet_data["images"] if 'images' in tweet_data and len(tweet_data['images']) > 0 else []
                if tweet_media:
                    CACHE['twitter_{}'.format(id_of_tweet)] = tweet_media.copy()
                    for idx, img_url in enumerate(tweet_media, start=1):
                        _filename = 'twitter_{}_status_{}_{}.jpeg'.format(
                            tweet_data['username'], id_of_tweet, idx)
                        await self._send(img_url, _filename, channel)
            except Exception as e:
                print(e)

    async def _do_pixiv_crosspost(self, illust_id, channel) -> None:
        if cache_of_pixiv := CACHE.get('pixiv_{}'.format(illust_id)):
            print("Cache : {}".format(cache_of_pixiv))
            return
        else:
            time.sleep(3)
            try:
                self.pixiv_api.auth(
                    refresh_token=self.config['pixiv_data']['refresh_token'])
                json_result = self.pixiv_api.illust_detail(illust_id)
                images = []
                for page in json_result.illust.meta_pages:
                    _filename = "pixiv_"+((page.image_urls.large).split("/"))[-1]
                    images.append(_filename)
                    self.pixiv_api.download(page.image_urls.large, path=self.temp_dir, name=_filename)
                for image in images:
                    await self._send(self.temp_dir + "/" + image, image, channel, local=True)
                CACHE['pixiv_{}'.format(illust_id)] = images.copy()
            except Exception as e:
                print(e)
            finally:
                return


    @commands.command()
    async def crosspost(self, ctx):
        """ Pong! """
        before = time.monotonic()
        before_ws = int(round(self.bot.latency * 1000, 1))
        message = await ctx.send("Crosspost Working")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"Crosspost Cogs WS: {before_ws}ms  |  REST: {int(ping)}ms")

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        '''on_message async function will listen to chat comments in discord trhu cog.listener decorator
        it uses the textreplies statics functions to read the list of responses from txt and csv files
        Args:
            message (Message): discord.py Message Object
        '''
        
        if message.content.startswith(self.config['prefix'][0]):
            return
        if (guild := message.guild) is None or message.author.bot:
            return
        channel = message.channel
        me = guild.me
        assert isinstance(channel, (TextChannel, Thread))
        assert isinstance(me, discord.Member)
        if not channel.permissions_for(me).send_messages:
            return
        if 'http' in message.content: #it's a url
            #twitter scenario
            if id_of_tweet := self.twitter_regex.search(message.content).group(3) if self.twitter_regex.search(message.content) else False:
                print("crosspost proccess id: " + id_of_tweet)
                await self._do_tweet_crosspost(id_of_tweet, channel)
                await self.bot.process_commands(message)
            #pixiv scenario
            elif illust_id := self.pixiv_regex.search(message.content).group() if self.pixiv_regex.search(message.content) else False:
                illust_id = re.findall(r'\d+', illust_id)[-1]
                print("crosspost proccess id: " + illust_id)
                await self._do_pixiv_crosspost(illust_id, channel)
                await self.bot.process_commands(message)
            return

                    
def setup(bot):
    bot.add_cog(Crosspost(bot))
