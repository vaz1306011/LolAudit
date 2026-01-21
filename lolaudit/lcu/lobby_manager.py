import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer

from lolaudit.models import Gameflow

if TYPE_CHECKING:
    from .league_client import LeagueClient
    from .match_manager import MatchManager

logger = logging.getLogger(__name__)


class LobbyManager(QObject):
    def __init__(self, client: "LeagueClient", match_manager: "MatchManager") -> None:
        super().__init__()
        self.__client = client
        self.__match_manager = match_manager
        self.__gameflow: Gameflow | None = None
        self.__auto_start_matchmaking = False
        self.__auto_start_attempts = 0
        self.__auto_start_timer = QTimer()
        self.__auto_start_timer.setInterval(500)
        self.__auto_start_timer.timeout.connect(self.__try_start_matchmaking)

    def set_gameflow(self, gameflow: Gameflow) -> None:
        self.__gameflow = gameflow
        if gameflow == Gameflow.LOBBY and self.__auto_start_matchmaking:
            self.__auto_start_matchmaking = False
            self.__match_manager.start_matchmaking()
            if self.__auto_start_timer.isActive():
                self.__auto_start_timer.stop()

    def match_toggle(self, gameflow: Gameflow | None) -> None:
        if gameflow is None:
            return
        if gameflow == Gameflow.MATCHMAKING:
            self.__match_manager.stop_matchmaking()
            return
        if gameflow == Gameflow.NONE:
            self.__start_one_key_queue()
            return
        self.__match_manager.start_matchmaking()

    def stop(self) -> None:
        self.__auto_start_matchmaking = False
        self.__auto_start_attempts = 0
        if self.__auto_start_timer.isActive():
            self.__auto_start_timer.stop()

    def __start_one_key_queue(self) -> None:
        self.__auto_start_matchmaking = True
        self.__auto_start_attempts = 0
        if not self.__auto_start_timer.isActive():
            self.__auto_start_timer.start()
        self.__match_manager.create_lobby()

    def __try_start_matchmaking(self) -> None:
        if not self.__auto_start_matchmaking:
            if self.__auto_start_timer.isActive():
                self.__auto_start_timer.stop()
            return
        if self.__gameflow == Gameflow.LOBBY:
            self.__auto_start_matchmaking = False
            self.__match_manager.start_matchmaking()
            self.__auto_start_timer.stop()
            return
        self.__auto_start_attempts += 1
        if self.__auto_start_attempts >= 10:
            logger.debug("一鍵列隊等待超時")
            self.__auto_start_matchmaking = False
            self.__auto_start_timer.stop()
