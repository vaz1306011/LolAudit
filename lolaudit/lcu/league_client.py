import logging
from typing import Optional

import requests
import urllib3

from lolaudit.exceptions import SummonerInfoError
from lolaudit.utils import Requester

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


class LeagueClient:
    def __init__(self):
        super().__init__()

        self.me = None
        self.puuid = None
        self.gameName = None
        self.tagLine = None

        self.requester = Requester()
        self.gameflow_manager = None

    def wait_for_refresh_port_and_token(self) -> None:
        self.requester.wait_for_refresh_port_and_token()

    def load_summoner_info(self) -> None:
        self.me = self.requester.get("/lol-summoner/v1/current-summoner")
        self.puuid = self.me.get("puuid")
        self.gameName = self.me.get("gameName")
        self.tagLine = self.me.get("tagLine")
        if not (self.puuid and self.gameName and self.tagLine):
            raise SummonerInfoError

    def wait_for_load_summoner_info(self) -> None:
        import time

        while True:
            try:
                self.load_summoner_info()
            except SummonerInfoError:
                pass
            except Exception as e:
                logger.warning(f"無法獲取召喚師狀態: {e}")
            else:
                break
            time.sleep(3)

    def get_gameflow(self) -> Optional[str]:
        """
        gameflow_list = ['"None"'      , '"Lobby"'       , '"Matchmaking"',
                         '"ReadyCheck"', '"ChampSelect"' , '"InProgress"' ,
                         '"Reconnect"' , '"PreEndOfGame"', '"EndOfGame"' ,]
        """
        try:
            url = "/lol-gameflow/v1/gameflow-phase"
            response = self.requester.get(url)
            if not response:
                return None
            return str(response)
        except requests.exceptions.MissingSchema:
            logger.warning("無法獲取遊戲流程")
            return None

    def get_matchmaking_info(self) -> dict:
        url = "/lol-matchmaking/v1/search"
        return self.requester.get(url)

    def start_matchmaking(self) -> None:
        url = "/lol-lobby/v2/lobby/matchmaking/search"
        self.requester.post(url)

    def quit_matchmaking(self) -> None:
        url = "/lol-lobby/v2/lobby/matchmaking/search"
        self.requester.delete(url)

    def accept_match(self) -> None:
        url = "/lol-matchmaking/v1/ready-check/accept"
        self.requester.post(url)

    def decline_match(self) -> None:
        url = "/lol-matchmaking/v1/ready-check/decline"
        self.requester.post(url)
