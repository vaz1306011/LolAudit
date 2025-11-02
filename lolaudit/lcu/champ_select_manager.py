import logging
import time

from lolaudit.lcu.league_client import LeagueClient

logger = logging.getLogger(__name__)


class ChampSelectManager:

    def __init__(self, client: LeagueClient):
        self.client = client

    def __get_champ_select_session(self):
        url = "/lol-champ-select/v1/session"
        return self.client.requester.get(url)

    def __get_champ_select_timer(self) -> dict:
        url = "/lol-champ-select/v1/session/timer"
        return self.client.requester.get(url)

    def get_champ_select_remaining_time(self):
        response = self.__get_champ_select_timer()
        adjustedTimeLeftInPhase = response["adjustedTimeLeftInPhase"] / 1000
        internalNowInEpochMs = response["internalNowInEpochMs"] / 1000
        remaining_time = (adjustedTimeLeftInPhase + internalNowInEpochMs) - time.time()
        return remaining_time

    def get_champ_select_my_team(self) -> list:
        session = self.__get_champ_select_session()
        myTeam = session.get("myTeam", [])
        return myTeam

    def get_champ_select_actions(self) -> list:
        """
        types = [[ban, ...], [ten_bans_reveal], [pick, pick], ...]
        """
        session = self.__get_champ_select_session()
        actions = session.get("actions", [])
        return actions
