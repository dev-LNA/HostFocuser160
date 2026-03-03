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
    QStatusBar,
    QFrame,
    QSlider)





class UiWidgets(QWidget):
    def __init__(self, window, window_name: str):


        if window_name == "main":
        # === Definitions for main window components === #

            # BOTAO PARA TESTES
            self.btnTestes = window.findChild(QPushButton, 'btnTestes')
            self.btnTestes: QPushButton = self.btnTestes
            self.editTeste = window.findChild(QLineEdit, 'editTeste')
            self.editTeste: QLineEdit = self.editTeste



        # Buttons
            self.btnStart = window.findChild(QPushButton, 'btnStart')
            self.btnStart: QPushButton = self.btnStart

            self.btnStop = window.findChild(QPushButton, 'btnStop')
            self.btnStop: QPushButton = self.btnStop

            self.btnArrow = window.findChild(QPushButton, 'btnArrow')
            self.btnArrow: QPushButton = self.btnArrow

            
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

            self.lblSocketIP = window.findChild(QLabel, 'lblSocketIP')
            self.lblSocketIP: QLabel = self.lblSocketIP

            self.lblPortPUB = window.findChild(QLabel, 'lblPortPUB')
            self.lblPortPUB: QLabel = self.lblPortPUB

            self.lblPortREP = window.findChild(QLabel, 'lblPortREP')
            self.lblPortREP: QLabel = self.lblPortREP

            self.lblComSpeed = window.findChild(QLabel, 'lblComSpeed')
            self.lblComSpeed: QLabel = self.lblComSpeed

    # Command info group box

            
            self.infoFrame = window.findChild(QFrame, 'infoFrame')
            self.infoFrame: QFrame = self.infoFrame

            self.gbCommandInfo = window.findChild(QGroupBox, 'gbCommandInfo')
            self.gbCommandInfo: QGroupBox = self.gbCommandInfo

            self.lblTime = window.findChild(QLabel, 'lblTime')
            self.lblTime: QLabel = self.lblTime

            self.lblClientName_val = window.findChild(QLabel, 'lblClientName_val')
            self.lblClientName_val: QLabel = self.lblClientName_val

            self.lblClientID_val = window.findChild(QLabel, 'lblClientID_val')
            self.lblClientID_val: QLabel = self.lblClientID_val
            
            self.lblTransactionId_val = window.findChild(QLabel, 'lblTransactionId_val')
            self.lblTransactionId_val: QLabel = self.lblTransactionId_val
            
            self.lblCommand_val = window.findChild(QLabel, 'lblCommand_val')
            self.lblCommand_val: QLabel = self.lblCommand_val
            
            self.lblLastHoming_val = window.findChild(QLabel, 'lblLastHoming_val')
            self.lblLastHoming_val: QLabel = self.lblLastHoming_val

            

    # Focuser status group box

            self.gbFocuserStatus = window.findChild(QGroupBox, 'gbFocuserStatus')
            self.gbFocuserStatus: QGroupBox = self.gbFocuserStatus

            self.ledMoving = window.findChild(QLabel, 'ledMoving')
            self.ledMoving: QLabel = self.ledMoving

            self.ledHome = window.findChild(QLabel, 'ledHome')
            self.ledHome: QLabel = self.ledHome

            self.ledLimMin = window.findChild(QLabel, 'ledLimMin')
            self.ledLimMin: QLabel = self.ledLimMin

            self.ledLimMax = window.findChild(QLabel, 'ledLimMax')
            self.ledLimMax: QLabel = self.ledLimMax

            self.lblEncoder_val = window.findChild(QLabel, 'lblEncoder_val')
            self.lblEncoder_val: QLabel = self.lblEncoder_val

            self.lblPosition_val = window.findChild(QLabel, 'lblPosition_val')
            self.lblPosition_val: QLabel = self.lblPosition_val

            self.lblStatus_val = window.findChild(QLabel, 'lblStatus_val')
            self.lblStatus_val: QLabel = self.lblStatus_val

            self.posSlider = window.findChild(QSlider, 'posSlider')
            self.posSlider: QSlider = self.posSlider

        elif window_name == "settings":
            # === Definitions for settings window components === #
            
            # Buttons
            self.btnEngineering = window.findChild(QPushButton, 'btnEngineering')
            self.btnEngineering: QPushButton = self.btnEngineering
            
            self.btnSave = window.findChild(QPushButton, 'btnSave')
            self.btnSave: QPushButton = self.btnSave


            # Labels
            self.lblFirmVer_value = window.findChild(QLabel, 'lblFirmVer_value')
            self.lblFirmVer_value: QLabel = self.lblFirmVer_value

            self.lblServerVer_val = window.findChild(QLabel, 'lblServerVer_val')
            self.lblServerVer_val: QLabel = self.lblServerVer_val

            self.lblFocuser = window.findChild(QLabel, 'lblFocuser')
            self.lblFocuser: QLabel = self.lblFocuser

            # Text boxes
            self.txtMotorIP = window.findChild(QLineEdit, 'txtMotorIP')
            self.txtMotorIP: QLineEdit = self.txtMotorIP

            self.txtBackComp = window.findChild(QLineEdit, 'txtBackComp')
            self.txtBackComp: QLineEdit = self.txtBackComp

            self.txtMaxPos = window.findChild(QLineEdit, 'txtMaxPos')
            self.txtMaxPos: QLineEdit = self.txtMaxPos

            self.txtPark = window.findChild(QLineEdit, 'txtPark')
            self.txtPark: QLineEdit = self.txtPark

            self.txtMaxSpeed = window.findChild(QLineEdit, 'txtMaxSpeed')
            self.txtMaxSpeed: QLineEdit = self.txtMaxSpeed

            self.txtNormalSpeed = window.findChild(QLineEdit, 'txtNormalSpeed')
            self.txtNormalSpeed: QLineEdit = self.txtNormalSpeed

            self.txtLowSpeed = window.findChild(QLineEdit, 'txtLowSpeed')
            self.txtLowSpeed: QLineEdit = self.txtLowSpeed

        # Frame send command

            self.frameCommand = window.findChild(QFrame, 'frameCommand')
            self.frameCommand: QFrame = self.frameCommand

            self.txtCommand = window.findChild(QLineEdit, 'txtCommand')
            self.txtCommand: QLineEdit = self.txtCommand

            self.lblResponse_Val = window.findChild(QLabel, 'lblResponse_Val')
            self.lblResponse_Val: QLabel = self.lblResponse_Val

            self.btnSendCommand = window.findChild(QPushButton, 'btnSendCommand')
            self.btnSendCommand: QPushButton = self.btnSendCommand






