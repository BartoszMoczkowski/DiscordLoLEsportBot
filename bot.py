from typing import Any
import discord
import os
from discord.flags import Intents
import dotenv
from discord.ext import tasks
import pandas as pd
import lol_esport_api
import pickle
import os

dotenv.load_dotenv()

LEAGUES = "LEC"
GAMES_FILE = "upcoming_games.pkl"


class MyClient(discord.Client):
    def __init__(self, *, intents: Intents, **options: Any) -> None:
        self.lol_api = lol_esport_api.Api()
        super().__init__(intents=intents, **options)

    def read_games_data(self):
        if not os.path.isfile(GAMES_FILE):
            return
        with open(GAMES_FILE, 'rb') as file:
            self.upcoming_games = pickle.load(file)

    def api_starup(self):

        self.leagues = self.lol_api.get_leagues()
        upcoming_games = []
        for league in LEAGUES:
            league_id = self.leagues[league]
            upcoming_games += self.lol_api.get_schedule(
                league_id, upcoming=True)
        for game in upcoming_games:
            if game
        self.upcoming_games = upcoming_games

    async def on_ready(self):
        print("Logged on as ", self.user)
        self.write_to_channel.start()

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content == "yo":
            await message.channel.send("Yo ")

    @tasks.loop(seconds=10)
    async def write_to_channel(self):
        channels = client.get_all_channels()
        for channel in channels:
            if channel.name == "esport":
                target_channel = channel

        if target_channel == None:
            return

        await target_channel.send("Esport Man")


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(os.getenv('TOKEN'))
