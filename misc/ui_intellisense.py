from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QPropertyAnimation
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
    QSlider,
    QStackedWidget,
    QRadioButton,
    QSpinBox,
    QDoubleSpinBox,
    QListWidget,
    QCheckBox,
    QMenuBar,
    QMainWindow)





class UiWidgets(QWidget):
    def __init__(self, window: QMainWindow, window_name: str):


        if window_name == "main":
        # === Definitions for main window components === #
        
            temp_item = window.menuBar()
            if temp_item:
                self.menuBar: QMenuBar = temp_item
            temp_item = window.statusBar()
            if temp_item:
                self.statusBar: QStatusBar = temp_item

            self.pageSelect = window.findChild(QStackedWidget, 'pageSelect')
            self.pageSelect: QStackedWidget = self.pageSelect

            # BOTAO PARA TESTES
            self.btnTestes = window.findChild(QPushButton, 'btnTestes')
            self.btnTestes: QPushButton = self.btnTestes

            self.editTeste = window.findChild(QLineEdit, 'editTeste')
            self.editTeste: QLineEdit = self.editTeste

        # Begin Page layout
            self.btnStartServer = window.findChild(QPushButton, 'btnStartServer')
            self.btnStartServer: QPushButton = self.btnStartServer

            self.rb160 = window.findChild(QRadioButton, 'rb160')
            self.rb160: QRadioButton = self.rb160

            self.rbIAG = window.findChild(QRadioButton, 'rbIAG')
            self.rbIAG: QRadioButton = self.rbIAG



        # Buttons
            self.lblMotor = window.findChild(QLabel, 'lblMotor')
            self.lblMotor: QLabel = self.lblMotor

            self.lblTitle = window.findChild(QLabel, 'lblTitle')
            self.lblTitle: QLabel = self.lblTitle

            self.btnStart = window.findChild(QPushButton, 'btnStart')
            self.btnStart: QPushButton = self.btnStart

            self.btnStop = window.findChild(QPushButton, 'btnStop')
            self.btnStop: QPushButton = self.btnStop

            self.btnArrow = window.findChild(QPushButton, 'btnArrow')
            self.btnArrow: QPushButton = self.btnArrow

            self.menuOptions = window.findChild(QMenu, 'menuOptions')
            self.menuOptions: QMenu = self.menuOptions

        # Actions
            self.actionHide = window.findChild(QAction, 'actionHide')
            self.actionHide: QAction = self.actionHide

            self.actionAbout = window.findChild(QAction, 'actionAbout')
            self.actionAbout: QAction = self.actionAbout

            self.actionEngineering = window.findChild(QAction, 'actionEngineering')
            self.actionEngineering: QAction = self.actionEngineering

            self.actionShow_toolbar = window.findChild(QAction, 'actionShow_toolbar')
            self.actionShow_toolbar: QAction = self.actionShow_toolbar

            self.actionClient_Simulator = window.findChild(QAction, 'actionClient_Simulator')
            self.actionClient_Simulator: QAction = self.actionClient_Simulator

            self.actionShow_Log = window.findChild(QAction, 'actionShow_Log')
            self.actionShow_Log: QAction = self.actionShow_Log

            self.toolBar = window.findChild(QToolBar, 'toolBar')
            self.toolBar: QToolBar = self.toolBar

        # LEDS
            self.ledServer = window.findChild(QLabel, 'ledServer')
            self.ledServer: QLabel = self.ledServer

            self.ledRouter = window.findChild(QLabel, 'ledRouter')
            self.ledRouter: QLabel = self.ledRouter

            self.ledMotor = window.findChild(QLabel, 'ledMotor')
            self.ledMotor: QLabel = self.ledMotor

            self.ledAlarm = window.findChild(QLabel, 'ledAlarm')
            self.ledAlarm: QLabel = self.ledAlarm

            self.ledFocusIn = window.findChild(QLabel, 'ledFocusIn')
            self.ledFocusIn: QLabel = self.ledFocusIn

            self.ledFocusOut = window.findChild(QLabel, 'ledFocusOut')
            self.ledFocusOut: QLabel = self.ledFocusOut

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

            self.lblSpeed = window.findChild(QLabel, 'lblSpeed')
            self.lblSpeed: QLabel = self.lblSpeed

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

            self.ledPark = window.findChild(QLabel, 'ledPark')
            self.ledPark: QLabel = self.ledPark

            self.ledLimMin = window.findChild(QLabel, 'ledLimMin')
            self.ledLimMin: QLabel = self.ledLimMin

            self.ledLimMax = window.findChild(QLabel, 'ledLimMax')
            self.ledLimMax: QLabel = self.ledLimMax

            self.ledProcessing = window.findChild(QLabel, 'ledProcessing')
            self.ledProcessing: QLabel = self.ledProcessing

            self.lblPosition_val = window.findChild(QLabel, 'lblPosition_val')
            self.lblPosition_val: QLabel = self.lblPosition_val

            self.lblStatus_val = window.findChild(QLabel, 'lblStatus_val')
            self.lblStatus_val: QLabel = self.lblStatus_val

            self.posSlider = window.findChild(QSlider, 'posSlider')
            self.posSlider: QSlider = self.posSlider



        elif window_name == "settings":
            # === Definitions for settings window components === #
            
            temp_item = window.statusBar()
            if temp_item:
                self.statusBar: QStatusBar = temp_item
            
            self.gbMotorParameters:QGroupBox = window.findChild(QGroupBox, 'gbMotorParameters')
            # self.gbMotorParameters: QGroupBox = self.gbMotorParameters

            self.gbZMQ = window.findChild(QGroupBox, 'gbZMQ')
            self.gbZMQ: QGroupBox = self.gbZMQ

            self.gbNetwork = window.findChild(QGroupBox, 'gbNetwork')
            self.gbNetwork: QGroupBox = self.gbNetwork

            self.gbRetrieveParameters: QGroupBox = window.findChild(QGroupBox, 'gbRetrieveParameters')

            self.gbServerParams: QGroupBox = window.findChild(QGroupBox, 'gbServerParams')


            # Buttons
            self.btnEngineering = window.findChild(QPushButton, 'btnEngineering')
            self.btnEngineering: QPushButton = self.btnEngineering
            
            self.btnSave = window.findChild(QPushButton, 'btnSave')
            self.btnSave: QPushButton = self.btnSave
            
            self.btnDefault = window.findChild(QPushButton, 'btnDefault')
            self.btnDefault: QPushButton = self.btnDefault
            
            self.btnBackup = window.findChild(QPushButton, 'btnBackup')
            self.btnBackup: QPushButton = self.btnBackup
            
            self.btnReadMotor = window.findChild(QPushButton, 'btnReadMotor')
            self.btnReadMotor: QPushButton = self.btnReadMotor


            # Labels
            self.lblFirmVer_value = window.findChild(QLabel, 'lblFirmVer_value')
            self.lblFirmVer_value: QLabel = self.lblFirmVer_value

            self.lblServerVer_val = window.findChild(QLabel, 'lblServerVer_val')
            self.lblServerVer_val: QLabel = self.lblServerVer_val

            self.lblFocuser = window.findChild(QLabel, 'lblFocuser')
            self.lblFocuser: QLabel = self.lblFocuser

            self.lblAccessLvl:QLabel = window.findChild(QLabel, 'lblAccessLvl')

        # Text boxes
        
            self.txtMotorIP = window.findChild(QLineEdit, 'txtMotorIP')
            self.txtMotorIP: QLineEdit = self.txtMotorIP

            self.txtSocketIP = window.findChild(QLineEdit, 'txtSocketIP')
            self.txtSocketIP: QLineEdit = self.txtSocketIP

            self.spinPortPub = window.findChild(QSpinBox, 'spinPortPub')
            self.spinPortPub: QSpinBox = self.spinPortPub

            self.spinPortRep = window.findChild(QSpinBox, 'spinPortRep')
            self.spinPortRep: QSpinBox = self.spinPortRep

            self.txtSubMask = window.findChild(QLineEdit, 'txtSubMask')
            self.txtSubMask: QLineEdit = self.txtSubMask

            self.txtGatewayIP = window.findChild(QLineEdit, 'txtGatewayIP')
            self.txtGatewayIP: QLineEdit = self.txtGatewayIP

        #Spin Boxes

            self.spinPortPub = window.findChild(QSpinBox, 'spinPortPub')
            self.spinPortPub: QSpinBox = self.spinPortPub

            self.spinPortRep = window.findChild(QSpinBox, 'spinPortRep')
            self.spinPortRep: QSpinBox = self.spinPortRep

            self.spinBacklash = window.findChild(QSpinBox, 'spinBacklash')
            self.spinBacklash: QSpinBox = self.spinBacklash

            self.spinMaxPos = window.findChild(QSpinBox, 'spinMaxPos')
            self.spinMaxPos: QSpinBox = self.spinMaxPos

            self.spinParkPos = window.findChild(QSpinBox, 'spinParkPos')
            self.spinParkPos: QSpinBox = self.spinParkPos

            self.spinMaxSpeed = window.findChild(QSpinBox, 'spinMaxSpeed')
            self.spinMaxSpeed: QSpinBox = self.spinMaxSpeed

            self.spinNormalSpeed = window.findChild(QSpinBox, 'spinNormalSpeed')
            self.spinNormalSpeed: QSpinBox = self.spinNormalSpeed

            self.spinLowSpeed = window.findChild(QSpinBox, 'spinLowSpeed')
            self.spinLowSpeed: QSpinBox = self.spinLowSpeed

            self.spinMaxStep = window.findChild(QSpinBox, 'spinMaxStep')
            self.spinMaxStep: QSpinBox = self.spinMaxStep

            self.spinTCPTimeout: QSpinBox = window.findChild(QSpinBox, 'spinTCPTimeout')

            self.spinComCycle: QSpinBox = window.findChild(QSpinBox, 'spinComCycle')

            self.spinMBTimeout: QSpinBox = window.findChild(QSpinBox, 'spinMBTimeout')

            self.spinKeepAliveTimeout: QSpinBox = window.findChild(QSpinBox, 'spinKeepAliveTimeout')

            self.spinAcceleration = window.findChild(QDoubleSpinBox, 'spinAcceleration')
            self.spinAcceleration: QDoubleSpinBox = self.spinAcceleration

            self.spinDeceleration = window.findChild(QDoubleSpinBox, 'spinDeceleration')
            self.spinDeceleration: QDoubleSpinBox = self.spinDeceleration

            self.spinIdleCurrent = window.findChild(QDoubleSpinBox, 'spinIdleCurrent')
            self.spinIdleCurrent: QDoubleSpinBox = self.spinIdleCurrent

            self.spinRunCurrent = window.findChild(QDoubleSpinBox, 'spinRunCurrent')
            self.spinRunCurrent: QDoubleSpinBox = self.spinRunCurrent

            self.spinAccCurrent = window.findChild(QDoubleSpinBox, 'spinAccCurrent')
            self.spinAccCurrent: QDoubleSpinBox = self.spinAccCurrent


        # Frame send command

            self.frameCommand = window.findChild(QFrame, 'frameCommand')
            self.frameCommand: QFrame = self.frameCommand

            self.txtCommand = window.findChild(QLineEdit, 'txtCommand')
            self.txtCommand: QLineEdit = self.txtCommand

            self.lblResponse_Val = window.findChild(QLabel, 'lblResponse_Val')
            self.lblResponse_Val: QLabel = self.lblResponse_Val

            self.btnSendCommand = window.findChild(QPushButton, 'btnSendCommand')
            self.btnSendCommand: QPushButton = self.btnSendCommand

        # Check boxes

            self.cbAutoStartup: QCheckBox = window.findChild(QCheckBox, 'cbAutoStartup')
            self.cbCLPAutoRestart: QCheckBox = window.findChild(QCheckBox, 'cbCLPAutoRestart')
            self.cbMotorAutoRestart: QCheckBox = window.findChild(QCheckBox, 'cbMotorAutoRestart')







