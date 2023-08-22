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

LEAGUES = ["LEC", "LCK", "LPL", "LCS", "MSI", "Worlds"]
GAMES_FILE = "upcoming_games.pkl"
BET_FILE = "bets.csv"


class MyClient(discord.Client):
    def __init__(self, *, intents: Intents, **options: Any) -> None:
        self.lol_api = lol_esport_api.Api()
        self.read_games_data()
        super().__init__(intents=intents, **options)

    def read_bet_data(self):
        if not os.path.isfile():
            self.bets = pd.DataFrame(
                columns=['nickname', 'id', 'correct', 'incorrect'])
            return
        with open(BET_FILE, 'r') as file:
            self.bets = pd.read_csv(file)

    def write_bet_data(self):

        with open(BET_FILE, 'w') as file:
            self.bets.to_csv(file)

    def update_bet_user(self, user: discord.client.User, bet_hit: bool):

        if not any(self.bets.id == user.id):
            self.bets = self.bets.append(pd.DataFrame([[user.name, user.id, 0, 0]], columns=[
                                         'nickname', 'id', 'correct', 'incorrect']))
        if bet_hit:
            self.bets.loc[(self.id == user.id), 'correct'] += 1
        else:
            self.bets.loc[(self.id == user.id), 'incorrect'] += 1

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

        msg = await target_channel.send(f"Upcoming Game {game}")
        await msg.add_reaction('1️⃣')
        await msg.add_reaction('2️⃣')

    async def api_update(self):

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
        self.read_channel.start()

    async def on_message(self, message):
        if message.author == self.user:
            print(message.reactions)
            return

    @tasks.loop(hours=1)
    async def write_to_channel(self):
        await self.api_update()

    async def read_channel(self):
        channels = client.get_all_channels()
        for channel in channels:
            if channel.name == 'esport':
                target_channel = channel
        if target_channel == None:
            return
        print(target_channel.id)
        msg = [message async for message in target_channel.history(limit=10)]
        for m in msg:
            if(len(m.reactions) == 0):
                await m.add_reaction('1️⃣') #🗿
                #await m.remove_reaction('👍', self.user)
            


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(os.getenv('TOKEN'))
