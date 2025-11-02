import logging
import threading
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot

from lolaudit.exceptions import UnknownGameflowStateError
from lolaudit.models import Gameflow
from lolaudit.utils import web_socket

if TYPE_CHECKING:
    from . import LeagueClient

logger = logging.getLogger(__name__)


class GameflowManager(QObject):

    on_gameflow_change = Signal(Gameflow)

    def __init__(self, client: "LeagueClient"):
        super().__init__()
        self.__client = client
        self.__client.on_websocket_message.connect(self.__new_main)
        self.__main_flag = threading.Event()

    @Slot(str)
    @web_socket.subscribe("/lol-gameflow/v1/gameflow-phase")
    def __new_main(self, gameflow: str):
        logger.info(f"gameflow: {gameflow}")
        match gameflow:
            case "None":
                self.on_gameflow_change.emit(Gameflow.NONE)

            case "Lobby":
                self.on_gameflow_change.emit(Gameflow.LOBBY)

            case "Matchmaking":
                self.on_gameflow_change.emit(Gameflow.MATCHMAKING)

            case "ReadyCheck":
                self.on_gameflow_change.emit(Gameflow.READY_CHECK)

            case "ChampSelect":
                self.on_gameflow_change.emit(Gameflow.CHAMP_SELECT)

            case "InProgress":
                self.on_gameflow_change.emit(Gameflow.IN_PROGRESS)

            case "Reconnect":
                self.on_gameflow_change.emit(Gameflow.RECONNECT)

            case "PreEndOfGame":
                self.on_gameflow_change.emit(Gameflow.PRE_END_OF_GAME)

            case "EndOfGame":
                self.on_gameflow_change.emit(Gameflow.END_OF_GAME)

            case _:
                raise UnknownGameflowStateError(gameflow)

    def __main(self):
        while not self.__main_flag.is_set():
            gameflow = self.__client.get_gameflow()
            try:
                logger.info(f"gameflow: {gameflow}")
                match gameflow:
                    case None:
                        self.on_gameflow_change.emit(Gameflow.LOADING)
                        self.__client.wait_for_connect()

                    case "None":
                        self.on_gameflow_change.emit(Gameflow.NONE)

                    case "Lobby":
                        self.on_gameflow_change.emit(Gameflow.LOBBY)

                    case "Matchmaking":
                        self.on_gameflow_change.emit(Gameflow.MATCHMAKING)

                    case "ReadyCheck":
                        self.on_gameflow_change.emit(Gameflow.READY_CHECK)

                    case "ChampSelect":
                        self.on_gameflow_change.emit(Gameflow.CHAMP_SELECT)

                    case "InProgress":
                        self.on_gameflow_change.emit(Gameflow.IN_PROGRESS)

                    case "Reconnect":
                        self.on_gameflow_change.emit(Gameflow.RECONNECT)

                    case "PreEndOfGame":
                        self.on_gameflow_change.emit(Gameflow.PRE_END_OF_GAME)

                    case "EndOfGame":
                        self.on_gameflow_change.emit(Gameflow.END_OF_GAME)

                    case _:
                        raise UnknownGameflowStateError(gameflow)
            except Exception as e:
                logger.error(f"{e}")
                self.on_gameflow_change.emit(Gameflow.UNKNOWN)

            time.sleep(0.5)
        else:
            logger.info("停止程序")

    def start(self):
        self.__client.subscribe("/lol-gameflow/v1/gameflow-phase")
        # self.__main_flag.clear()
        # main_thread = threading.Thread(target=self.__main)
        # main_thread.daemon = True
        # main_thread.start()

    def stop(self) -> None:
        self.__main_flag.set()
