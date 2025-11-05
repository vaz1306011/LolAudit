import logging

from PySide6.QtCore import QObject, Signal, Slot

from lolaudit.config import ConfigManager
from lolaudit.lcu import ChampSelectManager, GameflowManager, LeagueClient, MatchManager
from lolaudit.models import ConfigKeys, Gameflow, MatchmakingState
from lolaudit.utils import web_socket

logger = logging.getLogger(__name__)


class MainController(QObject):
    uiUpdate = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()

        self.__client = LeagueClient()
        self.__client.websocketOnOpen.connect(self.__onWebsocketOpen)
        self.__client.websocketOnClose.connect(self.__onWebsocketClose)

        self.__gameflow_manager = GameflowManager(self.__client)
        self.__gameflow_manager.gameflowChange.connect(self.__onGameflowChange)
        self.__gameflow = None

        self.__match_manager = MatchManager(self.__client)
        self.__match_manager.matchmakingChange.connect(self.__onMatchmakingChange)

        self.__champ_select_manager = ChampSelectManager(self.__client)
        self.__champ_select_manager.remainingTimeChange.connect(
            self.__onChampSelectRemainingTimeChange
        )
        self.__champ_select_manager.champSelectFinish.connect(self.__onChampSelectEnd)

    @property
    def gameflow(self) -> Gameflow:
        self.__gameflow = getattr(
            self,
            f"_{self.__class__.__name__}__gameflow",
            self.__gameflow_manager.get_gameflow(),
        )
        return self.__gameflow

    @gameflow.setter
    def gameflow(self, value: Gameflow) -> None:
        self.__gameflow = value
        self.__match_manager.gameflow = value

    @Slot(Gameflow)
    def __onGameflowChange(self, gameflow: Gameflow) -> None:
        self.__updating_gameflow = getattr(
            self,
            f"_{self.__class__.__name__}__updating_gameflow",
            False,
        )
        if self.__updating_gameflow:
            return
        self.__updating_gameflow = True

        logger.info(f"Gameflow變更為: {gameflow}")
        self.gameflow = gameflow
        if self.__client.is_connection():
            match gameflow:
                case Gameflow.LOBBY | Gameflow.MATCHMAKING:
                    self.__match_manager.start()
                case Gameflow.READY_CHECK:
                    self.__client.websocketOnMessage.emit(
                        web_socket.format_url("/lol-matchmaking/v1/search"), {}
                    )
                case _:
                    self.__match_manager.stop()
            match gameflow:
                case Gameflow.CHAMP_SELECT:
                    self.__champ_select_manager.start()
                case _:
                    self.__champ_select_manager.stop()

        self.__updating_gameflow = False

        display_text = {
            Gameflow.LOADING: "讀取中",
            Gameflow.NONE: "未在房間內",
            Gameflow.LOBBY: "未在列隊中",
            Gameflow.GAME_START: "準備進入遊戲",
            Gameflow.IN_PROGRESS: "遊戲中",
            Gameflow.RECONNECT: "重新連接中",
            Gameflow.WAITING_FOR_STATS: "等待結算中",
            Gameflow.PRE_END_OF_GAME: "點讚畫面",
            Gameflow.END_OF_GAME: "結算畫面",
            Gameflow.UNKNOWN: "未知狀態",
        }.get(gameflow)

        if not display_text:
            return

        self.uiUpdate.emit(display_text)

    def __refresh_gameflow(self) -> None:
        self.__onGameflowChange(self.__gameflow_manager.get_gameflow())

    @Slot(MatchmakingState, dict)
    def __onMatchmakingChange(self, matchmaking_state: MatchmakingState, data) -> None:
        match matchmaking_state:
            case MatchmakingState.PENALTY:
                penalty_time: float = data
                minute, second = divmod(round(penalty_time), 60)
                if penalty_time == 0:
                    display_text = "未在列隊中"
                elif penalty_time > 0:
                    display_text = f"懲罰中，剩餘時間：{minute}:{second:02d}"

            case MatchmakingState.MATCHING:
                time_in_queue = data["timeInQueue"]
                estimated_time = data["estimatedTime"]
                tiqM, tiqS = divmod(time_in_queue, 60)
                etM, etS = divmod(estimated_time, 60)

                display_text = (
                    f"列隊中：{tiqM:02d}:{tiqS:02d}\n預計時間：{etM:02d}:{etS:02d}"
                )

            case MatchmakingState.WAITING_ACCEPT:
                if not isinstance(data, dict):
                    logger.warning(f"未知的等待接受對戰資料: {data}")
                pass_time = data.get("pass_time")
                accept_delay = data.get("accept_delay")
                if not accept_delay:
                    display_text = f"等待接受對戰 {pass_time}"
                else:
                    display_text = f"等待接受對戰 {pass_time}/{accept_delay}"

            case MatchmakingState.ACCEPTED:
                display_text = "已接受對戰"

            case MatchmakingState.DECLINED:
                display_text = "已拒絕對戰"

        self.uiUpdate.emit(display_text)

    def __onChampSelectRemainingTimeChange(self, remaining_time: float) -> None:
        display_text = f"選擇英雄中 - {round(remaining_time)}"
        self.uiUpdate.emit(display_text)

    def __onChampSelectEnd(self) -> None:
        self.__refresh_gameflow()

    def __onWebsocketOpen(self) -> None:
        self.__client.wait_for_load_summoner_info()
        self.__gameflow_manager.start()

    def __onWebsocketClose(self) -> None:
        self.start()

    def start_matchmaking(self) -> None:
        self.__match_manager.start_matchmaking()

    def stop_matchmaking(self) -> None:
        self.__match_manager.stop_matchmaking()

    def set_accept_delay(self, value: int) -> None:
        self.__match_manager.set_accept_delay(value)
        self.config.set_config(ConfigKeys.ACCEPT_DELAY, value)

    def set_auto_accept(self, value: bool) -> None:
        self.__match_manager.set_auto_accept(value)
        self.config.set_config(ConfigKeys.AUTO_ACCEPT, value)

    def set_auto_rematch(self, value: bool) -> None:
        self.__match_manager.set_auto_rematch(value)
        self.config.set_config(ConfigKeys.AUTO_REMATCH, value)

    def start(self) -> None:
        self.__onGameflowChange(Gameflow.LOADING)
        self.__client.start()
