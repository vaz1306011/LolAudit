import logging
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from lolaudit.models import ConfigKeys
from lolaudit.utils import web_socket

if TYPE_CHECKING:
    from lolaudit.config import ConfigManager

    from . import LeagueClient

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class ChampSelectManager(QObject):
    remainingTimeChange = Signal(int)
    champSelectFinish = Signal()
    __auto_lock_threshold = -2

    def __init__(self, client: "LeagueClient", config: "ConfigManager") -> None:
        super().__init__()
        self.__client = client
        self.__config = config
        self.__client.websocketOnMessage.connect(self.__onChampSelectSessionChange)
        self.__session: dict
        self.__timer = None
        self.__auto_locked_action_ids: set[int] = set()
        self.__auto_banned_action_ids: set[int] = set()

    def __get_champ_select_session(self) -> dict:
        url = "/lol-champ-select/v1/session"
        return self.__client.get(url)

    @web_socket.subscribe("/lol-champ-select/v1/session")
    @Slot(dict)
    def __onChampSelectSessionChange(self, session: dict) -> None:
        self.__session = session
        self.__update_last_ban(session)

    def __onTimerTimeout(self) -> None:
        if not self.__session:
            return
        timer = self.__session.get("timer", {})
        adjusted_time_left = timer.get("adjustedTimeLeftInPhase")
        internal_now = timer.get("internalNowInEpochMs")
        if adjusted_time_left is None or internal_now is None:
            return
        adjustedTimeLeftInPhase = adjusted_time_left / 1000
        internalNowInEpochMs = internal_now / 1000
        remaining_time = (adjustedTimeLeftInPhase + internalNowInEpochMs) - time.time()
        self.remainingTimeChange.emit(remaining_time)
        self.__try_auto_lock(remaining_time)
        self.__try_auto_ban()

    def __update_last_ban(self, session: dict) -> None:
        local_cell_id = session.get("localPlayerCellId")
        if local_cell_id is None:
            return
        actions = session.get("actions", [])
        last_ban_champion_id = self.__config.get_config(ConfigKeys.LAST_BAN_CHAMPION_ID)
        for action_group in actions:
            for action in action_group:
                if action.get("actorCellId") != local_cell_id:
                    continue
                if action.get("type") != "ban":
                    continue
                if not action.get("completed"):
                    continue
                champion_id = action.get("championId") or 0
                if champion_id <= 0 or champion_id == last_ban_champion_id:
                    continue
                self.__config.set_config(ConfigKeys.LAST_BAN_CHAMPION_ID, champion_id)
                return

    def __try_auto_lock(self, remaining_time: float) -> None:
        if not bool(self.__config.get_config(ConfigKeys.AUTO_LOCK_CHAMPION)):
            return
        if remaining_time > self.__auto_lock_threshold:
            return
        session = self.__session or {}
        local_cell_id = session.get("localPlayerCellId")
        if local_cell_id is None:
            return
        actions = session.get("actions", [])
        for action_group in actions:
            for action in action_group:
                if action.get("actorCellId") != local_cell_id:
                    continue
                if action.get("type") != "pick":
                    continue
                if not action.get("isInProgress", False):
                    continue
                if action.get("completed"):
                    return
                action_id = action.get("id")
                if action_id is None or action_id in self.__auto_locked_action_ids:
                    return
                champion_id = action.get("championId") or 0
                if champion_id <= 0:
                    return
                logger.info("選角時間到，自動鎖角")
                url = f"/lol-champ-select/v1/session/actions/{action_id}"
                self.__client.patch(
                    url,
                    {"championId": champion_id, "completed": True},
                )
                self.__auto_locked_action_ids.add(action_id)
                return

    def __try_auto_ban(self) -> None:
        if not bool(self.__config.get_config(ConfigKeys.AUTO_BAN_LAST)):
            return
        session = self.__session or {}
        timer_phase = session.get("timer", {}).get("phase")
        session_phase = session.get("phase")
        if timer_phase != "BAN_PICK" and session_phase != "BAN_PICK":
            return
        local_cell_id = session.get("localPlayerCellId")
        if local_cell_id is None:
            return
        last_ban_champion_id = self.__config.get_config(ConfigKeys.LAST_BAN_CHAMPION_ID)
        if not last_ban_champion_id:
            return
        actions = session.get("actions", [])
        for action_group in actions:
            for action in action_group:
                if action.get("actorCellId") != local_cell_id:
                    continue
                if action.get("type") != "ban":
                    continue
                if not action.get("isInProgress", False):
                    continue
                if action.get("completed"):
                    return
                if (action.get("championId") or 0) > 0:
                    return
                action_id = action.get("id")
                if action_id is None or action_id in self.__auto_banned_action_ids:
                    return
                logger.info("選取禁用英雄")
                url = f"/lol-champ-select/v1/session/actions/{action_id}"
                self.__client.patch(url, {"championId": last_ban_champion_id})
                self.__auto_banned_action_ids.add(action_id)
                return

    def start(self) -> None:
        logger.debug("開始選角監聽")
        url = "/lol-champ-select/v1/session"
        self.__client.subscribe(url)
        self.__session = self.__get_champ_select_session()

        self.__timer = QTimer()
        self.__timer.setInterval(250)
        self.__timer.timeout.connect(self.__onTimerTimeout)
        self.__timer.start()

    def get_champ_select_actions(self) -> list:
        """
        types = [[ban, ...], [ten_bans_reveal], [pick, pick], ...]
        """
        session = self.__get_champ_select_session()
        actions = session.get("actions", [])
        return actions

    def stop(self) -> None:
        logger.debug("結束選角監聽")
        url = "/lol-champ-select/v1/session"
        self.__client.unsubscribe(url)
        self.__timer = None
        self.__auto_locked_action_ids.clear()
        self.__auto_banned_action_ids.clear()
        self.champSelectFinish.emit()
