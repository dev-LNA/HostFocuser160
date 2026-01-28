from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer, QRegularExpression, pyqtSignal
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QPushButton, QLineEdit, QProgressBar, QTextEdit, QLabel, QStackedWidget

from src.core.config import Config

import zmq
import sys
import json
import os
import time
import socket

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

main_ui_path = resource_path('../assets/client.ui')

class ClientSimulator(QtWidgets.QMainWindow):

    sig = pyqtSignal(bool)

    def __init__(self):
        super(ClientSimulator, self).__init__()
        uic.loadUi(main_ui_path, self)

        if not self._check_config():
            return

        
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

        self.lblTestConn1 = self.findChild(QLabel, 'lblTestConn1')
        self.lblTestConn1: QLabel = self.lblTestConn1

        self.btnConnectClient = self.findChild(QtWidgets.QPushButton, 'btnConnectClient')
        self.btnConnectClient: QPushButton = self.btnConnectClient

        self.pageSelect = self.findChild(QtWidgets.QStackedWidget, 'pageSelect')
        self.pageSelect: QStackedWidget = self.pageSelect
        
    # Configure Widgets and Widgets Actions
        self.btnMove.clicked.connect(self._move_to)
        self.btnConnect.clicked.connect(self._connect)
        self.btnHalt.clicked.connect(self._halt)
        self.btnHome.clicked.connect(self._home)
        self.btnUp.clicked.connect(self._move_out)
        self.btnDown.clicked.connect(self._move_in)
        self.btnConnectClient.clicked.connect(self._connect_to_server)
        self.btnUpdateStatus.clicked.connect(self._get_status)

        self.BarFocuser.setStyleSheet("QProgressBar::chunk { background-color: rgb(26, 26, 26) } QProgressBar { color: indianred; }")
        self.BarFocuser.setTextDirection(0) 

        self.lblTestConn1.setText("")                             
        self.txtClientIp.setText(_get_private_ip())                      # Considers the Ip of the current machine
        self.txtClientIp.returnPressed.connect(self._clientIpDefined)    # Configures event of return key press
        inputValidator = QRegularExpressionValidator(                   # Validator that allows only numbers and points
            QRegularExpression("[0-9.]+"), self.txtClientIp
        )
        self.txtClientIp.setValidator(inputValidator)

        self.pageSelect.setCurrentIndex(0)                              # Defines starting widget

        


        # self.context = zmq.Context()       
        self.context = None

        self.previous_is_mov = None
        self.previous_pos = None

        self.connected = False
        self.is_moving = False
        self.homing = False
        self.position = 0

        self._client_id = 666

        self._msg_json = {
            "clientId": self._client_id,
            "clientTransactionId": 0,
            "clientName": "Simulator",
            "action": "STATUS"
        }

        # self._start_client()
        # self.txtStatus.setText(f"{Config.ip_address}")
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.update)
        # self._get_status()
        # self.timer.start(100)  

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
            self._start_client()  
            self.txtStatus.setText(f"Connected to + {self._connection_ip}")    
            self.lblServerIP.setText(self._connection_ip)
            self.timer = QTimer()
            self.timer.timeout.connect(self.update)
            self._get_status()
            self.timer.start(100)  

            message = self.subscriber.recv_string()
            self.txtStatus.setText(message)
            data = json.loads(message)

            self.lblMotorID.setText(data["device_ID"])
            self.lblMotorIP.setText(data["device_IP"])
            self.lblMotorFirmVer.setText(data["device_Firmware_Version"])

            self.pageSelect.setCurrentIndex(1)
        except Exception as e:
            print({str(e)})
            self.lblTestConn1.setText("Could not establish connection to server")



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

        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://{self._connection_ip}:{Config.port_pub}")
        topics_to_subscribe = ''

        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, topics_to_subscribe)

        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)

        self.req = self.context.socket(zmq.REQ)
        self.req.connect(f"tcp://{self._connection_ip}:{Config.port_rep}")


    def _send_request(self, action, timeout=1000):
        self._msg_json["action"] = action
        self.req.send_string(json.dumps(self._msg_json))

        poller = zmq.Poller()
        poller.register(self.req, zmq.POLLIN)

        socks = dict(poller.poll(timeout))  # Timeout in milliseconds
        if socks.get(self.req) == zmq.POLLIN:
            try:
                response = self.req.recv_string()
                return response
            except Exception as e:
                print(f"Error receiving response: {e}")
                return None
        else:
            print(f"No response received within {timeout} milliseconds.")
            return None
    
    def _connect(self):
        response = self._send_request("CONNECT")
        if response:
            self.txtStatus.setText(response)

    def _home(self):
        response = self._send_request("HOME")
        if response:
            self.txtStatus.setText(response)

    def _disconnect(self):
        response = self._send_request("DISCONNECT")
        if response:
            self.txtStatus.setText(response)

    def _halt(self):
        response = self._send_request("HALT")
        if response:
            self.txtStatus.setText(response)

    def _move_to(self):
        if not self.is_moving:
            pos = self.txtMov.text()
            response = self._send_request(f"MOVE={pos}")
            if response:
                self.txtStatus.setText(response)

    def _move_in(self):
        if not self.is_moving:
            response = self._send_request("FOCUSIN=200")
            if response:
                self.txtStatus.setText(response)

    def _move_out(self):
        if not self.is_moving:
            response = self._send_request("FOCUSOUT=200")
            if response:
                self.txtStatus.setText(response)

    def _get_status(self):
        response = self._send_request("STATUS")
        if response:
            self.txtStatus.setText(response)

    def update(self):
        if round(time.time() % 35) == 0:
            self._get_status()
        self.socks = dict(self.poller.poll(100))
        if self.socks.get(self.subscriber) == zmq.POLLIN:
            message = self.subscriber.recv_string()
            self.txtStatus.setText(message)
            data = json.loads(message)
            try: 
                self.position = int(data["position"])                    
                self.BarFocuser.setValue(int(self.position))
                if (data["cmd"]["clientId"]) > 0:
                    self.statBusy_2.setStyleSheet("background-color: lightgreen")
                    self.statBusy_2.setText(str(data["cmd"]["clientId"]))
                else:
                    self.statBusy_2.setText('')
                    self.statBusy_2.setStyleSheet("background-color: indianred")
                if data["homing"]:
                    self.homing = True
                    self.statInit_2.setStyleSheet("background-color: lightgreen")
                else:
                    self.homing = False
                    self.statInit_2.setStyleSheet("background-color: indianred") 
                if data["isMoving"]:
                    self.is_moving = True
                    self.statMov_2.setStyleSheet("background-color: lightgreen")
                else:
                    self.is_moving = False
                    self.statMov_2.setStyleSheet("background-color: indianred") 
                if data["connected"]:
                    self.connected = True
                    self.statConn_2.setStyleSheet("background-color: lightgreen")
                else:
                    self.connected = False
                    self.statConn_2.setStyleSheet("background-color: indianred")               
            except Exception as e:
                print(e)
                self.BarFocuser.setValue(0)
    
    def closeEvent(self, event):
        """Close application"""
        if(self.context):
            self._disconnect()
        self.sig.emit(True)
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