# app.py - Connections to Sockets (ZeroMQ) an control management
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QPixmap

from logging import Logger

import time
import zmq
import json
from enum import Enum, StrEnum
from datetime import datetime
# from pythonping import ping
from icmplib import ping
from os import path
import sys

from misc.client_sample import TEST_SETUP
from src.core.config import Config
import src.core.exceptions as AlpacaExceptions
from src.utils.constants import constants, MotorModels, ReachStatus, MotorParamsIdx, ServerCommands, MotorValidCommands
from src.utils.constants import ServerJsonKeys as SJson
from src.utils.signals import PropertySignals, MultiSignal
from src.utils.motor import Motor
from src.interface.zmq_comm import zmqComm

import socket

# from src.interface.dmx_eth import FocuserDriver as Focuser
# from src.interface.focuser_driver import FocuserDriver as Focuser

TESTE_TCSPD = False             #TEST: Colocar em True para realizar teste com o tcspd

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)

icon_con_ok = resource_path('../../assets/ui/icons/status.png')
icon_con_nok = resource_path('../../assets/ui/icons/status-busy.png')
icon_con_wait = resource_path('../../assets/ui/icons/status-away.png')

class ServerSignals(QObject):
    server_status = PropertySignals()
    router_status = PropertySignals()
    motor_status = PropertySignals()
    status_message = pyqtSignal(str)
    connection_speed = pyqtSignal(str)
    
    # encoder = pyqtSignal(str)
    # position_str = pyqtSignal(str)
    # position_int = pyqtSignal(int)
    max_pos = pyqtSignal(int)
    backlash = pyqtSignal(int)
    # moving = PropertySignals()
    # lim_min = PropertySignals()
    # lim_max = PropertySignals()
    # initialized = PropertySignals()
    parking = PropertySignals()
    firmware_status = pyqtSignal(str)
    last_command = pyqtSignal(dict)
    communicating_to_motor_bool = pyqtSignal(bool)
    client_id = pyqtSignal(str)
    transaction_id = pyqtSignal(str)

class Server(QObject):

    signals = ServerSignals()


    def __init__(self, logger: Logger):
        super(Server, self).__init__()
        self.logger = logger                            # Instantiates logger
    
        # Network (ZMQ)
        self.zmq_comm: zmqComm = None

        # Control variables
        self.motor:Motor = None

        self._stop_loop = False                          #|
        self.previous_is_mov = False                    #|
        self.previous_homing = False                    #|
        self.previous_initialized = False               #|
        self.previous_parking = False                   #|  Control variables initialization
        self.previous_pos = 0                           #|
        self.last_ping_time = datetime.now()            #|
        self.last_pub_time:datetime = datetime.now()                  #|
        self._flag_change = False                       #|

        # Variables for status request
        self._client_id = '0' 
        self.busy_id = 0
        self._router_reachable = False 
        self._motor_reachable = False
        self.motor:Motor = None                               # Instantiates motor as None
        self.motor_model = None

        # self._is_moving = False                         #|
        # self._is_busy = False                           #|
        # self._position = 0                              #|
        # self._homing = False                            #|
        # self._parking = False                           #| 
        # self._initialized = False                       #|
        # self._stopping = False                          #|  Status initialization
        #                             #|
        #                                 #|
        # self._current_speed = Config.max_speed          #|
        # self._encoder = 0                               #|
        # self._status_lim_minus = False                  #|
        # self._status_lim_max = False                    #|
        # self._transaction_id = 0                        #|
        #                   #|
        #                     #|

        

        # Status Message
        if TESTE_TCSPD:                                 #TEST: O json do tcspd não está atualizado então é necessário usar o antigo para testar com o tcspd
            self.status = {
                SJson.ABSOLUTE.value: Config.absolute,            
                SJson.ALARM.value: 0,
                SJson.BROKER.value: "Focuser160",
                SJson.CMD.value: {
                    SJson.CMD_CLIENT_ID.value : self._client_id,
                    SJson.CMD_CLIENT_TRANSACTION_ID.value: 0,
                    SJson.CMD_CLIENT_NAME.value: "",
                    SJson.CMD_ACTION.value: ""
                },
                SJson.CONNECTED.value: False,
                SJson.CONTROLLER.value: Config.name,
                SJson.DEVICE.value: Config.device_name,
                SJson.ERROR.value: "",
                SJson.HOMING.value: False,            # Homing solicited
                SJson.INITIALIZED.value: False,       # Homing finalized
                SJson.IS_MOVING.value: False,          # Executing a function inside the motor
                SJson.MAX_SPEED.value: Config.max_speed,
                SJson.MAX_STEP.value: Config.max_step,
                SJson.POSITION.value: 0,
                SJson.TEMP_COMP.value: Config.temp_comp,
                SJson.TEMP_COMP_AVAIABLE.value: Config.tempcompavailable,
                SJson.TEMPERATURE.value: 0,
                SJson.TIMESTAMP.value: datetime.isoformat(datetime.now(), timespec='milliseconds'),
                SJson.VERSION.value: "1.0.0",            #TODO: Pegar a versão do arquivo config.toml
            }
        else:
            self.status = {
                SJson.ABSOLUTE.value: Config.absolute,            
                SJson.ALARM.value: 0,
                SJson.BROKER.value: "Focuser160",
                SJson.CMD.value: {
                    SJson.CMD_CLIENT_ID.value : self._client_id,
                    SJson.CMD_CLIENT_TRANSACTION_ID.value: 0,
                    SJson.CMD_CLIENT_NAME.value: "",
                    SJson.CMD_ACTION.value: ""
                },
                SJson.CONNECTED.value: False,
                SJson.CONTROLLER.value: Config.name,
                SJson.DEVICE.value: Config.device_name,
                SJson.ERROR.value: "",
                SJson.HOMING.value: False,            # Homing solicited
                SJson.INITIALIZED.value: False,       # Homing finalized
                SJson.IS_MOVING.value: False,          # Executing a function inside the motor
                SJson.MAX_SPEED.value: Config.max_speed,
                SJson.MAX_STEP.value: Config.max_step,
                SJson.POSITION.value: 0,
                SJson.TEMP_COMP.value: Config.temp_comp,
                SJson.TEMP_COMP_AVAIABLE.value: Config.tempcompavailable,
                SJson.TEMPERATURE.value: 0,
                SJson.TIMESTAMP.value: datetime.isoformat(datetime.now(), timespec='milliseconds'),
                SJson.VERSION.value: "1.0.0",            #TODO: Pegar a versão do arquivo config.toml
                SJson.PARKING.value: False,               # Executing Parking
                SJson.DEVICE_IP.value: "127.0.0.1",       # Motor IP
                SJson.DEVICE_ID.value: "",                # Motor ID
                SJson.DEVICE_FIRMWARE_VERSION.value: "",  # Motor firmware version
                SJson.TIMEOUT.value: False,               # Timeout
            }



    def teste(self):
        if self.zmq_comm:
            self.status[SJson.TIMESTAMP] = self.zmq_comm.pub(self.status)
            print(self.zmq_comm._connected)
        else:
            print('Server communication not defined')

    @property
    def stop_loop(self):
        return self._stop_loop
    @stop_loop.setter
    def stop_loop(self, value: bool):
        self._stop_loop = value


    @property
    def server_online(self):
        """Status of server
        
        Setting a new value will update the server status and emit '_signals_server' """
        return self._server_connected
    @server_online.setter
    def server_online(self, value: bool):
        self._server_connected = value
        if value:
            self.signals.server_status.emit(value,"statusLed", "OK")          # When server is connected the 'statusLed' is green (defined in the stylesheet)
        else:
            self.signals.server_status.emit(value,"statusLed", "NOK")         # When server is NOT connected the 'statusLed' is red (defined in the stylesheet)

    def start_server(self):
        """Starts server communication"""
        if self.zmq_comm:
            self.logger.info(f'Trying to start the server but the server is already running')
            return
        
        self.zmq_comm = zmqComm(Config.ip_address,
                                    port_pub=Config.port_pub,
                                    port_rep=Config.port_rep
                                    )
        try:
            self.server_online = self.zmq_comm.connect()
            self.logger.info(f"Publisher binded to {self.zmq_comm.ip_address}:{self.zmq_comm.port_pub}")
            self.logger.info(f"REP binded to {self.zmq_comm.ip_address}:{self.zmq_comm.port_rep}")
            self.logger.info(f'Server started')
        except Exception as e:
            self.logger.error(e)

    def stop_server(self):
        """Disconnects motor and stops server communication"""
        try:
            self.motor.disconnect()
            self.status[SJson.CONNECTED] = self.motor.connected
            # self.motor = None
            self.motor_reachable = False
            self.logger.info(f'Motor disconnected')
            self.zmq_comm.pub(self.status)
            self.server_online = self.zmq_comm.disconnect()
            self.zmq_comm = None
            self.router_reachable = False
            self.logger.info(f'Server stopped')
        except Exception as e:
            print(e)
            self.logger.error(e)

    def init_device(self, motor_model: MotorModels):
        """Initializes the motor driver according to the selected focuser

        Parameters
        ----------
        motor_model : str
            Motor model

        Raises
        ------
        ValueError
            Raises exception if the motor model is not valid
        """
        if self.motor == None:                                                         # If motor was not instantiated

            self.motor = Motor(motor_model)     # Instantiates the motor according to the selected focuser
            self.motor_model = motor_model
        else:
            raise ValueError("Invalid motor model")                                         # Raises an exception if the motor value is not valid


    def reach_device(self):
        """Verifies if the router and the motor are reachable. 
        If its reachable connects to the motor and updates status information"""
        _try = 0
        self.last_ping_time = datetime.now()                                                    # Saves the time when the method was called

        if not self.router_reachable:                                                           # If the router is not reachable
            self.router_reachable = ReachStatus.CONNECTING                                           # Emits signals for GUI update (Router attempting connection)
            self.motor_reachable = ReachStatus.WAITING                                               # Emits signals for GUI update (Motor waiting)
            self.communicating_to_motor = False                                                     # Not communicating to the motor
                        
            for _try in range(5):                                                                   # Tries 5 times to ping the router
                time.sleep(0.5)             # delay between tries                         
                self.signals.status_message.emit(f"Trying Connect to Router: Try number {_try+1}")                      # Emits signals for GUI update
                self.router_reachable = ping(Config.router_ip, count=1, timeout=0.6, privileged=False).is_alive         # Tries to ping the router IP
                if self.router_reachable:                                                                               # If the ping is succesful
                    self.signals.status_message.emit(f"Connection succesfull after {_try+1} tries")                         # Emits signals for GUI update
                    break                                                                                   # Exits for loop
        else:                                                                                   # If router already reachable
            self.router_reachable = ReachStatus.CONNECTED                                           # Emits signals for GUI update (Router connected)

        if self.router_reachable and not self.motor_reachable:                                  # If the router is reachable and the motor is not reachable
            time.sleep(0.5)
            self.motor_reachable = ReachStatus.CONNECTING                                            # Emits signals for GUI update (Motor attempting connection)
            self.communicating_to_motor = False                                                     # Not communicating to the motor
            
            for _try in range(5):                                                                   # Tries 5 times to ping the router
                time.sleep(0.5)             # delay between tries
                self.signals.status_message.emit(f"Trying Connect to Motor: Try number {_try+1}")               # Emits signals for GUI update
                self.motor_reachable = self.motor.ping()                                              # Tries to ping the motor IP
                if self._motor_reachable:                                                               # If the ping is successful
                    # print("Connection succesfull after", (_try+1), "tries" )
                    self.signals.status_message.emit(f"Connection succesfull after {_try+1} tries")                 # Emits signals for GUI update
                    break                                                                                   # Exits for loop
            
        if self.motor_reachable:                                                                # If the motor is reachable
            self.router_reachable = ReachStatus.CONNECTED                                            # Emits signals for GUI update
            self.motor_reachable = ReachStatus.CONNECTED                                           # Emits signals for GUI update
            time.sleep(0.2)                
            try:
                self.motor.connect()                                                        # Creates the socket and connects the server to the motor
                # self.position =self.motor.position                                                 # Reads current motor position
                self.motor.update_status()
                self.status["position"] = self.motor.position                                             # Updates status
                self.status["initialized"] = self.motor.initialized                                # Updates status
                self.status["device_IP"] = self.motor.get_param(MotorParamsIdx.MOTOR_IP)                                    # Updates status
                self.status["device_ID"] = self.motor.ID                                    # Updates status
                self.status["device_Firmware_Version"] = self.motor.firmware_version        # Updates status

                # self._check_homing()                                                                # Emits homing signals      #TODO: Trocar nome do método

            #--- Emits max pos and backlash to update GUI. The value is different in the test setup due to the size and gear differences
                if TEST_SETUP:
                    self.signals.max_pos.emit(int(self.motor.get_param(MotorParamsIdx.MAX_POS)) + 5)             # A small gap at the end to account the distance to the lim+ uswitch 
                    self.signals.backlash.emit(-(int(self.motor.get_param(MotorParamsIdx.BACKLASH)) + 10))       # A small gap at the end to account the distance to the lim+ uswitch 
                else:
                    # TODO: Definir valores de excursão na montagem real
                    self.signals.max_pos.emit(int(self.motor.get_param(MotorParamsIdx.MAX_POS)))                 # A small gap at the end to account the distance to the lim+ uswitch 
                    self.signals.backlash.emit(-(int(self.motor.get_param(MotorParamsIdx.BACKLASH))))            # A small gap at the end to account the distance to the lim+ uswitch 
                
                self.logger.info(f'Motor Reached and connected.')
            except Exception as e:
                self.logger.error(f'{str(e)}')     

    def run(self):
        """Server Main Loop (Runs on a thread started by main)
        
        The server main loop is responsible for:
        - Receiving commands from clients
        - Publishing status
        - Checking connectivity status
        """
        self.stop_loop = False
        self._client_id = 0
        # command_handlers = {                                        # Handles for the methods to be executed according to the commands
        #     'HOME': self._handle_home,
        #     # 'HALT': self.handle_halt,
        #     'STATUS': self._pub_status,
        #     'PARK': self._handle_park
        # }
        if self.motor is None:
            self.init_device(self.motor_model)
        self.start_server()
        self.reach_device()
        self.status[SJson.CONNECTED] = self.motor.connected
        while self._stop_loop == False:
            t0 = time.time()                                        # Keeps the time when the loop began
            current_time = datetime.now()                           # Reads current time

        # Atualização de leituras?
            # self.signals.firmware_status.emit(self.motor.firmware_status)
            self.status[SJson.POSITION] = self.motor.position

        # Publica status a cada 1 segundo
            if abs(current_time.second - self.last_pub_time.second) >= 1:
                # try:
                self.last_pub_time = self.zmq_comm.pub(self.status)
                self.logger.debug(f'Status published: {self.status}')
                # except Exception as e:
                #     print(e)
                #     self.logger.error(e)

            if self.motor.connected and self.zmq_comm.poller:
                socks = dict(self.zmq_comm.poller.poll(50))
                if socks.get(self.zmq_comm.replier) == zmq.POLLIN:
                    self.motor.update_status()                                                          # Updates motor status
                    parsed_cmd = self._parse_client_command(self.zmq_comm.replier.recv_string())        # Parses client command
                    self._handle_command(parsed_cmd)                                                    # Handles clent command



                self.status[SJson.CONNECTED] = self.motor.connected
                self.motor.update_status()

            else:
                self.reach_device()
                self.status["connected"] = self.motor.connected                                                                # Updates "connected" state
                self.signals.status_message.emit("")    

            self.signals.connection_speed.emit(f"{round(time.time()-t0, 3)}")



        print("Finalizado")
        self.signals.connection_speed.emit(f"") 
        #--- Things to do when 'run' is stopped
        resp = self.zmq_comm.stop_poller()
        self.logger.info(resp)


    def _parse_client_command(self, msg: str) -> dict:
        """Parses received command and updates status

        :param msg: received command
        :type msg: str
        :return: Dictionary containing the command and parameters
        :rtype: dict
        """
        try:
            parsed = dict()
            print(f"mensagem recebida: {msg}")
            msg = json.loads(msg)
            print(f"mensagem json: {msg}")

            cmd = msg.get(SJson.CMD_ACTION)
            if cmd != ServerCommands.STATUS and \
                ( (msg.get(SJson.CMD_CLIENT_ID) == self._client_id or \
                self._client_id == '0') ):
                # Only accept commands (except for status request) if it 
                # was requested by the same client #TODO: Checar se essa lógica precisa ser utilizada
                self.status[SJson.CMD] = msg
                self.clientID = msg.get(SJson.CMD_CLIENT_ID)
                self.transaction_id = msg.get(SJson.CMD_CLIENT_TRANSACTION_ID)

            print(f'received command : {cmd}')
            p = cmd.find('=')
            print(f'Equal sign at {p} position')

            if p == -1:         # '-1' indicates that there is no '=' sign so there is no parameter 
                parsed = {
                    'COMMAND': cmd,
                    'PARAMETER': None
                }
            else:
                parsed = {
                    'COMMAND': cmd[:p],
                    'PARAMETER': int(cmd[p+1:])
                }    
            




            return parsed
        except Exception as e:
            print(e)
            self.zmq_comm.reply('NAK')   # If an error occurred during the reading of the JSON return 'NAK' to the client
                                                       # Logs error

    def _handle_command(self, cmd: dict):
        try:
            # Handle all possible commands
            self.status["error"] = ""             
                                                                              # Resets "error" status
            print(f'Command: {cmd['COMMAND']}')
            print(f'Parameter: {cmd['PARAMETER']}')

            # 'STATUS' is a command to the server and not to the motor
            if cmd["COMMAND"] == ServerCommands.STATUS:
                self.zmq_comm.pub(self.status)            
            else:
                if cmd["COMMAND"] in MotorValidCommands:
                    if self.motor.is_moving:
                        raise RuntimeError(f'Cannot issue "{cmd["COMMAND"]}" command while motor is moving')

                self.communicating_to_motor = True
                resp = self.motor.send_command(cmd)
                self.communicating_to_motor = False
                if resp == "NOK":
                    raise RuntimeError(f'Motor returned "NOK" trying to run command "{cmd["COMMAND"]}"')
            self.zmq_comm.reply('ACK')
            self.logger.info(f'Command issued: {cmd}')
        except Exception as e:                
            self.zmq_comm.reply('NAK')                                                                      # If an exception occurs during the handling of the command 
            self.zmq_comm.pub(self.status)                              # Publishes current status                                                                                       # Published current status
            self.logger.error(f'Error: {str(e)}')            

    @property
    def clientID(self) -> str:
        """The ID of the client.

        Setting a new value will update the client ID and emit '_signal_client_id' to
        update its value wherever it is needed.
        """
        return self._client_id                          
    @clientID.setter
    def clientID(self, ID: str):
        self._client_id = ID
        if ID != '0':
            self.status[SJson.CMD_CLIENT_ID] = ID
            self.signals.client_id.emit(ID)
        else:
            self.status[SJson.CMD_CLIENT_ID] = ''
            self.signals.client_id.emit('')

    @property
    def transaction_id(self) -> str:
        """Client transaction ID.
        
        Setting a new value will update the client transaction ID and emit '_signal_transaction_id' """
        return self._transaction_id
    @transaction_id.setter
    def transaction_id(self, value: int):
        if self.clientID:                                   # The transaction ID must be related to a client
            self._transaction_id = value
            self.status[SJson.CMD_CLIENT_TRANSACTION_ID] = str(value)
            self.signals.transaction_id.emit(str(value))
        else:
            self._transaction_id = 0
            self.status[SJson.CMD_CLIENT_TRANSACTION_ID] = ''
            self.signals.transaction_id.emit("")

    @property
    def router_reachable(self) -> bool:
        return self._router_reachable
    @router_reachable.setter
    def router_reachable(self, status: ReachStatus | bool):
        if isinstance(status, bool):
            if status == True:
                status = ReachStatus.CONNECTED
            else:
                status = ReachStatus.WAITING

        self.signals.router_status.info.emit("conStatusBar", status)
        if status == ReachStatus.CONNECTED:
            self.signals.router_status.emit(True, "statusLed", "OK")
            self._router_reachable = True
        else:
            self.signals.router_status.emit(False, "statusLed", "NOK")
            self._router_reachable = False

    @property
    def motor_reachable(self) -> bool:
        return self._motor_reachable
    @motor_reachable.setter
    def motor_reachable(self, status: ReachStatus | bool):
        if isinstance(status, bool):
            if status == True:
                status = ReachStatus.CONNECTED
            else:
                status = ReachStatus.WAITING

        self.signals.motor_status.info.emit("conStatusBar", status)
        if status == ReachStatus.CONNECTED:
            self.signals.motor_status.emit(True, "statusLed", "OK")
            self._motor_reachable = True
        else:
            self.signals.motor_status.emit(False, "statusLed", "NOK")
            self._motor_reachable = False


    @property
    def communicating_to_motor(self):   #TODO: Verificar se vai ser usada essa informação
        """Status of the communication between server and motor. Indicates that a message is being sent from the server to the motor.
        
        Setting a new value will update the communication status and emit '_signal_communicating_to_motor_bool'.
        Also emits the signal '_statusBar_led' to update the status bar led         #TODO: mudar esse signal"""
        return self._communicating_to_motor
    @communicating_to_motor.setter
    def communicating_to_motor(self, value: bool):
        self._communicating_to_motor = value
        self.signals.communicating_to_motor_bool.emit(value)