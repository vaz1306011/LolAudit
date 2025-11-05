from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


class Tray(QSystemTrayIcon):
    def __init__(self, parent: QWidget, icon: QIcon) -> None:
        super().__init__(parent)
        self.__parent: QWidget = parent
        self.setIcon(icon)
        self.setToolTip("LOL Audit")

        self.__menu = QMenu()

        self.quit_action = self.__menu.addAction("退出")

        self.setContextMenu(self.__menu)
        self.activated.connect(self.on_click)

    def on_click(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.__parent.show()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            self.__menu.show()
