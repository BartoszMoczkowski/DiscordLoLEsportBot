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
GAMES_FILE = "games.pkl"
GAME_MSG_FILE = "gm.pkl"

BET_FILE = "bets.csv"


class MyClient(discord.Client):
    def __init__(self, *, intents: Intents, testing, **options: Any) -> None:
        self.testing = testing
        self.lol_api = lol_esport_api.Api()
        self.read_games_data()
        self.read_bet_data()
        super().__init__(intents=intents, **options)

    def read_bet_data(self):
        if not os.path.isfile(BET_FILE):
            self.bets = pd.DataFrame(
                columns=['nickname', 'id', 'correct', 'incorrect'])
            return
        with open(BET_FILE, 'r') as file:
            self.bets = pd.read_csv(file)

    def write_bet_data(self):

        with open(BET_FILE, 'w') as file:
            self.bets.to_csv(file, index=False)

    def update_bet_user(self, user: discord.client.User, bet_hit: bool):

        if not any(self.bets.id == user.id):
            self.bets = pd.concat([self.bets, pd.DataFrame(
                [{'nickname': user.name, 'id': user.id, 'correct': 0, 'incorrect': 0}])], ignore_index=True)
        if bet_hit:
            self.bets.loc[(self.bets.id == user.id), 'correct'] += 1
        else:
            self.bets.loc[(self.bets.id == user.id), 'incorrect'] += 1

    def read_games_data(self):
        if not os.path.isfile(GAMES_FILE):
            self.games = {'upcoming': [], 'resolved': []}

        else:
            with open(GAMES_FILE, 'rb') as file:
                self.games = pickle.load(file)

        if not os.path.isfile(GAME_MSG_FILE):
            self.game_to_msg = {-1: -1}
            return
        with open(GAME_MSG_FILE, 'rb') as file:
            self.game_to_msg = pickle.load(file)

    def write_games_data(self):
        with open(GAMES_FILE, 'wb') as file:
            pickle.dump(self.games, file)
        with open(GAME_MSG_FILE, 'wb') as file:
            pickle.dump(self.game_to_msg, file)

    async def on_game_start_notification(self, game: lol_esport_api.Match):
        channels = client.get_all_channels()
        for channel in channels:
            if channel.name == 'esport':
                target_channel = channel
        if target_channel == None:
            return

        reaction_msg = f"Predict with: \n 1️⃣ for {game.team1.name} \n 2️⃣ for {game.team2.name}"
        msg = await target_channel.send(f"Upcoming Game {game.upcoming_string_format()} \n{reaction_msg}")
        await msg.add_reaction('1️⃣')
        await msg.add_reaction('2️⃣')
        return msg.id

    async def on_game_resolved_notification(self, game: lol_esport_api.Match):
        channels = client.get_all_channels()
        for channel in channels:
            if channel.name == 'esport':
                target_channel = channel
        if target_channel == None:
            return
        winner = game.team1 if game.team1.result == "win" else game.team2

        previous_msg = await channel.fetch_message(self.game_to_msg[game.id])
        team1_users, team2_users = await self.read_message_reaction_users(previous_msg)
        for user in team1_users:
            if user in team2_users:
                continue
            if winner == game.team1:
                self.update_bet_user(user, True)
            else:
                self.update_bet_user(user, False)
        for user in team2_users:
            if user in team1_users:
                continue
            if winner == game.team2:
                self.update_bet_user(user, True)
            else:
                self.update_bet_user(user, False)
        print(self.bets.head())

        msg = await target_channel.send(f"Game resolved \n {game.finished_string_format()}")

    async def api_update(self):
        if self.testing == None:
            self.leagues = self.lol_api.get_leagues()
            new_games = {'upcoming': [], 'resolved': []}
            for league in LEAGUES:
                league_id = self.leagues[league]
                new_games['upcoming'] += self.lol_api.get_schedule(
                    league_id)['upcoming']
                new_games['resolved'] += self.lol_api.get_schedule(
                    league_id)['resolved']

        elif self.testing == 'start':
            new_games = self.lol_api.get_test_schedule_start()
        elif self.testing == 'end':
            new_games = self.lol_api.get_test_schedule_end()

        for game in self.games['upcoming']:
            if not game in new_games['upcoming']:
                print(f"game {game} resolved")
                game_index = new_games['resolved'].index(game)

                await self.on_game_resolved_notification(
                    new_games['resolved'][game_index])

        for i, game in enumerate(new_games['upcoming']):
            if not game in self.games['upcoming']:
                print(f"found new game {game}")
                msg_id = await self.on_game_start_notification(game)
                self.game_to_msg[game.id] = msg_id
        self.games = new_games
        self.write_games_data()
        self.write_bet_data()

    async def on_ready(self):
        await self.api_update()
        print("Logged on as ", self.user)
        self.write_to_channel.start()

    def print_users_score(self):
        df = self.bets.copy()
        df['percent correct'] = df['correct']/(df['correct'] + df['incorrect'])
        return df.to_string(columns=['nickname', 'percent correct'], index=False, float_format=lambda x: f"{x:.0%}")

    def print_user_score(self, user):
        df = self.bets.copy()
        df['percent correct'] = df['correct']/(df['correct'] + df['incorrect'])
        return df['nickname', user.name].to_string(columns=['nickname', 'percent correct'], index=False, float_format=lambda x: f"{x:.0%}")

    async def on_message(self, message: discord.message):
        if message.author == self.user:
            return
        if message.content == 'stop':
            await message.channel.send("Stopping")
            await self.close()
        elif message.content == "How boosted are we?":
            await message.channel.send(self.print_users_score())
        elif message.content == "How boosted am I?":
            await message.channel.send(self.print_user_score(message.author))

    @tasks.loop(hours=1)
    async def write_to_channel(self):
        await self.api_update()

    async def read_channel_reactions(self):
        channels = client.get_all_channels()
        for channel in channels:
            if channel.name == 'esport':
                target_channel = channel
        if target_channel == None:
            return
        messages = [message async for message in target_channel.history(limit=10)]
        for message in messages:
            if message.author != client.user:
                continue
            team1_users, team2_users = await self.read_message_reaction_users(
                message)

        return team1_users, team2_users

    async def read_message_reaction_users(self, message):
        react_1_user_list = []
        react_2_user_list = []

        for react in message.reactions:
            if react.emoji == '1️⃣':
                react_1_user_list = [user async for user in react.users() if user != client.user]
            elif react.emoji == '2️⃣':
                react_2_user_list = [user async for user in react.users()if user != client.user]
        return react_1_user_list, react_2_user_list


test = True
if test:
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents, testing='start')
    client.run(os.getenv('TOKEN'))
    client = MyClient(intents=intents, testing='end')
    client.run(os.getenv('TOKEN'))
else:
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents, testing=None)
    client.run(os.getenv('TOKEN'))
