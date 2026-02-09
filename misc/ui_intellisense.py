from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QWidget, 
    QMessageBox, 
    QMenu, 
    QSystemTrayIcon, 
    QPushButton,
    QToolBar, 
    QLabel,
    QProgressBar,
    QLineEdit,
    QGroupBox,
    QTextEdit,
    QDockWidget,
    QStatusBar)




class UiWidgets(QWidget):
    def __init__(self, window):

        # BOTAO PARA TESTES
        self.btnTestes = window.findChild(QPushButton, 'btnTestes')
        self.btnTestes: QPushButton = self.btnTestes


        # uic.loadUi(main_ui_path, self)

    # Buttons
        self.btnStart = window.findChild(QPushButton, 'btnStart')
        self.btnStart: QPushButton = self.btnStart

        self.btnStop = window.findChild(QPushButton, 'btnStop')
        self.btnStop: QPushButton = self.btnStop

        
        self.menuOptions = window.findChild(QMenu, 'menuOptions')
        self.menuOptions: QMenu = self.menuOptions

        self.actionHide = window.findChild(QAction, 'actionHide')
        self.actionHide: QAction = self.actionHide

        self.actionSettings = window.findChild(QAction, 'actionSettings')
        self.actionSettings: QAction = self.actionSettings

        self.actionShow_toolbar = window.findChild(QAction, 'actionShow_toolbar')
        self.actionShow_toolbar: QAction = self.actionShow_toolbar

        self.actionClient_Simulator = window.findChild(QAction, 'actionClient_Simulator')
        self.actionClient_Simulator: QAction = self.actionClient_Simulator

        self.actionShow_Log = window.findChild(QAction, 'actionShow_Log')
        self.actionShow_Log: QAction = self.actionShow_Log

        self.toolBar = window.findChild(QToolBar, 'toolBar')
        self.toolBar: QToolBar = self.toolBar

        self.ledServer = window.findChild(QLabel, 'ledServer')
        self.ledServer: QLabel = self.ledServer

        self.ledRouter = window.findChild(QLabel, 'ledRouter')
        self.ledRouter: QLabel = self.ledRouter

        self.ledMotor = window.findChild(QLabel, 'ledMotor')
        self.ledMotor: QLabel = self.ledMotor

        self.conBarServerRouter = window.findChild(QProgressBar, 'conBarServerRouter')
        self.conBarServerRouter: QProgressBar = self.conBarServerRouter

        self.conBarRouterMotor = window.findChild(QProgressBar, 'conBarRouterMotor')
        self.conBarRouterMotor: QProgressBar = self.conBarRouterMotor

        # self.statusbar = window.findChild(QStatusBar, 'statusbar')
        # self.statusbar: QStatusBar = self.statusbar


# Connectivity group box

        self.gbConnectivity = window.findChild(QGroupBox, 'gbConnectivity')
        self.gbConnectivity: QGroupBox = self.gbConnectivity

        self.txtSocketIP = window.findChild(QLineEdit, 'txtSocketIP')
        self.txtSocketIP: QLineEdit = self.txtSocketIP

        self.txtPortPUB = window.findChild(QLineEdit, 'txtPortPUB')
        self.txtPortPUB: QLineEdit = self.txtPortPUB

        self.txtPortREP = window.findChild(QLineEdit, 'txtPortREP')
        self.txtPortREP: QLineEdit = self.txtPortREP

        self.txtComSpeed = window.findChild(QLineEdit, 'txtComSpeed')
        self.txtComSpeed: QLineEdit = self.txtComSpeed

# Driver info group box










