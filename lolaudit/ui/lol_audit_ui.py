import logging
import platform

from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from lolaudit.config import ConfigKeys
from lolaudit.core import MainController
from lolaudit.models import Gameflow
from lolaudit.ui import Tray, Ui_MainWindow
from lolaudit.utils import check_update, resource_path

logger = logging.getLogger(__name__)


class LolAuditUi(QMainWindow, Ui_MainWindow):
    def __init__(self, version):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(f"LOL Audit {version}")
        icon_path = (
            "./lol_audit.icns" if platform.system() == "Darwin" else "./lol_audit.ico"
        )
        self.__icon = QIcon(resource_path(icon_path))
        self.setWindowIcon(self.__icon)
        self.setFixedSize(self.size())
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        logger.info("初始化主控制器")
        self.__main_controller = MainController()
        self.__main_controller.ui_update.connect(self.__on_ui_update)
        self.__main_controller.start()
        logger.info("主控制器初始化完成")

        self.__init_ui()
        logger.info("UI 初始化完成")

        self.__check_update(version)

        self.gameflow: Gameflow

    def __init_ui(self):
        cfg = self.__main_controller.config
        self.accept_delay_value.setText(str(cfg.get_config(ConfigKeys.ACCEPT_DELAY)))
        self.accept_delay_value.textChanged.connect(
            self.__main_controller.set_accept_delay
        )

        self.match_button.clicked.connect(self.__on_match_button_click)

        for key, widget, func in [
            (
                ConfigKeys.ALWAYS_ON_TOP,
                self.always_on_top_status,
                self.__set_always_on_top,
            ),
            (
                ConfigKeys.AUTO_ACCEPT,
                self.auto_accept_status,
                self.__main_controller.set_auto_accept,
            ),
            (
                ConfigKeys.AUTO_REMATCH,
                self.auto_rematch_status,
                self.__main_controller.set_auto_rematch,
            ),
        ]:
            status = bool(cfg.get_config(key))
            widget.setCheckable(True)
            widget.setChecked(status)
            widget.triggered.connect(func)
            if key == ConfigKeys.ALWAYS_ON_TOP:
                self.__set_always_on_top(status)

        self.tray = Tray(self, self.__icon)
        self.tray.quit_action.triggered.connect(self.__exit_app)
        self.tray.show()

    @Slot(Gameflow, str)
    def __on_ui_update(self, gameflow: Gameflow, text: str):
        self.gameflow = gameflow
        self.label.setText(text)

        match gameflow:
            case Gameflow.LOBBY:
                self.match_button.setText("開始列隊")
                self.match_button.setDisabled(False)
                self.match_button.show()

            case Gameflow.MATCHMAKING:
                self.match_button.setText("停止列隊")
                self.match_button.setDisabled(False)
                self.match_button.show()

            case _:
                self.match_button.setDisabled(True)
                self.match_button.hide()

    def __on_match_button_click(self):
        if self.gameflow == Gameflow.LOBBY:
            self.__main_controller.start_matchmaking()
        else:
            self.__main_controller.stop_matchmaking()

    def __set_always_on_top(self, status: bool):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, status)
        self.show()
        self.__main_controller.config.set_config(ConfigKeys.ALWAYS_ON_TOP, status)

    def __check_update(self, version):
        result = check_update(version)
        if not result.has_update:
            logger.info("已是最新版本")
            return

        latest = result.latest
        url = result.url
        notes = result.notes or ""
        logger.info(f"發現新版本: {latest}")

        msg = QMessageBox(self)
        msg.setWindowTitle("有新版本可用")
        msg.setText(f"檢測到新版本：{latest}\n\n是否前往下載？")
        msg.setInformativeText(notes)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(url))

    def __exit_app(self):
        self.__main_controller.stop()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
