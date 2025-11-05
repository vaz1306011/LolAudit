import logging
import os
import sys

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication

from lolaudit import LolAuditUi, __version__, setup_logging

setup_logging()
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import tempfile

    app = QApplication(sys.argv)

    lock_file_path = os.path.join(tempfile.gettempdir(), "lol_audit.lock")
    lock_file = QLockFile(lock_file_path)
    if not lock_file.tryLock(100):
        logger.warning("Another instance is already running.")
        sys.exit(1)

    lol_audit_ui = LolAuditUi(__version__)
    lol_audit_ui.start()

    sys.exit(app.exec())
