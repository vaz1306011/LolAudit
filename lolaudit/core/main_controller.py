import logging

from PySide6.QtCore import QObject, Signal, Slot

from lolaudit.config import ConfigManager
from lolaudit.lcu import ChampSelectManager, GameflowManager, LeagueClient, MatchManager
from lolaudit.models import ConfigKeys, Gameflow, MatchmakingState

logger = logging.getLogger(__name__)


class MainController(QObject):
    ui_update = Signal(str)

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()

        self.__client = LeagueClient()
        self.__client.websocket_on_open.connect(self.__on_websocket_open)
        self.__client.websocket_on_close.connect(self.__on_websocket_close)

        self.__gameflow_manager = GameflowManager(self.__client)
        self.__gameflow_manager.gameflow_change.connect(self.__on_gameflow_change)
        self.__gameflow = None

        self.__match_manager = MatchManager(self.__client)
        self.__match_manager.matchmaking_change.connect(self.__on_matchmaking_change)

        self.__champ_select_manager = ChampSelectManager(self.__client)
        self.__champ_select_manager.remaining_time_change.connect(
            self.__on_champ_select_remaining_time_change
        )
        self.__champ_select_manager.end.connect(self.__on_champ_select_end)

    @property
    def gameflow(self) -> Gameflow:
        self.__gameflow = self.__gameflow_manager.get_gameflow()
        return self.__gameflow

    @gameflow.setter
    def gameflow(self, value: Gameflow):
        self.__gameflow = value
        self.__match_manager.gameflow = value

    @Slot(Gameflow)
    def __on_gameflow_change(self, gameflow: Gameflow):
        self._gameflow_handle = getattr(self, "_gameflow_handle", False)
        if self._gameflow_handle:
            return
        self._gameflow_handle = True

        logger.info(f"Gameflow變更為: {gameflow}")
        self.gameflow = gameflow
        if self.__client.is_connection():
            match gameflow:
                case Gameflow.LOBBY | Gameflow.MATCHMAKING | Gameflow.READY_CHECK:
                    self.__match_manager.start()
                case _:
                    self.__match_manager.stop()
            match gameflow:
                case Gameflow.CHAMP_SELECT:
                    self.__champ_select_manager.start()
                case _:
                    self.__champ_select_manager.stop()

        self._gameflow_handle = False

        display_text = None
        match gameflow:
            case Gameflow.LOADING:
                display_text = "讀取中"

            case Gameflow.NONE:
                display_text = "未在房間內"

            case Gameflow.LOBBY:
                display_text = "未在列隊中"

            case Gameflow.MATCHMAKING:
                pass

            case Gameflow.READY_CHECK:
                pass

            case Gameflow.CHAMP_SELECT:
                pass

            case Gameflow.IN_PROGRESS:
                display_text = "遊戲中"

            case Gameflow.RECONNECT:
                display_text = "重新連接中"

            case Gameflow.PRE_END_OF_GAME:
                display_text = "點讚畫面"

            case Gameflow.END_OF_GAME:
                display_text = "結算畫面"

            case Gameflow.UNKNOWN:
                display_text = "未知狀態"

        if not display_text:
            return

        self.ui_update.emit(display_text)

    def __refresh_gameflow(self):
        self.__on_gameflow_change(self.gameflow)

    @Slot(MatchmakingState, dict)
    def __on_matchmaking_change(self, matchmaking_state: MatchmakingState, data):
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
                pass_time = data["pass_time"]
                accept_delay = data["accept_delay"]
                display_text = f"等待接受對戰 {pass_time}/{accept_delay}"

            case MatchmakingState.ACCEPTED:
                display_text = "已接受對戰"

            case MatchmakingState.DECLINED:
                display_text = "已拒絕對戰"

        self.ui_update.emit(display_text)

    def __on_champ_select_remaining_time_change(self, remaining_time: float):
        display_text = f"選擇英雄中 - {round(remaining_time)}"
        self.ui_update.emit(display_text)

    def __on_champ_select_end(self):
        self.__refresh_gameflow()

    def __on_websocket_open(self):
        self.__client.wait_for_load_summoner_info()
        self.__gameflow_manager.start()

    def __on_websocket_close(self):
        self.start()

    def start_matchmaking(self):
        self.__match_manager.start_matchmaking()

    def stop_matchmaking(self):
        self.__match_manager.stop_matchmaking()

    def set_accept_delay(self, value: int):
        self.__match_manager.set_accept_delay(value)
        self.config.set_config(ConfigKeys.ACCEPT_DELAY, value)

    def set_auto_accept(self, value: bool):
        self.__match_manager.set_auto_accept(value)
        self.config.set_config(ConfigKeys.AUTO_ACCEPT, value)

    def set_auto_rematch(self, value: bool):
        self.__match_manager.set_auto_rematch(value)
        self.config.set_config(ConfigKeys.AUTO_REMATCH, value)

    def start(self):
        self.__on_gameflow_change(Gameflow.LOADING)
        self.__client.start()
