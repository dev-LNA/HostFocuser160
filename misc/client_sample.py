from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSignal, QThreadPool, QEvent, QObject
from PyQt6.QtWidgets import QPushButton, QLineEdit, QProgressBar, QTextEdit, QLabel, QStackedWidget, QSpinBox, QSlider, QDoubleSpinBox

from src.core.config import Config
from src.utils.constants import constants
from src.utils.constants import ServerJsonKeys as SJson

from misc.client_updater import Updater
from misc.client_sender import ReqSender

import zmq
import sys
import json
import os
import socket

def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # No executável, sys._MEIPASS é a raiz da pasta temporária
        base_path = sys._MEIPASS
    else:
        # No desenvolvimento, a base é a pasta raiz do projeto (onde está o main4.py)
        # Como este arquivo está em misc, pegamos o pai dele
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    return os.path.normpath(os.path.join(base_path, relative_path))

main_ui_path = resource_path('assets/ui/client.ui')

TEST_SETUP = True

class ClientSimulator(QtWidgets.QMainWindow):

    sig = pyqtSignal(int)

    _client_id = 666
    _client_transaction_ID = 0
    _client_name = "Simulator"

    def __init__(self, clientID: int=None, clientName: str=None):
        super(ClientSimulator, self).__init__()
        uic.loadUi(main_ui_path, self)

        if not self._check_config():
            return

        self._updater = None
        self._sender = None

        if clientID is not None:
            self.client_ID = clientID
        if clientName is not None:
            self.name = clientName
        
    # Associate UI variables to allow intellisense with PyQt Widgets
        self.btnMove = self.findChild(QtWidgets.QPushButton, 'btnMove')
        self.btnMove: QPushButton = self.btnMove
        # self.btnConnect = self.findChild(QtWidgets.QPushButton, 'btnConnect')
        # self.btnConnect: QPushButton = self.btnConnect
        self.btnHalt = self.findChild(QtWidgets.QPushButton, 'btnHalt')
        self.btnHalt: QPushButton = self.btnHalt
        self.btnHome = self.findChild(QtWidgets.QPushButton, 'btnHome')
        self.btnHome: QPushButton = self.btnHome
        self.btnUp = self.findChild(QtWidgets.QPushButton, 'btnUp')
        self.btnUp: QPushButton = self.btnUp
        self.btnDown = self.findChild(QtWidgets.QPushButton, 'btnDown')
        self.btnDown: QPushButton = self.btnDown
        self.btnUpdateStatus = self.findChild(QtWidgets.QPushButton, 'btnUpdateStatus')
        self.btnUpdateStatus: QPushButton = self.btnUpdateStatus
        self.btnHome_Park = self.findChild(QtWidgets.QPushButton, 'btnHome_Park')
        self.btnHome_Park: QPushButton = self.btnHome_Park

        self.BarFocuser = self.findChild(QtWidgets.QProgressBar, 'BarFocuser')
        self.BarFocuser: QProgressBar = self.BarFocuser
        self.txtStatus = self.findChild(QtWidgets.QTextEdit, 'txtStatus')
        self.txtStatus: QTextEdit = self.txtStatus

        self.statConn_2 = self.findChild(QtWidgets.QLabel, 'statConn_2')     #TODO: Verificar pq não consigo colocar sem o "_2" no designer
        self.statConn_2: QLabel = self.statConn_2
        self.statMov_2 = self.findChild(QtWidgets.QLabel, 'statMov_2')     #TODO: Verificar pq não consigo colocar sem o "_2" no designer
        self.statMov_2: QLabel = self.statMov_2
        self.statBusy_2 = self.findChild(QtWidgets.QLabel, 'statBusy_2')     #TODO: Verificar pq não consigo colocar sem o "_2" no designer
        self.statBusy_2: QLabel = self.statBusy_2
        self.statInit_2 = self.findChild(QtWidgets.QLabel, 'statInit_2')     #TODO: Verificar pq não consigo colocar sem o "_2" no designer
        self.statInit_2: QLabel = self.statInit_2

        self.lblMotorID = self.findChild(QtWidgets.QLabel, 'lblMotorID')
        self.lblMotorID: QLabel = self.lblMotorID
        self.lblMotorIP = self.findChild(QtWidgets.QLabel, 'lblMotorIP')
        self.lblMotorIP: QLabel = self.lblMotorIP
        self.lblClientID = self.findChild(QtWidgets.QLabel, 'lblClientID')
        self.lblClientID: QLabel = self.lblClientID

        self.lblServerIP = self.findChild(QtWidgets.QLabel, 'lblServerIP')
        self.lblServerIP: QLabel = self.lblServerIP

        self.txtClientIp = self.findChild(QtWidgets.QLineEdit, 'txtClientIp')
        self.txtClientIp: QLineEdit = self.txtClientIp

        self.btnConnectClient = self.findChild(QtWidgets.QPushButton, 'btnConnectClient')
        self.btnConnectClient: QPushButton = self.btnConnectClient

        self.pageSelect = self.findChild(QtWidgets.QStackedWidget, 'pageSelect')
        self.pageSelect: QStackedWidget = self.pageSelect

        self.stsBar = self.findChild(QtWidgets.QStatusBar, 'stsBar')
        self.stsBar: QStackedWidget = self.stsBar

        self.sbMovePos: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "sbMovePos")
        self.sbMovePos.setSuffix(u" mm\u207B\u00B2")    # Unicode symbols to show -2 superscript

        self.ledFocusIn: QLabel = self.findChild(QLabel, "ledFocusIn")
        self.ledFocusIn.installEventFilter(self)

        self.ledFocusOut: QLabel = self.findChild(QLabel, "ledFocusOut")
        self.ledFocusOut.installEventFilter(self)


        self.sbSpeed: QDoubleSpinBox = self.findChild(QDoubleSpinBox, 'sbSpeed')
        self.sliderSpeed: QSlider = self.findChild(QSlider, 'sliderSpeed')

        self.sliderSpeed.valueChanged.connect(lambda val: self.sbSpeed.setValue(val * 0.1))
        self.sbSpeed.setValue(self.sliderSpeed.value() * 0.1)

        self.statInit: QLabel = self.findChild(QLabel, 'statInit')

        self.statAlarm: QLabel = self.findChild(QLabel, 'statAlarm')

        self.lblFocusPos: QLabel = self.findChild(QLabel, 'lblFocusPos')

        
    # Configure Widgets and Widgets Actions
        self.btnMove.clicked.connect(self._move_to)
        self.btnMove.setStatusTip("Set focus position")
        # self.btnConnect.clicked.connect(self._connect)
        self.btnHalt.clicked.connect(self._halt)
        self.btnHome.clicked.connect(self._home)
        self.btnUp.clicked.connect(self._move_out)
        self.btnDown.clicked.connect(self._move_in)
        self.btnConnectClient.clicked.connect(self._connect_to_server)
        self.btnUpdateStatus.clicked.connect(self._get_status)
        self.btnHome_Park.clicked.connect(self._home_park)

        # self.BarFocuser.setStyleSheet("QProgressBar::chunk { background-color: rgb(26, 26, 26) } QProgressBar { color: indianred; }")
        self.BarFocuser.setTextDirection(QProgressBar.Direction.BottomToTop) 
        self.BarFocuser.setMaximum(2510)
        self.BarFocuser.setMinimum(-200)
                            
        self.txtClientIp.setText(_get_private_ip())                      # Considers the Ip of the current machine
        self.txtClientIp.returnPressed.connect(self._clientIpDefined)    # Configures event of return key press
        self.txtClientIp.setInputMask('000.000.000.000;')
        # inputValidator = QRegularExpressionValidator(                   # Validator that allows only numbers and points
        #     QRegularExpression("[0-9.]+"), self.txtClientIp                 #TODO: trocar por -> self.txtClientIp.setInputMask('000.000.000.000;_')
        # )
        # self.txtClientIp.setValidator(inputValidator)

        self.pageSelect.setCurrentIndex(0)                              # Defines starting widget


        # Events definitions
        #   Install event filter on objects
        self.statConn_2.installEventFilter(self)
        self.statMov_2.installEventFilter(self)
        self.statBusy_2.installEventFilter(self)
        self.statInit_2.installEventFilter(self)
        self.BarFocuser.installEventFilter(self)
        self.statInit.installEventFilter(self)
        self.statAlarm.installEventFilter(self)

        # self.context = zmq.Context()       
        self.context = None

        self.previous_is_mov = None
        self.previous_pos = None

        self.connected = False
        self.is_moving = False
        self.homing = False
        self.position = 0

        # self._client_id = 666
        # self._client_transaction_ID = 0

        self._msg_json = {
            "clientId": self.client_ID,
            "clientTransactionId": self.transaction_ID,
            "clientName": self.name,
            "action": "STATUS"
        }

        # self._start_client()
        # self.txtStatus.setText(f"{Config.ip_address}")
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.update)
        # self._get_status()
        # self.timer.start(100)  

    @property
    def client_ID(self) -> int:
        return self._client_id
    
    @client_ID.setter
    def client_ID(self, value: int):
        self._client_id = value

    @property
    def transaction_ID(self) -> int:
        return self._client_transaction_ID
    
    @transaction_ID.setter
    def transaction_ID(self, value: int):
        self._client_transaction_ID = value

    @property
    def name(self) -> str:
        return self._client_name
    
    @name.setter
    def name(self, value: str):
        self._client_name = value   


    def _connect_to_server(self):
        """
        Starts the client and the 'update' method.
        Before the creation of the 0mq context a ping is performed to guarantee that
            the server is reachable.
        
        :param self: 
        """
        self._connection_ip = self.txtClientIp.text()
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((self._connection_ip, self.port_pub))
            s.close()
            
            self.context = zmq.Context() 
            self.context.setsockopt(zmq.LINGER, 0)      # Drop pending messages in case of timeout        
            self._start_client()  
            self.txtStatus.setText(f"Connected to + {self._connection_ip}")    
            self.lblServerIP.setText(self._connection_ip)
            
            
            self.threadpool = QThreadPool()                                                  # Defines threadpool
            self._updater = Updater(poller=self.poller, subscriber=self.subscriber)          # Creates Updater thread
            self._updater.signals.message.connect(self.txtStatus.setText)                    # Updates status text box with updated message
            self._updater.signals.position.connect(lambda val: self.BarFocuser.setValue(int(val)))                 # Updates bar value with position
            self._updater.signals.position.connect(lambda val: self.lblFocusPos.setText(str(val)) if val!=constants.INVALID_RESPONSE else self.lblFocusPos.setText('Invalid'))
            # self._updater.signals.clientID.connect(self.statBusy_2.setText)                  # Updates client Id
            self._updater.signals.lbl_clientId_style.connect(self.statBusy_2.setProperty)  # Updates style of client Id label according to status
            self._updater.signals.connected.connect(self._update_connect_status)
            self._updater.signals.lbl_conn_style.connect(self.statConn_2.setProperty)      #
            self._updater.signals.homing.connect(self._update_home_status)
            self._updater.signals.lbl_init_style.connect(self.statInit_2.setProperty)
            self._updater.signals.is_moving.connect(self._update_moving_status)
            self._updater.signals.lbl_mov_style.connect(self.statMov_2.setProperty)
            self._updater.signals.focus_in_status.connect(self.ledFocusIn.setProperty)
            self._updater.signals.focus_out_status.connect(self.ledFocusOut.setProperty)
            self._updater.signals.alarm.connect(self.statAlarm.setProperty)
            self._updater.signals.initialized.connect(self.statInit.setProperty)
            
            self._sender = ReqSender(req=self.req)
            self._sender.signals.timeout_error.connect(self._reset_client_context)
            self._sender.signals.response.connect(self.txtStatus.setText)
            self._sender.setAutoDelete(False)

            # Initial update
            message = self.subscriber.recv_string()
            
            self.txtStatus.setText(message)
            data = json.loads(message)
            
            self.lblMotorID.setText(data["device_ID"])
            self.lblMotorIP.setText(data["device_IP"])
            self.lblClientID.setText(str(self.client_ID))
            self.sbMovePos.setValue(data[SJson.MAX_STEP])
            
            self.statusBar().clearMessage()
            self.pageSelect.setCurrentIndex(1)

            self.threadpool.start(self._updater)    # Starts updater
            # self.threadpool.start(self._sender)     # Starts sender


        except Exception as e:
            print({str(e)})
            self.statusBar().showMessage("Could not establish connection to server")

    def _clientIpDefined(self):
        self.btnConnectClient.click()

    def _check_config(self):
        try:
            self.ip_addr = Config.ip_address  
            self.port_pub = Config.port_pub  
            self.port_req = Config.port_rep
            return True
        except:
            return False

    def _start_client(self):
        self.txtStatus.setText("Connecting subscriber socket...")
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://{self._connection_ip}:{Config.port_pub}")
        topics_to_subscribe = ''

        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, topics_to_subscribe)

        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)

        self.txtStatus.setText("Connecting requisition socket...")
        self.req = self.context.socket(zmq.REQ)
        self.req.connect(f"tcp://{self._connection_ip}:{Config.port_rep}")
        self.txtStatus.clear()
       
    def _reset_client_context(self):
        """ Resets client context to allow continuous communication in case of a timeout  """
        try:
            self._clear_thread_updater()
            self._clear_thread_sender()
            self.context.destroy()
            self._connect_to_server()
            print(f"[ZMQ Client] Communication reset success")
        except:
            print(f"[ZMQ Client] Error establishing connection")
        
    
    def _send_command(self, command: str, timeout: int=5000) -> str: #1500
        try:
            self.transaction_ID += 1                                        #   Updates transaction ID
            self._sender.send_request(self, command, timeout)               #   Sets message
            self.threadpool.start(self._sender)                             #   Starts Sender thread    
            return "OK"
        except Exception as e:
            return f"[ZMQ Client] Error sending command to server -> {str(e)}"

    def _connect(self):
        # self._send_command("CONNECT")
        pass
        

    def _home(self):
        self._send_command("HOME")

    def _home_park(self):
        self._send_command("PARK")

    def _disconnect(self):
        # self._send_command("DISCONNECT")
        # If the updater thread is active it is necessary to safely close it
        self._clear_thread_updater()
        # If the sender thread is active it is necessary to safely close it
        self._clear_thread_sender()

    def _halt(self):
        self._send_command("HALT")

    def _move_to(self):
        # if not self.is_moving:
        # pos = str(10 * self.sbMovePos.value())
        pos = self.sbMovePos.text()[:-4]    # Must remove the suffix from the QSpinDoubleBox
        self._send_command(f"MOVE={pos}")

    def _move_in(self):
        # status = json.loads(self.txtStatus.toPlainText())

        max_speed = int(self._updater.data['maxSpeed'])                 # actually is the Normal speed configuration
        if not self.is_moving:
            if TEST_SETUP:
                self._send_command(f"FOCUSIN=" + f"{str(int(max_speed * self.sbSpeed.value() * 0.01))}")   #TEST_VALUE -> ORIGINAL VALUE => FOCUSIN=200
            else:
                self._send_command(f"FOCUSIN=" + f"{str(int(max_speed * self.sbSpeed.value() * 0.01))}")
        else:
            self._send_command("HALT")

    def _move_out(self):
        status = json.loads(self.txtStatus.toPlainText())
        max_speed = int(status['maxSpeed'])                 # actually is the Normal speed configuration
        if not self.is_moving:
            if TEST_SETUP:
                self._send_command(f"FOCUSOUT="  + f"{str(int(max_speed * self.sbSpeed.value() * 0.01))}")  #TEST_VALUE -> ORIGINAL VALUE => FOCUSOUT=200
            else:
                self._send_command(f"FOCUSOUT="  + f"{str(int(max_speed * self.sbSpeed.value() * 0.01))}")
        else:
            self._send_command("HALT")
                
    def _get_status(self):
        if self._sender._send is False:                          # A new command is only sent if the last one was already sent
            self._send_command("STATUS")

            
    def _clear_thread_updater(self):
        if self._updater is not None:
            self._updater.stop()                         # Sends stop signal to thread
            while self._updater.finished is not True:    # Waits thread to finish
                pass
            self._updater = None                         # Clears updater

    def _clear_thread_sender(self):
        if self._sender is not None:
            self._sender.stop()                         # Sends stop signal to thread
            while self._sender.finished is not True:    # Waits thread to finish
                pass
            self._sender = None                         # Clears sender

    def _update_connect_status(self, status):
        self.connected = status
        print(f"Connected = {self.connected}")

    def _update_home_status(self, status):
        self.homing = status

    def _update_moving_status(self, status):
        self.is_moving = status


    def _update_gui_element(self, widget: QtWidgets):
        """Updates the GUI element style after an event occured

        Parameters
        ----------
        widget : QtWidgets
            Widget to be updated
        """
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Process events

        Parameters
        ----------
        obj : QObject
            Object that triggered the event
        event : QEvent
            Event that occurred

        Returns
        -------
        bool
            Returns if everything went ok
        """

        # Events related to a 'Dynamic Property' being changed
        if event.type() == QEvent.Type.DynamicPropertyChange:

            if obj.__class__ is QtWidgets.QLabel:
                    # Executed when a label property changes
                    self._update_gui_element(obj)
                    return True 
            
        # For all other events or objects, return False to allow normal handling
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """Close application"""
        if(self.context):
            self._disconnect()
        self.sig.emit(self.client_ID)
        event.accept()

def _get_private_ip():
    """
    Gets the IP address of the PC running the program.
    This will be considered as the initial IP to connect to the host.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as st:
        st.settimeout(0.0)
        try:
            st.connect((Config.gateway_ip, 80))          # Opens a connections just to verify the socket
            ip = st.getsockname()[0]
        except socket.error:
            ip = '127.0.0.1'                            #TODO: Mostrar uma mensagem de erro?
        st.close()
    return ip



