from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSignal, QThreadPool
from PyQt6.QtWidgets import QPushButton, QLineEdit, QProgressBar, QTextEdit, QLabel, QStackedWidget

from src.core.config import Config

from misc.client_updater import Updater
from misc.client_sender import ReqSender

import zmq
import sys
import json
import os
import socket

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

main_ui_path = resource_path('../assets/client.ui')

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
        self.btnConnect = self.findChild(QtWidgets.QPushButton, 'btnConnect')
        self.btnConnect: QPushButton = self.btnConnect
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
        self.lblMotorFirmVer = self.findChild(QtWidgets.QLabel, 'lblMotorFirmVer')
        self.lblMotorFirmVer: QLabel = self.lblMotorFirmVer

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
        
    # Configure Widgets and Widgets Actions
        self.btnMove.clicked.connect(self._move_to)
        self.btnMove.setStatusTip("Set focus position")
        self.btnConnect.clicked.connect(self._connect)
        self.btnHalt.clicked.connect(self._halt)
        self.btnHome.clicked.connect(self._home)
        self.btnUp.clicked.connect(self._move_out)
        self.btnDown.clicked.connect(self._move_in)
        self.btnConnectClient.clicked.connect(self._connect_to_server)
        self.btnUpdateStatus.clicked.connect(self._get_status)

        self.BarFocuser.setStyleSheet("QProgressBar::chunk { background-color: rgb(26, 26, 26) } QProgressBar { color: indianred; }")
        self.BarFocuser.setTextDirection(QProgressBar.Direction.BottomToTop) 
                            
        self.txtClientIp.setText(_get_private_ip())                      # Considers the Ip of the current machine
        self.txtClientIp.returnPressed.connect(self._clientIpDefined)    # Configures event of return key press
        self.txtClientIp.setInputMask('000.000.000.000;')
        # inputValidator = QRegularExpressionValidator(                   # Validator that allows only numbers and points
        #     QRegularExpression("[0-9.]+"), self.txtClientIp                 #TODO: trocar por -> self.txtClientIp.setInputMask('000.000.000.000;_')
        # )
        # self.txtClientIp.setValidator(inputValidator)

        self.pageSelect.setCurrentIndex(0)                              # Defines starting widget

        


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
            self._updater.signals.position.connect(self.BarFocuser.setValue)                 # Updates bar value with position
            self._updater.signals.clientID.connect(self.statBusy_2.setText)                  # Updates client Id
            self._updater.signals.lbl_clientId_style.connect(self.statBusy_2.setStyleSheet)  # Updates style of client Id label according to status
            self._updater.signals.connected.connect(self._update_connect_status)
            self._updater.signals.lbl_conn_style.connect(self.statConn_2.setStyleSheet)      #
            self._updater.signals.homing.connect(self._update_home_status)
            self._updater.signals.lbl_init_style.connect(self.statInit_2.setStyleSheet)
            self._updater.signals.is_moving.connect(self._update_moving_status)
            self._updater.signals.lbl_mov_style.connect(self.statMov_2.setStyleSheet)
            
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
            self.lblMotorFirmVer.setText(data["device_Firmware_Version"])
            
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
            print(f"Communication reset success")
        except:
            print(f"Error establishing connection")
        
    
    def _send_command(self, command: str, timeout: int=1500) -> str:
        try:
            self.transaction_ID += 1                                        #   Updates transaction ID
            self._sender.send_request(self, command, timeout)               #   Sets message
            self.threadpool.start(self._sender)                             #   Starts Sender thread    
            return "OK"
        except Exception as e:
            return f"Error sending command to server -> {str(e)}"

    def _connect(self):
        self._send_command("CONNECT")
        

    def _home(self):
        self._send_command("HOME")

    def _disconnect(self):
        self._send_command("DISCONNECT")
        # If the updater thread is active it is necessary to safely close it
        self._clear_thread_updater()
        # If the sender thread is active it is necessary to safely close it
        self._clear_thread_sender()

    def _halt(self):
        self._send_command("HALT")

    def _move_to(self):
        if not self.is_moving:
            pos = self.txtMov.text()
            self._send_command(f"MOVE={pos}")

    def _move_in(self):
        if not self.is_moving:
            self._send_command("FOCUSIN=9")   #TEST_VALUE -> ORIGINAL VALUE => FOCUSIN=200

    def _move_out(self):
        if not self.is_moving:
            self._send_command("FOCUSOUT=9")  #TEST_VALUE -> ORIGINAL VALUE => FOCUSOUT=200

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
            st.connect((Config.router_ip, 80))          # Opens a connections just to verify the socket
            ip = st.getsockname()[0]
        except socket.error:
            ip = '127.0.0.1'                            #TODO: Mostrar uma mensagem de erro?
        st.close()
    return ip