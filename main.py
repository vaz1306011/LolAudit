import logging
import sys

from PySide6.QtWidgets import QApplication

from lolaudit import setup_logging
from lolaudit.lol_audit_app import LolAuditApp

setup_logging()
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    lol_audit_app = LolAuditApp()
    lol_audit_app.start()

    sys.exit(app.exec())
