import logging
import threading
import time

from PySide6.QtCore import QObject, Signal

from lolaudit.exceptions import UnknownGameflowStateError
from lolaudit.lcu import LeagueClient
from lolaudit.models import Gameflow

logger = logging.getLogger(__name__)


class GameflowManager(QObject):
    gameflow_change = Signal(Gameflow)

    def __init__(self, client: LeagueClient):
        super().__init__()
        self.__client = client
        self.__main_flag = threading.Event()

    def __wait_for_init(self):
        self.__client.wait_for_refresh_credentials()
        self.__client.wait_for_load_summoner_info()

    def __main(self):
        self.__wait_for_init()
        while not self.__main_flag.is_set():
            gameflow = self.__client.get_gameflow()
            try:
                logger.info(f"gameflow: {gameflow}")
                match gameflow:
                    case None:
                        self.gameflow_change.emit(Gameflow.LOADING)
                        self.__wait_for_init()

                    case "None":
                        self.gameflow_change.emit(Gameflow.NONE)

                    case "Lobby":
                        self.gameflow_change.emit(Gameflow.LOBBY)

                    case "Matchmaking":
                        self.gameflow_change.emit(Gameflow.MATCHMAKING)

                    case "ReadyCheck":
                        self.gameflow_change.emit(Gameflow.READY_CHECK)

                    case "ChampSelect":
                        self.gameflow_change.emit(Gameflow.CHAMP_SELECT)

                    case "InProgress":
                        self.gameflow_change.emit(Gameflow.IN_PROGRESS)

                    case "Reconnect":
                        self.gameflow_change.emit(Gameflow.RECONNECT)

                    case "PreEndOfGame":
                        self.gameflow_change.emit(Gameflow.PRE_END_OF_GAME)

                    case "EndOfGame":
                        self.gameflow_change.emit(Gameflow.END_OF_GAME)

                    case _:
                        raise UnknownGameflowStateError(gameflow)
            except Exception as e:
                logger.error(f"{e}")
                self.gameflow_change.emit(Gameflow.UNKNOWN)

            time.sleep(0.5)
        else:
            logger.info("停止程序")

    def start_main(self):
        self.__main_flag.clear()
        main_thread = threading.Thread(target=self.__main)
        main_thread.daemon = True
        main_thread.start()

    def stop_main(self) -> None:
        self.__main_flag.set()
