import logging
import time
from typing import Optional

import urllib3

from lolaudit.exceptions import SummonerInfoError
from lolaudit.lcu.auth import get_lcu_port_and_token, wait_for_lcu_port_and_token
from lolaudit.models import SummonerInfo

from .client_requester import ClientRequester
from .client_web_socket import ClientWebSocket

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


class LeagueClient(ClientRequester, ClientWebSocket):
    def __init__(self) -> None:
        super().__init__()
        self.token: Optional[str] = None
        self.port: Optional[str] = None
        self.summoner_info: SummonerInfo
        self.is_running: bool = True

    def start(self) -> None:

        logger.info("等待授權...")
        while self.is_running:
            auth = get_lcu_port_and_token()
            if auth is not None:
                self.port, self.token = auth
                break
            time.sleep(1)
        else:
            logger.info("應用程式停止,結束授權等待")
            return
        logger.info(f"授權成功\n  port: {self.port}\n  token: {self.token}")
        self.start_websocket()

    def stop(self) -> None:
        self.stop_websocket()
        self.is_running = False

    def is_connection(self) -> bool:
        if self.get("/lol-summoner/v1/current-summoner"):
            return True
        return False

    def load_summoner_info(self) -> None:
        me = self.get("/lol-summoner/v1/current-summoner")
        self.summoner_info = SummonerInfo(**me)

    def wait_for_load_summoner_info(self) -> None:
        import time

        logger.info("嘗試獲取召喚師狀態...")
        while self.is_running:
            try:
                self.load_summoner_info()
            except SummonerInfoError:
                pass
            except Exception as e:
                logger.warning(f"無法獲取召喚師狀態: {e}")
            else:
                break
            time.sleep(1)
        else:
            logger.info("應用程式停止,結束獲取召喚師狀態等待")
            return
        logger.info(
            f"獲取召喚師狀態成功\n  puuid: {self.summoner_info.puuid}\n  gameName: {self.summoner_info.gameName}#{self.summoner_info.tagLine}"
        )
