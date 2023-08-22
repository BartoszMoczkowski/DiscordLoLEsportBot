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
    def __init__(self, dict) -> None:
        self.name = dict['name']
        self.image = dict['image']
        if self.name == 'TBD':
            return
        self.result = dict['result']['outcome']
        self.game_wins = dict['result']['outcome']
        self.record_wins = dict['record']['wins']
        self.record_losses = dict['record']['losses']

    def __str__(self) -> str:
        if self.name == "TBD":
            return self.name
        return f"{self.name} {self.record_wins}-{self.record_losses}"

    def __repr__(self) -> str:
        return str(self)


class Match():
    def __init__(self, dict) -> None:
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

    def __str__(self) -> str:
        return f"{self.league} {self.block_name}\n\
        {self.start_time}\n\
        {self.team1} {self.team1.game_wins}-{self.team2.game_wins} {self.team2}\n"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, __value: object) -> bool:
        return self.id == __value.id


class Api():
    default_query_parameters = {"hl": "en-US"}
    headers = {"x-api-key": X_API_KEY}

    def get_leagues(self):
        response = requests.api.get(
            HOST+GET_LEAGUES, self.default_query_parameters, headers=self.headers)
        leagues_json = json.loads(response.content)['data']['leagues']
        return {league['name']: league['id'] for league in leagues_json}

    def get_schedule(self, league_id, upcoming=False):
        query_parameters = self.default_query_parameters
        query_parameters['leagueId'] = league_id
        response = requests.api.get(
            HOST+GET_SCHEDULE,
            query_parameters,
            headers=self.headers
        )
        matches_json = json.loads(response.content)[
            'data']['schedule']['events']
        if upcoming:
            matches_json = list(
                filter(lambda match: match['state'] != 'completed', matches_json))
        return [Match(match) for match in matches_json]


if __name__ == "__main__":
    api = Api()
    leagues = api.get_leagues()
    matches = api.get_schedule(leagues['LEC'],)
    print(matches)
