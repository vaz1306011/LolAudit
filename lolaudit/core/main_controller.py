import logging

from PySide6.QtCore import QObject, QThread, Signal, Slot

from lolaudit.config import ConfigManager
from lolaudit.lcu import ChampSelectManager, GameflowManager, LeagueClient, MatchManager
from lolaudit.models import ConfigKeys, Gameflow, MatchmakingState

logger = logging.getLogger(__name__)


class MainController(QObject):
    ui_update = Signal(Gameflow, str)

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.__client = LeagueClient()
        self.__client.wait_for_connect()
        self.__gameflow_manager = GameflowManager(self.__client)
        self.__gameflow_manager.on_gameflow_change.connect(self.__on_gameflow_change)
        self.__match_manager = MatchManager(self.__client)
        self.__champ_select_manager = ChampSelectManager(self.__client)
        self.__work_thread = None

    @Slot(Gameflow)
    def __on_gameflow_change(self, gameflow: Gameflow):
        display_text = None
        match gameflow:
            case Gameflow.LOADING:
                display_text = "讀取中"

            case Gameflow.NONE:
                display_text = "未在房間內"

            case Gameflow.LOBBY:
                penalty_time = self.__match_manager.in_lobby()
                minute, second = divmod(round(penalty_time), 60)
                if penalty_time == 0:
                    display_text = "未在列隊中"
                elif penalty_time > 0:
                    display_text = f"懲罰中，剩餘時間：{minute}:{second:02d}"

            case Gameflow.MATCHMAKING:
                data = self.__match_manager.in_matchmaking()
                try:
                    time_in_queue = data["timeInQueue"]
                    estimated_time = data["estimatedTime"]
                except Exception as e:
                    display_text = f"匹配時間獲取失敗: {e}\ndata:{data}"

                tiqM, tiqS = divmod(time_in_queue, 60)
                etM, etS = divmod(estimated_time, 60)

                display_text = (
                    f"列隊中：{tiqM:02d}:{tiqS:02d}\n預計時間：{etM:02d}:{etS:02d}"
                )

            case Gameflow.READY_CHECK:
                state, data = self.__match_manager.in_ready_check()
                match state:
                    case MatchmakingState.NONE:
                        display_text = "等待接受"

                    case MatchmakingState.WAITING_ACCEPT:
                        pass_time = data["pass_time"]
                        accept_delay = data["accept_delay"]
                        display_text = f"等待接受對戰 {pass_time}/{accept_delay}"

                    case MatchmakingState.ACCEPTED:
                        display_text = "已接受對戰"

                    case MatchmakingState.DECLINED:
                        display_text = "已拒絕對戰"

            case Gameflow.CHAMP_SELECT:
                remaining_time = (
                    self.__champ_select_manager.get_champ_select_remaining_time()
                )
                display_text = f"選擇英雄中 - {round(remaining_time)}"

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

        self.ui_update.emit(gameflow, display_text)

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
        logger.info("啟動主控制器工作線程")
        if self.__work_thread:
            logger.warning("主控制器工作線程已啟動，無法重複啟動")
            return

        self.__work_thread = QThread()
        self.moveToThread(self.__work_thread)
        self.__work_thread.started.connect(self.__gameflow_manager.start)
        self.__work_thread.start()
        logger.info("主控制器工作線程啟動完成")

    def stop(self):
        pass
        if not self.__work_thread:
            logger.warning("主控制器工作線程未啟動")
            return

        self.__client.stop_websocket()
        self.__work_thread.quit()
        self.__work_thread.wait()
