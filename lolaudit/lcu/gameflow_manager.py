import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot
from stringcase import constcase

from lolaudit.exceptions import UnknownGameflowStateError
from lolaudit.models import Gameflow
from lolaudit.utils import web_socket

if TYPE_CHECKING:
    from . import LeagueClient

logger = logging.getLogger(__name__)


class GameflowManager(QObject):

    gameflow_change = Signal(Gameflow)

    def __init__(self, client: "LeagueClient"):
        super().__init__()
        self.__client = client
        self.__client.websocket_on_message.connect(self.__on_websocket_on_message)

    @web_socket.subscribe("/lol-gameflow/v1/gameflow-phase")
    @Slot(str)
    def __on_websocket_on_message(self, gameflow: str):
        gameflow = constcase(gameflow)
        try:
            self.gameflow_change.emit(Gameflow[gameflow])
        except KeyError:
            logger.warning(f"未知的gameflow狀態: {gameflow}")
            self.gameflow_change.emit(Gameflow.UNKNOWN)

    def start(self):
        url = "/lol-gameflow/v1/gameflow-phase"
        self.__client.subscribe(url)

    def get_gameflow(self) -> Gameflow:
        """
        gameflow_list = ['"None"'      , '"Lobby"'       , '"Matchmaking"',
                         '"ReadyCheck"', '"ChampSelect"' , '"InProgress"' ,
                         '"Reconnect"' , '"PreEndOfGame"', '"EndOfGame"' ,]
        """
        try:
            url = "/lol-gameflow/v1/gameflow-phase"
            gameflow = self.__client.get(url)
            gameflow = constcase(gameflow)
            return Gameflow[gameflow]
        except KeyError:
            raise UnknownGameflowStateError(f"未知的gameflow狀態: {gameflow}")
