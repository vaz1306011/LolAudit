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
        self.__client.websocket_message.connect(self.__on_websocket_message)

    def __emit_gameflow_change(self, gameflow: str) -> None:
        logger.info(f"gameflow: {gameflow}")
        gameflow = constcase(gameflow)
        try:
            self.gameflow_change.emit(Gameflow[gameflow])
        except KeyError:
            logger.warning(f"未知的gameflow狀態: {gameflow}")
            self.gameflow_change.emit(Gameflow.UNKNOWN)

    @Slot(str, str)
    @web_socket.subscribe("/lol-gameflow/v1/gameflow-phase")
    def __on_websocket_message(self, gameflow: str):
        self.__emit_gameflow_change(gameflow)

    def start(self):
        url = "/lol-gameflow/v1/gameflow-phase"
        self.__client.subscribe(url)
        response = self.__client.get(url)
        if isinstance(response, str):
            self.__emit_gameflow_change(response)
        else:
            raise UnknownGameflowStateError(str(response))
