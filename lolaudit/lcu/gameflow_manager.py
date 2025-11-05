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

    gameflowChange = Signal(Gameflow)

    def __init__(self, client: "LeagueClient"):
        super().__init__()
        self.__client = client
        self.__client.websocketOnMessage.connect(self.__onGameFlowChange)

    @web_socket.subscribe("/lol-gameflow/v1/gameflow-phase")
    @Slot(str)
    def __onGameFlowChange(self, gameflow: str):
        gameflow = constcase(gameflow)
        try:
            self.gameflowChange.emit(Gameflow[gameflow])
        except KeyError:
            logger.warning(f"未知的gameflow狀態: {gameflow}")
            self.gameflowChange.emit(Gameflow.UNKNOWN)

    def start(self):
        url = "/lol-gameflow/v1/gameflow-phase"
        self.__client.subscribe(url)
        self.gameflowChange.emit(self.get_gameflow())

    def get_gameflow(self) -> Gameflow:
        """
        gameflow_list = ['"None"'      , '"Lobby"'       , '"Matchmaking"',
                         '"ReadyCheck"', '"ChampSelect"' , '"InProgress"' ,
                         '"Reconnect"' , '"PreEndOfGame"', '"EndOfGame"' ,]
        """
        try:
            url = "/lol-gameflow/v1/gameflow-phase"
            gameflow = self.__client.get(url)
            if not gameflow:
                return Gameflow.LOADING
            gameflow = constcase(gameflow)
            return Gameflow[gameflow]
        except KeyError:
            raise UnknownGameflowStateError(f"未知的gameflow狀態: {gameflow}")
