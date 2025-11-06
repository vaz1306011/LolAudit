import logging
from math import floor
from pprint import pformat

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from lolaudit.exceptions import (
    UnknownMatchmakingInfoError,
    UnknownPlayerResponseError,
    UnknownSearchStateError,
)
from lolaudit.lcu import LeagueClient
from lolaudit.models import Gameflow, MatchmakingState
from lolaudit.utils import web_socket

logger = logging.getLogger(__name__)


class MatchManager(QObject):
    matchmakingChange = Signal(MatchmakingState, object)
    __stopReadyCheckTimer = Signal()

    def __init__(self, client: LeagueClient) -> None:
        super().__init__()
        self.gameflow: Gameflow
        self.__client = client
        self.__client.websocketOnMessage.connect(self.inLobby)
        self.__client.websocketOnMessage.connect(self.inMatchmaking)
        self.__client.websocketOnMessage.connect(self.inReadyCheck)

        self.__auto_accept = True
        self.__accept_delay = 3
        self.__ready_check_timer: QTimer = QTimer()
        self.__ready_check_timer.setInterval(1000)
        self.__ready_check_timer.timeout.connect(self.__onReadyCheckTimerTick)
        self.__stopReadyCheckTimer.connect(self.__stop_ready_check_timer)
        self.__auto_rematch = True
        self.__auto_start_match = True

    def start(self) -> None:
        url = "/lol-matchmaking/v1/search"
        self.__client.subscribe(url)

    def stop(self) -> None:
        url = "/lol-matchmaking/v1/search"
        self.__client.unsubscribe(url)
        self.__stopReadyCheckTimer.emit()

    @web_socket.subscribe("/lol-matchmaking/v1/search")
    @Slot(dict)
    def inLobby(self, mchmking_info: dict) -> None:
        if self.gameflow != Gameflow.LOBBY or not mchmking_info:
            return
        search_state = mchmking_info.get("searchState")
        match search_state:
            case None | "Searching" | "Found":
                return
            case "Error":
                try:
                    if not mchmking_info["errors"]:
                        ptr = 0
                    elif mchmking_info["errors"][0]["penaltyTimeRemaining"] > 0:
                        ptr = mchmking_info["errors"][0]["penaltyTimeRemaining"]
                    else:
                        raise UnknownMatchmakingInfoError(mchmking_info)

                except Exception:
                    raise UnknownMatchmakingInfoError(mchmking_info)

                if ptr == 0 and self.__auto_start_match:
                    self.start_matchmaking()

                self.matchmakingChange.emit(MatchmakingState.PENALTY, ptr)
            case _:
                raise UnknownSearchStateError(search_state)

    @web_socket.subscribe("/lol-matchmaking/v1/search")
    @Slot(dict)
    def inMatchmaking(self, mchmking_info: dict) -> None:
        if self.gameflow != Gameflow.MATCHMAKING or not mchmking_info:
            return
        search_state = mchmking_info.get("searchState")
        match search_state:
            case "Searching":
                time_in_queue = floor(mchmking_info["timeInQueue"])
                estimated_time = floor(mchmking_info["estimatedQueueTime"])
                # estimated_time = 5

                if self.__auto_rematch and time_in_queue > estimated_time:
                    logger.info("等待時間過長，重新列隊")
                    self.stop_matchmaking()
                    self.start_matchmaking()

                self.matchmakingChange.emit(
                    MatchmakingState.MATCHING,
                    {"timeInQueue": time_in_queue, "estimatedTime": estimated_time},
                )

            case "Found":
                pass

            case _:
                logger.warning(f"未知的搜索狀態: {pformat(mchmking_info)}")
                raise UnknownSearchStateError(search_state)

    def __start_ready_check_timer(self) -> None:
        logger.debug("啟動準備接受對戰計時器")
        if self.__ready_check_timer.isActive():
            return
        self.__ready_check_timer.start()
        return

    def __stop_ready_check_timer(self) -> None:
        logger.debug("停止準備接受對戰計時器")
        if not self.__ready_check_timer.isActive():
            return
        self.__ready_check_timer.stop()
        return

    def __onReadyCheckTimerTick(self) -> None:
        ready_check = self.get_matchmaking_info().get("readyCheck", {})
        pass_time = int(ready_check.get("timer", -1))

        logger.debug(f"pass_time: {pass_time}\nready_check: {pformat(ready_check)}")

        if not self.__auto_accept:
            self.matchmakingChange.emit(
                MatchmakingState.WAITING_ACCEPT,
                {"pass_time": pass_time},
            )
            return

        self.matchmakingChange.emit(
            MatchmakingState.WAITING_ACCEPT,
            {
                "pass_time": pass_time,
                "accept_delay": self.__accept_delay,
            },
        )

        if pass_time >= self.__accept_delay:
            logger.debug("自動接受對戰")
            self.accept_match()

    # /lol-lobby/v2/lobby/matchmaking/search-state
    @web_socket.subscribe("/lol-matchmaking/v1/search")
    @Slot(dict)
    def inReadyCheck(self, mchmking_info: dict) -> None:
        if self.gameflow != Gameflow.READY_CHECK:
            return
        if not mchmking_info:
            mchmking_info = self.get_matchmaking_info()

        # logger.debug(pformat(mchmking_info))
        ready_check = mchmking_info.get("readyCheck", {})

        playerResponse = ready_check.get("playerResponse")
        state = ready_check.get("state")
        match playerResponse, state:
            case "None", "InProgress":
                if self.__ready_check_timer.isActive():
                    return
                self.__start_ready_check_timer()

            case ("None", "Invalid") | (None, _):
                pass

            case "Accepted", _:
                self.__stop_ready_check_timer()
                self.matchmakingChange.emit(MatchmakingState.ACCEPTED, None)

            case "Declined", _:
                self.__stop_ready_check_timer()
                self.matchmakingChange.emit(MatchmakingState.DECLINED, None)

            case _:
                self.__stop_ready_check_timer()
                raise UnknownPlayerResponseError(
                    f"{playerResponse}<{type(playerResponse)}>, {state}<{type(state)}>"
                )

    def get_accept_delay(self) -> int:
        return self.__accept_delay

    def set_accept_delay(self, delay: int) -> None:
        self.__accept_delay = delay

    def get_auto_accept(self) -> bool:
        return self.__auto_accept

    def set_auto_accept(self, status: bool) -> None:
        self.__auto_accept = status

    def get_auto_rematch(self) -> bool:
        return self.__auto_rematch

    def set_auto_rematch(self, status: bool) -> None:
        self.__auto_rematch = status

    def get_matchmaking_info(self) -> dict:
        url = "/lol-matchmaking/v1/search"
        return self.__client.get(url)

    def start_matchmaking(self) -> None:
        url = "/lol-lobby/v2/lobby/matchmaking/search"
        self.__client.post(url)

    def stop_matchmaking(self) -> None:
        url = "/lol-lobby/v2/lobby/matchmaking/search"
        self.__client.delete(url)

    def accept_match(self) -> None:
        url = "/lol-matchmaking/v1/ready-check/accept"
        self.__client.post(url)

    def decline_match(self) -> None:
        url = "/lol-matchmaking/v1/ready-check/decline"
        self.__client.post(url)
