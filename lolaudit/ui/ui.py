# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QMainWindow,
    QMenu, QMenuBar, QPushButton, QSizePolicy,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(360, 250)
        MainWindow.setStyleSheet(u"*{\n"
"	color:#FFFFFF;\n"
"}\n"
"#MainWindow{\n"
"	background-color:#121212;\n"
"}\n"
"\n"
"QLineEdit{\n"
"	background-color:#222322;\n"
"	border:0;\n"
"}\n"
"\n"
"QPushButton{\n"
"	background-color: #2C2C2C;\n"
"}\n"
"QPushButton:hover{\n"
"	background-color: #3C3C3C;\n"
"}\n"
"QPushButton:pressed{\n"
"	 background-color: #1A1A1A;\n"
"}")
        self.auto_accept_status = QAction(MainWindow)
        self.auto_accept_status.setObjectName(u"auto_accept_status")
        self.auto_rematch_status = QAction(MainWindow)
        self.auto_rematch_status.setObjectName(u"auto_rematch_status")
        self.always_on_top_status = QAction(MainWindow)
        self.always_on_top_status.setObjectName(u"always_on_top_status")
        self.auto_lock_status = QAction(MainWindow)
        self.auto_lock_status.setObjectName(u"auto_lock_status")
        self.auto_ban_last_status = QAction(MainWindow)
        self.auto_ban_last_status.setObjectName(u"auto_ban_last_status")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 120, 341, 91))
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(14)
        self.label.setFont(font)
        self.label.setTextFormat(Qt.PlainText)
        self.label.setAlignment(Qt.AlignCenter)
        self.match_button = QPushButton(self.centralwidget)
        self.match_button.setObjectName(u"match_button")
        self.match_button.setGeometry(QRect(105, 65, 150, 50))
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(12)
        self.match_button.setFont(font1)
        self.accept_delay_value = QLineEdit(self.centralwidget)
        self.accept_delay_value.setObjectName(u"accept_delay_value")
        self.accept_delay_value.setGeometry(QRect(125, 20, 110, 20))
        self.accept_delay_value.setAlignment(Qt.AlignCenter)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 360, 25))
        self.menubar.setStyleSheet(u"*{\n"
"	background-color:#121212;\n"
"}\n"
"QMenuBar::item:selected{\n"
"	background-color: #3C3C3C;\n"
"}\n"
"\n"
"QMenu:selected{\n"
"	 background-color:#2f2c2c;\n"
"}\n"
"\n"
"QAciotn{\n"
"	 background-color:#2f2c2c;\n"
"}\n"
"")
        self.options_menu = QMenu(self.menubar)
        self.options_menu.setObjectName(u"options_menu")
        self.options_menu.setStyleSheet(u"")
        self.queue_menu = QMenu(self.menubar)
        self.queue_menu.setObjectName(u"queue_menu")
        self.queue_mode_menu = QMenu(self.menubar)
        self.queue_mode_menu.setObjectName(u"queue_mode_menu")
        self.champ_select_menu = QMenu(self.menubar)
        self.champ_select_menu.setObjectName(u"champ_select_menu")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.options_menu.menuAction())
        self.menubar.addAction(self.queue_menu.menuAction())
        self.menubar.addAction(self.champ_select_menu.menuAction())
        self.options_menu.addAction(self.always_on_top_status)
        self.queue_menu.addAction(self.queue_mode_menu.menuAction())
        self.queue_menu.addAction(self.auto_rematch_status)
        self.queue_menu.addAction(self.auto_accept_status)
        self.champ_select_menu.addAction(self.auto_ban_last_status)
        self.champ_select_menu.addAction(self.auto_lock_status)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        self.auto_accept_status.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52d5\u63a5\u53d7", None))
        self.auto_rematch_status.setText(QCoreApplication.translate("MainWindow", u"\u8d85\u6642\u91cd\u6392", None))
        self.always_on_top_status.setText(QCoreApplication.translate("MainWindow", u"\u8996\u7a97\u81f3\u9802", None))
        self.auto_lock_status.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52d5\u9396\u89d2", None))
        self.auto_ban_last_status.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52d5\u9078\u53d6\u7981\u7528\u82f1\u96c4", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u672a\u5728\u5217\u968a", None))
        self.match_button.setText(QCoreApplication.translate("MainWindow", u"\u958b\u59cb\u5217\u968a", None))
        self.options_menu.setTitle(QCoreApplication.translate("MainWindow", u"\u9078\u9805", None))
        self.queue_menu.setTitle(QCoreApplication.translate("MainWindow", u"\u5217\u968a", None))
        self.queue_mode_menu.setTitle(QCoreApplication.translate("MainWindow", u"\u4e00\u9375\u5217\u968a\u6a21\u5f0f", None))
        self.champ_select_menu.setTitle(QCoreApplication.translate("MainWindow", u"\u82f1\u96c4\u9078\u64c7", None))
        pass
    # retranslateUi

