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

LEAGUES = ["LEC", ]
GAMES_FILE = "upcoming_games.pkl"


class MyClient(discord.Client):
    def __init__(self, *, intents: Intents, **options: Any) -> None:
        self.lol_api = lol_esport_api.Api()
        super().__init__(intents=intents, **options)

    def read_games_data(self):
        if not os.path.isfile(GAMES_FILE):
            self.upcoming_games = []
            return
        with open(GAMES_FILE, 'rb') as file:
            self.upcoming_games = pickle.load(file)

    def write_games_data(self):
        with open(GAMES_FILE, 'wb') as file:
            pickle.dump(self.upcoming_games, file)

    async def on_game_start_notification(self, game):
        channels = client.get_all_channels()
        for channel in channels:
            if channel.name == 'esport':
                target_channel = channel
        if target_channel == None:
            return

        await target_channel.send(f"Upcoming Game {game}")

    async def api_update(self):

        self.read_games_data()
        self.leagues = self.lol_api.get_leagues()
        upcoming_games = []
        for league in LEAGUES:
            league_id = self.leagues[league]
            upcoming_games += self.lol_api.get_schedule(
                league_id, upcoming=True)
        for game in self.upcoming_games:
            if not game in upcoming_games:
                print(f"game {game} resolved")
                self.upcoming_games.remove(game)
        for game in upcoming_games:
            if not game in self.upcoming_games:
                print(f"found new game {game}")
                self.upcoming_games.append(game)
                await self.on_game_start_notification(game)
        self.write_games_data()

    async def on_ready(self):
        await self.api_update()
        print("Logged on as ", self.user)
        self.write_to_channel.start()

    async def on_message(self, message):
        if message.author == self.user:
            return

    @tasks.loop(hours=1)
    async def write_to_channel(self):
        await self.api_update()


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(os.getenv('TOKEN'))
