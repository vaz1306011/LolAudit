import logging
import os
import sys
import tempfile

from PySide6.QtCore import QLockFile, QThread
from PySide6.QtWidgets import QApplication

from lolaudit import __version__
from lolaudit.config.config_manager import ConfigManager
from lolaudit.core import MainController
from lolaudit.models.enums.gameflow import Gameflow
from lolaudit.ui import LolAuditUi
from lolaudit.utils.update_checker import check_update

logger = logging.getLogger(__name__)


class LolAuditApp:
    def __init__(self):
        self._config = ConfigManager()
        self.version = __version__
        self._gameflow: Gameflow = Gameflow.LOADING

        self.__thread = QThread()
        self.__ui = LolAuditUi(self.version, self._config)
        self.__main_controller = MainController(self._config)
        self.__main_controller.moveToThread(self.__thread)
        self.__thread.started.connect(self.__main_controller.start)

        self.__wire_signals()

    def start(self):
        self.__setup_lock_file()
        self._config.load_config()
        self.__ui.start()
        self.__thread.start()
        self.check_update(self.version)

    def stop(self):
        self.__main_controller.stop()
        self.__thread.quit()
        self.__thread.wait()
        QApplication.quit()

    def check_update(self, version: str):
        result = check_update(version)
        if result.has_update:
            logger.info(f"發現新版本: {result.latest}")
            self.__ui.showUpdateWindow.emit(result)
        else:
            logger.info("已是最新版本")

    def __wire_signals(self):
        self.__ui.exitRequested.connect(self.stop)
        self.__ui.matchToggleRequested.connect(self.__main_controller.match_toggle)
        self.__main_controller.gameflowChange.connect(self.__ui.gameflowChange)
        self.__main_controller.labelEditRequest.connect(self.__ui.lableUpdated)

    def __setup_lock_file(self):
        lock_file_path = os.path.join(tempfile.gettempdir(), "lol_audit.lock")
        self.__lock_file = QLockFile(lock_file_path)
        if not self.__lock_file.tryLock(100):
            logger.warning("Another instance is already running.")
            sys.exit(1)
