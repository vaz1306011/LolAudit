import logging
import time
from pprint import pformat
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from lolaudit.utils import web_socket

if TYPE_CHECKING:
    from . import LeagueClient

logger = logging.getLogger(__name__)


class ChampSelectManager(QObject):
    change = Signal()
    remaining_time_change = Signal(int)
    end = Signal()

    def __init__(self, client: "LeagueClient"):
        super().__init__()
        self.__client = client
        self.__client.websocket_on_message.connect(self.__emit_champ_select_change)
        self.__session: dict
        self.timer = QTimer(self)

    def __get_champ_select_session(self):
        url = "/lol-champ-select/v1/session"
        return self.__client.get(url)

    @web_socket.subscribe("/lol-champ-select/v1/session")
    @Slot(dict)
    def __emit_champ_select_change(self, session: dict) -> None:
        self.__session = session

    def __emit_champ_select_remaining_time(self):
        timer = self.__session["timer"]
        adjustedTimeLeftInPhase = timer["adjustedTimeLeftInPhase"] / 1000
        internalNowInEpochMs = timer["internalNowInEpochMs"] / 1000
        remaining_time = (adjustedTimeLeftInPhase + internalNowInEpochMs) - time.time()
        self.remaining_time_change.emit(remaining_time)

    def start(self) -> None:
        logger.info("啟動Champ Select管理器")
        url = "/lol-champ-select/v1/session"
        self.__client.subscribe(url)
        self.__session = self.__get_champ_select_session()
        self.timer.timeout.connect(self.__emit_champ_select_remaining_time)
        self.timer.start(250)

    def get_champ_select_actions(self) -> list:
        """
        types = [[ban, ...], [ten_bans_reveal], [pick, pick], ...]
        """
        session = self.__get_champ_select_session()
        actions = session.get("actions", [])
        return actions

    def stop(self) -> None:
        url = "/lol-champ-select/v1/session"
        self.__client.unsubscribe(url)
        self.timer.stop()
        self.end.emit()
