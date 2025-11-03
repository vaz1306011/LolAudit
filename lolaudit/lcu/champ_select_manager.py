import logging
import time
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
        self.__timer = None

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
        url = "/lol-champ-select/v1/session"
        self.__client.subscribe(url)
        self.__session = self.__get_champ_select_session()

        self.__timer = QTimer()
        self.__timer.setInterval(250)
        self.__timer.timeout.connect(self.__emit_champ_select_remaining_time)
        self.__timer.start()

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
        if self.__timer:
            self.__timer.stop()
        self.end.emit()
