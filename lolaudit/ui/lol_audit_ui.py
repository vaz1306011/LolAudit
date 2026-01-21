import logging
import platform

from PySide6.QtCore import Qt, QUrl, Signal, Slot
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices, QIcon
from PySide6.QtWidgets import QLineEdit, QMainWindow, QMessageBox

from lolaudit.config import ConfigManager
from lolaudit.models import ConfigKeys, Gameflow, UpdateInfo
from lolaudit.utils import resource_path

from .tray import Tray
from .ui import Ui_MainWindow

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LolAuditUi(QMainWindow, Ui_MainWindow):
    matchToggleRequested = Signal()
    exitRequested = Signal()

    showUpdateWindow = Signal(UpdateInfo)
    lableUpdated = Signal(str)
    gameflowChange = Signal(Gameflow)

    def __init__(self, version: str, config: ConfigManager) -> None:
        super().__init__()

        logger.info("開始初始化UI")
        self.__config = config
        self.setupUi(self)
        self.__setup_champ_select_actions()
        self.__setup_queue_mode_menu()
        self.setWindowTitle(f"LOL Audit {version}")
        icon_path = (
            "./assets/lol_audit.icns"
            if platform.system() == "Darwin"
            else "./assets/lol_audit.ico"
        )
        self.__icon = QIcon(resource_path(icon_path))
        self.setWindowIcon(self.__icon)
        self.setFixedSize(self.size())
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self.tray = Tray(self, self.__icon)

        self.__wire_signals()
        logger.info("UI 初始化完成")

    def start(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self.tray.show()
        self.read_config()

    def read_config(self) -> None:
        self.accept_delay_value: QLineEdit
        self.accept_delay_value.setText(
            str(self.__config.get_config(ConfigKeys.ACCEPT_DELAY))
        )
        always_on_top = bool(self.__config.get_config(ConfigKeys.ALWAYS_ON_TOP))
        self.always_on_top_status: QAction
        self.always_on_top_status.setChecked(always_on_top)
        self.__setAlwaysOnTop(always_on_top)

        auto_accept = bool(self.__config.get_config(ConfigKeys.AUTO_ACCEPT))
        self.auto_accept_status: QAction
        self.auto_accept_status.setChecked(auto_accept)

        auto_rematch = bool(self.__config.get_config(ConfigKeys.AUTO_REMATCH))
        self.auto_rematch_status: QAction
        self.auto_rematch_status.setChecked(auto_rematch)

        auto_lock_champion = bool(
            self.__config.get_config(ConfigKeys.AUTO_LOCK_CHAMPION)
        )
        self.auto_lock_status: QAction
        self.auto_lock_status.setChecked(auto_lock_champion)

        auto_ban_last = bool(self.__config.get_config(ConfigKeys.AUTO_BAN_LAST))
        self.auto_ban_last_status: QAction
        self.auto_ban_last_status.setChecked(auto_ban_last)

        queue_id = int(self.__config.get_config(ConfigKeys.ONE_KEY_QUEUE_ID))
        action = self.queue_mode_actions.get(queue_id)
        if action:
            action.setChecked(True)

    @Slot(UpdateInfo)
    def __onShowUpdateWindow(self, update_info: UpdateInfo) -> None:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("有新版本可用！")
        msg.setText(
            f"發現新版本: {update_info.latest}\n\n更新內容:\n{update_info.notes}"
        )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        msg.button(QMessageBox.StandardButton.Ok).setText("前往下載")
        ret = msg.exec()

        if ret == QMessageBox.StandardButton.Ok:
            QDesktopServices.openUrl(QUrl(update_info.url))

    @Slot(str)
    def __onLableUpdate(self, text: str) -> None:
        self.label.setText(text)

    @Slot(Gameflow)
    def __onChangeGameflow(self, gameflow: Gameflow) -> None:
        match gameflow:
            case Gameflow.LOBBY:
                self.match_button.setText("開始列隊")
                self.match_button.show()

            case Gameflow.MATCHMAKING:
                self.match_button.setText("停止列隊")
                self.match_button.show()

            case Gameflow.NONE:
                self.match_button.setText("一鍵列隊")
                self.match_button.show()

            case _:
                self.match_button.hide()

    def __onChangeSetting(self, key: ConfigKeys, value: object) -> None:
        self.__config.set_config(key, value)

    def __setAcceptDelay(self, text: str) -> None:
        try:
            value = int(text)
            if value < 0:
                raise ValueError
            self.__onChangeSetting(ConfigKeys.ACCEPT_DELAY, value)
        except ValueError:
            pass

    def __setAlwaysOnTop(self, value: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, value)
        self.show()
        self.__onChangeSetting(ConfigKeys.ALWAYS_ON_TOP, value)

    def __setAutoAccept(self, value) -> None:
        self.__onChangeSetting(ConfigKeys.AUTO_ACCEPT, value)

    def __setAutoRematch(self, value) -> None:
        self.__onChangeSetting(ConfigKeys.AUTO_REMATCH, value)

    def __setAutoLock(self, value) -> None:
        self.__onChangeSetting(ConfigKeys.AUTO_LOCK_CHAMPION, value)

    def __setAutoBanLast(self, value) -> None:
        self.__onChangeSetting(ConfigKeys.AUTO_BAN_LAST, value)

    def __onQueueModeSelected(self, action: QAction) -> None:
        queue_id = action.data()
        if queue_id is None:
            return
        self.__onChangeSetting(ConfigKeys.ONE_KEY_QUEUE_ID, int(queue_id))

    def __setup_champ_select_actions(self) -> None:
        self.auto_lock_status = QAction(self)
        self.auto_lock_status.setObjectName("auto_lock_status")
        self.auto_lock_status.setText("自動鎖角")
        self.menu.addAction(self.auto_lock_status)

        self.auto_ban_last_status = QAction(self)
        self.auto_ban_last_status.setObjectName("auto_ban_last_status")
        self.auto_ban_last_status.setText("自動選取禁用英雄")
        self.menu.addAction(self.auto_ban_last_status)

    def __setup_queue_mode_menu(self) -> None:
        self.queue_mode_menu = self.menu.addMenu("一鍵列隊模式")
        self.queue_mode_actions = {}
        self.queue_mode_group = QActionGroup(self)
        self.queue_mode_group.setExclusive(True)
        self.queue_mode_group.triggered.connect(self.__onQueueModeSelected)
        modes = [
            ("競技模式", 400),
            ("單雙", 420),
            ("彈性積分", 440),
            ("隨機單中", 450),
        ]
        for label, queue_id in modes:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setData(queue_id)
            self.queue_mode_group.addAction(action)
            self.queue_mode_menu.addAction(action)
            self.queue_mode_actions[queue_id] = action

    def __wire_signals(self):
        # UI物件
        self.tray.quit_action.triggered.connect(self.exitRequested.emit)
        self.match_button.clicked.connect(self.matchToggleRequested.emit)

        self.accept_delay_value.textChanged.connect(self.__setAcceptDelay)

        self.always_on_top_status.triggered.connect(self.__setAlwaysOnTop)
        self.always_on_top_status.setCheckable(True)

        self.auto_accept_status.triggered.connect(self.__setAutoAccept)
        self.auto_accept_status.setCheckable(True)

        self.auto_rematch_status.triggered.connect(self.__setAutoRematch)
        self.auto_rematch_status.setCheckable(True)

        self.auto_lock_status.triggered.connect(self.__setAutoLock)
        self.auto_lock_status.setCheckable(True)

        self.auto_ban_last_status.triggered.connect(self.__setAutoBanLast)
        self.auto_ban_last_status.setCheckable(True)

        # 其他信號
        self.showUpdateWindow.connect(self.__onShowUpdateWindow)
        self.lableUpdated.connect(self.__onLableUpdate)
        self.gameflowChange.connect(self.__onChangeGameflow)

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
