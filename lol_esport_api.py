import requests
import json
from datetime import datetime
import base64

X_API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"

# Endpoints
HOST = "https://esports-api.lolesports.com/persisted/gw/"
GET_LEAGUES = "getLeagues"
GET_STANDINGS = "getStandings"
GET_SCHEDULE = "getSchedule"
GET_LIVE = "getLive"
GET_TEAMS = "getTeams"


class Team():
    def __init__(self, dict, test=False) -> None:
        if test:
            return
        self.name = dict['name']
        self.image = dict['image']
        if self.name == 'TBD':
            return
        self.result = dict['result']['outcome']
        self.game_wins = dict['result']['outcome']
        self.record_wins = dict['record']['wins']
        self.record_losses = dict['record']['losses']

    def create_test_team(self):
        self.name = 'name'
        self.image = 'img'
        self.result = 'None'
        self.game_wins = 0
        self.record_losses = 0
        self.record_wins = 0
        return self

    def __str__(self) -> str:
        if self.name == "TBD":
            return self.name
        return f"{self.name} {self.record_wins}-{self.record_losses}"

    def __repr__(self) -> str:
        return str(self)


class Match():
    def __init__(self, dict, test=False) -> None:
        if test:
            return
        time_format_zulu = dict['startTime'].replace(
            "T", " ").replace("Z", " UTC")
        self.start_time = datetime.strptime(
            time_format_zulu, "%Y-%m-%d %H:%M:%S %Z")
        self.state = dict["state"]
        self.block_name = dict["blockName"]
        self.league = dict["league"]["name"]
        self.id = dict["match"]["id"]
        self.team1 = Team(dict["match"]["teams"][0])
        self.team2 = Team(dict["match"]["teams"][1])

    def create_test_upcoming(self) -> None:
        self.start_time = datetime.now()
        self.state = 'upcoming'
        self.block_name = 'block_name'
        self.league = 'league'
        self.id = '-1'
        self.team1 = Team({}, True).create_test_team()
        self.team2 = Team({}, True).create_test_team()

    def create_test_completed(self) -> None:
        self.start_time = datetime.now()
        self.state = 'completed'
        self.block_name = 'block_name'
        self.league = 'league'
        self.id = '-1'
        self.team1 = Team({}, True).create_test_team()
        self.team2 = Team({}, True).create_test_team()

    def __str__(self) -> str:

        return f"{self.league} {self.block_name}\n\
        {self.start_time}\n\
        {self.team1}  {self.team2}\n"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, __value: object) -> bool:
        return self.id == __value.id

    def upcoming_string_format(self):
        if not self.team1.name == "TBD":
            team1_str = f"{self.team1.record_wins}-{self.team1.record_losses} {self.team1.name}"
        else:
            team1_str = f"{self.team1.name}"
        if not self.team2.name == "TBD":
            team2_str = f"{self.team2.name} {self.team2.record_wins}-{self.team2.record_losses}"

        else:
            team2_str = f"{self.team2.name}"

        return f"{self.league} {self.block_name}\n\
        {self.start_time}\n\
         {team1_str} vs {team2_str}\n"

    def finished_string_format(self):
        if self.team1.name == 'TBD' or self.team2.name == "TBD":
            print("finished games should not have TBD teams!")
        winning_team = f"{self.team1.name if self.team1.result.lower() == 'win' else self.team2.name}"
        return f"{self.league} {self.block_name}\n\
        {self.start_time}\n\
        result {winning_team} wins\n\
        {self.team1.record_wins}-{self.team1.record_losses} {self.team1.name} {self.team1.game_wins}-{self.team2.game_wins} {self.team1.name} {self.team2.record_wins}-{self.team2.record_losses}\n"


class Api():
    default_query_parameters = {"hl": "en-US"}
    headers = {"x-api-key": X_API_KEY}

    def get_leagues(self):
        response = requests.api.get(
            HOST+GET_LEAGUES, self.default_query_parameters, headers=self.headers)
        leagues_json = json.loads(response.content)['data']['leagues']
        return {league['name']: league['id'] for league in leagues_json}

    def get_schedule(self, league_id):
        query_parameters = self.default_query_parameters
        query_parameters['leagueId'] = league_id
        response = requests.api.get(
            HOST+GET_SCHEDULE,
            query_parameters,
            headers=self.headers
        )
        matches_json = json.loads(response.content)[
            'data']['schedule']['events']
        matches_upcoming = []
        matches_resolved = []
        for match in matches_json:
            if match['match']['teams'][0]['name'] == "TBD":
                continue

            if match['match']['teams'][1]['name'] == "TBD":
                continue

            if match['state'] != 'completed':
                matches_upcoming.append(Match(match))
                continue
            matches_resolved.append(Match(match))
        games = {'upcoming': matches_upcoming, 'resolved': matches_resolved}
        return games

    def get_test_schedule_start(self):
        match = Match({}, test=True)
        match.create_test_upcoming()
        return {'upcoming': [match], 'resolved': []}

    def get_test_schedule_end(self):
        match = Match({}, test=True)
        match.create_test_completed()
        return {'upcoming': [], 'resolved': [match]}


if __name__ == "__main__":
    api = Api()
    leagues = api.get_leagues()
    matches = api.get_schedule(leagues['LEC'],)
    print(matches)
