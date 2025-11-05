import logging
from math import floor
from pprint import pformat
from typing import Optional

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
logger.setLevel(logging.DEBUG)


class MatchManager(QObject):
    matchmakingChange = Signal(MatchmakingState, object)

    def __init__(self, client: LeagueClient) -> None:
        super().__init__()
        self.gameflow: Gameflow
        self.__client = client
        self.__client.websocketOnMessage.connect(self.inLobby)
        self.__client.websocketOnMessage.connect(self.inMatchmaking)
        self.__client.websocketOnMessage.connect(self.inReadyCheck)

        self.__auto_accept = True
        self.__accept_delay = 3
        self.__ready_check_timer: Optional[QTimer] = None
        self.__auto_rematch = True
        self.__auto_start_match = True

    def start(self) -> None:
        url = "/lol-matchmaking/v1/search"
        self.__client.subscribe(url)

    def stop(self) -> None:
        url = "/lol-matchmaking/v1/search"
        self.__client.unsubscribe(url)

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

    @web_socket.subscribe("/lol-matchmaking/v1/search")
    @Slot(dict)
    def in_ready_check(self, mchmking_info: dict) -> None:
        if self.gameflow != Gameflow.READY_CHECK or not mchmking_info:
            return
        playerResponse = mchmking_info.get("readyCheck", {}).get("playerResponse")
        match playerResponse:
            case "None":
                if not self.__auto_accept:
                    return

                ready_check_data = self.get_matchmaking_info()["readyCheck"]
                if ready_check_data["state"] != "InProgress":
                    return
                pass_time = round(ready_check_data["timer"])

                def __is_playerResponsed() -> bool:
                    mchmking_info: dict = self.get_matchmaking_info()
                    playerResponse = mchmking_info.get("readyCheck", {}).get(
                        "playerResponse"
                    )
                    return playerResponse in ("Accepted", "Declined")

                if not __is_playerResponsed() and pass_time >= self.__accept_delay:
                    self.accept_match()
                    self.matchmaking_change.emit(MatchmakingState.ACCEPTED, None)
                    return

                self.matchmaking_change.emit(
                    MatchmakingState.WAITING_ACCEPT,
                    {"pass_time": pass_time, "accept_delay": self.__accept_delay},
                )

            case "Accepted":
                self.matchmaking_change.emit(MatchmakingState.ACCEPTED, None)

            case "Declined":
                self.matchmaking_change.emit(MatchmakingState.DECLINED, None)

            case _:
                raise UnknownPlayerResponseError(playerResponse)

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
