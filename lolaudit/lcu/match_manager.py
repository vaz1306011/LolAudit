import logging
from math import floor
from pprint import pformat

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from lolaudit.config import ConfigManager
from lolaudit.exceptions import (
    UnknownMatchmakingInfoError,
    UnknownPlayerResponseError,
    UnknownSearchStateError,
)
from lolaudit.models import Gameflow, MatchmakingState
from lolaudit.models.entities.response.matchmaking_info import MatchmakingInfo
from lolaudit.models.enums.config_keys import ConfigKeys
from lolaudit.utils import web_socket

from .league_client import LeagueClient

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class MatchManager(QObject):
    matchmakingChange = Signal(MatchmakingState, object)
    __stopReadyCheckTimer = Signal()
    __default_queue_id = 420

    def __init__(self, client: LeagueClient, config: ConfigManager) -> None:
        super().__init__()
        self.gameflow: Gameflow
        self.__client = client
        self.__client.websocketOnMessage.connect(self.inLobby)
        self.__client.websocketOnMessage.connect(self.inMatchmaking)
        self.__client.websocketOnMessage.connect(self.inReadyCheck)
        self.__config = config

        self.__ready_check_timer: QTimer = QTimer()
        self.__ready_check_timer.setInterval(1000)
        self.__ready_check_timer.timeout.connect(self.__onReadyCheckTimerTick)
        self.__stopReadyCheckTimer.connect(self.__stop_ready_check_timer)

    @property
    def accept_delay(self) -> int:
        return self.__config.get_config(ConfigKeys.ACCEPT_DELAY)

    @property
    def auto_accept(self) -> bool:
        return bool(self.__config.get_config(ConfigKeys.AUTO_ACCEPT))

    @property
    def auto_rematch(self) -> bool:
        return bool(self.__config.get_config(ConfigKeys.AUTO_REMATCH))

    @property
    def auto_start_match(self) -> bool:
        return bool(self.__config.get_config(ConfigKeys.AUTO_START_MATCH))

    def start(self) -> None:
        url = "/lol-matchmaking/v1/search"
        self.__client.subscribe(url)

    def stop(self) -> None:
        url = "/lol-matchmaking/v1/search"
        self.__client.unsubscribe(url)
        self.__stopReadyCheckTimer.emit()

    def get_matchmaking_info(self) -> dict:
        url = "/lol-matchmaking/v1/search"
        return self.__client.get(url)

    def start_matchmaking(self) -> None:
        url = "/lol-lobby/v2/lobby/matchmaking/search"
        self.__client.post(url)

    def stop_matchmaking(self) -> None:
        url = "/lol-lobby/v2/lobby/matchmaking/search"
        self.__client.delete(url)

    def create_lobby(self, queue_id: int | None = None) -> None:
        url = "/lol-lobby/v2/lobby"
        self.__client.post(url, {"queueId": queue_id or self.__default_queue_id})

    def accept_match(self) -> None:
        url = "/lol-matchmaking/v1/ready-check/accept"
        self.__client.post(url)

    def decline_match(self) -> None:
        url = "/lol-matchmaking/v1/ready-check/decline"
        self.__client.post(url)

    @web_socket.subscribe("/lol-matchmaking/v1/search")
    @Slot(dict)
    def inLobby(self, mchmking_info_dict: dict) -> None:
        if self.gameflow != Gameflow.LOBBY or not mchmking_info_dict:
            return
        mchmking_info = MatchmakingInfo(**mchmking_info_dict)
        search_state = mchmking_info.searchState
        logger.debug(f"搜索狀態: {pformat(mchmking_info.model_dump())}")
        match search_state:
            case "Error":
                try:
                    if not mchmking_info.errors:
                        ptr = 0
                    elif mchmking_info.errors[0].penaltyTimeRemaining > 0:
                        ptr = mchmking_info.errors[0].penaltyTimeRemaining
                    else:
                        raise UnknownMatchmakingInfoError(mchmking_info)

                except Exception:
                    raise UnknownMatchmakingInfoError(mchmking_info)

                if ptr == 0 and self.auto_start_match:
                    self.start_matchmaking()

                self.matchmakingChange.emit(MatchmakingState.PENALTY, ptr)
            case None | "Searching" | "Found":
                pass
            case _:
                raise UnknownSearchStateError(search_state)

    @web_socket.subscribe("/lol-matchmaking/v1/search")
    @Slot(dict)
    def inMatchmaking(self, mchmking_info_dict: dict) -> None:
        if self.gameflow != Gameflow.MATCHMAKING or not mchmking_info_dict:
            return
        matchmaking_info = MatchmakingInfo(**mchmking_info_dict)
        search_state = matchmaking_info.searchState
        match search_state:
            case "Searching":
                time_in_queue = floor(matchmaking_info.timeInQueue)
                estimated_time = floor(matchmaking_info.estimatedQueueTime)
                # estimated_time = 5

                if (
                    self.auto_rematch
                    and time_in_queue > estimated_time
                    and self.__is_lobby_leader()
                ):
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
                logger.warning(
                    f"未知的搜索狀態: {pformat(matchmaking_info.model_dump()) }"
                )
                raise UnknownSearchStateError(search_state)

    # /lol-lobby/v2/lobby/matchmaking/search-state
    @web_socket.subscribe("/lol-matchmaking/v1/search")
    @Slot(dict)
    def inReadyCheck(self, mchmking_info_dict: dict) -> None:
        if self.gameflow != Gameflow.READY_CHECK:
            return
        if not mchmking_info_dict:
            mchmking_info_dict = self.get_matchmaking_info()

        mchmking_info = MatchmakingInfo(**mchmking_info_dict)

        logger.debug(pformat(mchmking_info.model_dump()))
        ready_check = mchmking_info.readyCheck

        playerResponse = ready_check.playerResponse
        state = ready_check.state
        match playerResponse, state:
            case "None", "InProgress":
                self.__start_ready_check_timer()

            case "Accepted", _:
                self.__stop_ready_check_timer()
                self.matchmakingChange.emit(MatchmakingState.ACCEPTED, None)

            case "Declined", _:
                self.__stop_ready_check_timer()
                self.matchmakingChange.emit(MatchmakingState.DECLINED, None)

            case ("None", "Invalid") | (None, _):
                pass

            case _:
                self.__stop_ready_check_timer()
                raise UnknownPlayerResponseError(
                    f"{playerResponse}<{type(playerResponse)}>, {state}<{type(state)}>"
                )

    def __start_ready_check_timer(self) -> None:
        if self.__ready_check_timer.isActive():
            return
        logger.debug("啟動準備接受對戰計時器")
        self.__ready_check_timer.start()

    def __stop_ready_check_timer(self) -> None:
        if not self.__ready_check_timer.isActive():
            return
        logger.debug("停止準備接受對戰計時器")
        self.__ready_check_timer.stop()

    def __onReadyCheckTimerTick(self) -> None:
        ready_check = self.get_matchmaking_info().get("readyCheck", {})
        pass_time = int(ready_check.get("timer", -1)) + 1

        logger.debug(f"pass_time: {pass_time}\nready_check: {pformat(ready_check)}")

        if not self.auto_accept:
            self.matchmakingChange.emit(
                MatchmakingState.WAITING_ACCEPT,
                {"pass_time": pass_time},
            )

        self.matchmakingChange.emit(
            MatchmakingState.WAITING_ACCEPT,
            {"pass_time": pass_time, "accept_delay": self.accept_delay},
        )

        if pass_time >= self.accept_delay:
            logger.debug("自動接受對戰")
            self.accept_match()

    def __is_lobby_leader(self) -> bool:
        lobby = self.__client.get("/lol-lobby/v2/lobby") or {}
        local_member = lobby.get("localMember", {})
        is_leader = local_member.get("isLeader")
        if is_leader is not None:
            return bool(is_leader)
        return False
