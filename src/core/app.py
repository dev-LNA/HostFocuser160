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
import numpy
import zmq
import json
import socket
from datetime import datetime
from pythonping import ping
from os import path
import sys

from src.core.config import Config
import src.core.exceptions as AlpacaExceptions
from src.utils.constants import constants
from src.utils.signals import PropertySignals

# from src.interface.dmx_eth import FocuserDriver as Focuser
from src.interface.motor_driver import FocuserDriver as Focuser


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)

icon_con_ok = resource_path('../../assets/ui/icons/status.png')
icon_con_nok = resource_path('../../assets/ui/icons/status-busy.png')
icon_con_wait = resource_path('../../assets/ui/icons/status-away.png')

class App(QObject):

    _signals_router = PropertySignals()
    _signals_motor = PropertySignals()

    _signal_server_started_status = pyqtSignal(str, str)
    _signal_server_started_bool = pyqtSignal(bool)

    _statusMessage = pyqtSignal(str)
    _connection_speed = pyqtSignal(str)

    _signal_communicating_to_motor_bool = pyqtSignal(bool)
    _statusBar_led = pyqtSignal(QPixmap)

    _signal_client_id = pyqtSignal(str)
    _signal_transaction_id = pyqtSignal(str)
    _signal_position = pyqtSignal(str)
    _signal_encoder = pyqtSignal(str)
    
    _signal_firmware_status = pyqtSignal(str)

    _signals_moving = PropertySignals()
    _signals_lim_min = PropertySignals()
    _signals_lim_max = PropertySignals()

    _signals_server = PropertySignals()


    

    def __init__(self, logger: Logger):
        super(App, self).__init__()
        self.logger = logger
        self.config_file = r"src/config/config.toml"   #TODO: Remover, não é usado para nada.

        # Network Settings
        self.context = None
        self.ip_address = Config.ip_address
        self.port_pub = Config.port_pub
        self.port_rep = Config.port_rep
        self.poller = None
        self.connection_speed = 0

        # Control variables
        self._stop_var = False
        self.previous_is_mov = False
        self.previous_homing = False
        self.previous_pos = 0
        self.last_ping_time = datetime.now()
        self.last_pub = datetime.now()
        self._flag_change = False

        #variables for status request
        self._is_moving = False
        self._is_busy = False
        self._position = 0
        self._homing = False
        self._stopping = False
        self._client_id = 0
        self.busy_id = 0
        self._current_speed = Config.max_speed
        self._encoder = 0

        self._status_lim_minus = False
        self._status_lim_max = False


        self._transaction_id = 0

        # Status Message
        self.status = {
            "absolute": Config.absolute,
            "alarm": 0,
            "broker": "Focuser160",
            "cmd": {
                "clientId": self._client_id,
                "clientTransactionId": 0,
                "clientName": "",
                "action": ""
            },
            "connected": False,
            "controller": Config.name,
            "device": Config.device_name,
            "device_IP": "127.0.0.1",
            "device_ID": "",
            "device_Firmware_Version": "",
            "error": "",
            "timeout": False,
            "homing": False,            # Homing solicited
            "initialized": False,       # Homing finalized
            "isMoving": False,          # Executing a function inside the motor
            "maxSpeed": Config.max_speed,
            "maxStep": Config.max_step,
            "position": 0,
            "tempComp": Config.temp_comp,
            "tempCompAvailable": Config.tempcompavailable,
            "temperature": 0,
            "timestamp": datetime.isoformat(datetime.now(), timespec='milliseconds'),
            "version": "1.0.0"            #TODO: Pegar a versão do arquivo config.toml
        }
        
        self.device = Focuser(self.logger, constants.ARCUS_DMX_ETH)

    # Reaching the device and starting the server at this point is not necessary        
        # self.reach_device()
        # self.start_server()

    def reach_device(self):
        """Ping device and reads the position and initialized variables"""
        _try = 0
        self.last_ping_time = datetime.now()

        if not self.router_reachable:
            self._signals_router_connection("connecting")
            self._signals_motor_connection("waiting")
            self.communicating_to_motor = False
            
            
            for _try in range(5):
                print(f"Trying Connect to Router: Try number {_try+1}")
                self._statusMessage.emit(f"Trying Connect to Router: Try number {_try+1}")
                self.router_reachable = self.ping_router()
                if self.router_reachable:
                    print("Connection succesfull after", (_try+1), "tries" )
                    self._statusMessage.emit(f"Connection succesfull after {_try+1} tries")
                    self._signals_router_connection("connected")
                    break


        if self.router_reachable:
            self._signals_router_connection("connected")
            self._signals_motor_connection("connecting")
            self.communicating_to_motor = False
            
            for _try in range(5): 
                print(f"Trying Connect to Motor: Try number {_try+1}")
                self._statusMessage.emit(f"Trying Connect to Motor: Try number {_try+1}")
                self._motor_reachable = self.ping_server()
                if self._motor_reachable:
                    print("Connection succesfull after", (_try+1), "tries" )
                    self._statusMessage.emit(f"Connection succesfull after {_try+1} tries")
                    self._signals_motor_connection("connected")
                    break
            
            if self._motor_reachable:
                self._signals_motor_connection("connected")
                              
                try:
                    self.device.connected = True
                    self.position =self.device.position
                    self.status["position"] = self.position
                    self.status["initialized"] = self.device.initialized
                    self.status["device_IP"] = self.device.device_IP
                    self.status["device_ID"] = self.device.device_ID
                    self.status["device_Firmware_Version"] = self.device.device_Firmware_Version
                    
                    self.logger.info(f'Device Reached.')
                except Exception as e:
                    self.logger.error(f'Error reaching device: {str(e)}')     

    def start_server(self): 
        """ Starts Server ZeroMQ, creating context 
        then binding PUB and REP sockets"""

        if self.context:                                                                # If context already created returns
            self.server_connected = True
            return  
        
        self.context = zmq.Context()                                                    # Creates context
        print('Context Created')

        try:
            # Status Publisher
            self.publisher = self.context.socket(zmq.PUB)                               # Creates PUB
            self.publisher.bind(f"tcp://{self.ip_address}:{self.port_pub}")             # Binds PUB to * IP address and configured PUB port
            print(f"Publisher binded to {self.ip_address}:{self.port_pub}")
        except Exception as e:
            self.logger.error(f'Error Binding Publisher: {str(e)}')
            self.server_connected = False
            return

        try:
            # Command REP
            self.replier = self.context.socket(zmq.REP)                                 # Creates REP
            self.replier.bind(f"tcp://{self.ip_address}:{self.port_rep}")               # Binds REP to * IP adress and configured REP port
            print(f"REP binded to {self.ip_address}:{self.port_rep}")
        except Exception as e:
            self.logger.error(f'Error Binding Replier: {str(e)}')
            self.server_connected = False
            return

        # Poller
        self.poller = zmq.Poller()                                                      # Creates Poller
        self.poller.register(self.replier, zmq.POLLIN)                                  # Register poller to monitoring REP
        self.logger.info(f'Server Started')
        self._pub_status()                                                               # Publishes current status to ZMQ
        self.server_connected = True
        
    
    def _close_connection(self):
        """Unbind all sockets and destroy context"""
        self.device.disconnect()
        self.status["connected"] = self.device.connected
        self._pub_status()
        try:
            if(self.publisher):
                self.publisher.unbind(f"tcp://{self.ip_address}:{self.port_pub}")
                self.logger.info(f'Disconnecting Publisher')
        except Exception as e:
            self.logger.error(f'Error closing Publisher connection: {str(e)}')
        try:
            if(self.replier):
                self.replier.unbind(f"tcp://{self.ip_address}:{self.port_rep}")
                self.logger.info(f'Disconnecting Replier')
        except Exception as e:
            self.logger.error(f'Error closing Replier connection: {str(e)}')
        
        if self.context is not None:
            self.context.destroy()
            self.context = None

    def disconnect(self):
        """Stops main loop and close all sockets"""
        self._stop()
        self._close_connection()
        self.logger.info(f'Server Disconnecting')
    
    def _pub_status(self) -> datetime:
        """Publishes status via ZeroMQ

        Returns
        -------
        datetime
            Time when the pub occurred
        """
        self.status["timestamp"] = datetime.isoformat(datetime.now(), timespec='milliseconds')              # Sets status timestamp
        json_string = json.dumps(self.status)                                                               # Serializes the current Status in a JSON formatted string
        try:      
            self.publisher.send_string(json_string)                                                         # Publishes Status JSON string
            self.logger.info(f'Status published: {self.status}')                                            # If no error occurred while publishing logs the published JSON string
            return datetime.now()
        except Exception as e:
            self.logger.error(f'Error: {str(e)}')
    
    def _stop(self):
        """Stop main loop and unregister zmq.POLL"""
        self._stop_var = True
        if self.poller:
            self.poller.unregister(self.replier)
            self.poller = None
            time.sleep(.2)
    
    def ping_server(self):                      # TODO: Trocar nome da função para "ping_motor"
        """Check if motor is reachable
        ::returns:: bool
        """
        response = ping(Config.device_ip, count=1, timeout=0.6)
        if(response.success()):
            return True
        else:
            return False

    def ping_router(self):
        """Check if router is reachable
        ::returns:: bool
        """
        response = ping(Config.router_ip, count=1, timeout=0.6)
        if(response.success()):
            return True
        else:
            return False

    def handle_home(self):
        """Executes the INIT routine, which means moving motor axis to the
        microswitches and then removing the backlash until the encoder return 0"""
        try:
            self.communicating_to_motor = True
            res = self.device.home()
            self.communicating_to_motor = False
            time.sleep(.1)
            if res == "OK":
                self._homing = True
                self._is_busy = True
            else:
                self.status["alarm"] = self.device.alarm
            self.logger.info(f'Device Homing {res}')
        except Exception as e:
            self.communicating_to_motor = False
            self.status["alarm"] = self.device.alarm
            self.status["error"] = str(e)
            self.logger.error(f'Homing {e}')
            self._pub_status()

    def handle_halt(self):
        """Stops the motor"""
        self.communicating_to_motor = True
        if self.device.Halt():
            self.communicating_to_motor = False
            time.sleep(.1)
            self._is_busy = True # set _is_moving to true so the main loop can realy check if the motor is moving or not  #TODO: Verificar o motivo disso ser necessário
            self.logger.info(f'Device Stopped')
        else:
            self.communicating_to_motor = False
            self.status["alarm"] = self.device.alarm
            self.logger.info(f'Halt Fail')

    def handle_speed(self, vel):
        """Change the motor's speed"""
        if vel > Config.max_speed:
            vel = Config.max_speed
        elif vel <=0:
            vel = Config.max_speed
        try:
            self.communicating_to_motor = True
            if self.device.speed(vel):
                self.communicating_to_motor = False
                time.sleep(.1)
                self.logger.info(f'Speed changed')
            else:
                self.communicating_to_motor = False
                self.logger.info(f'Speed change Fail')
        except Exception as e:
            self.communicating_to_motor = False
            self.logger.error(f"Error speed {str(e)}")

    def handle_connect(self):
        """(Deprecated) - Self explained"""
        self.logger.info(f'Device Connected')
        self.communicating_to_motor = True
        self.device.position
        self.communicating_to_motor = False
        self._pub_status()

    def handle_disconnect(self):
        """(Deprecated) - Self explained"""
        self.logger.info(f'Device Disconnected')
    
    def handle_in_out(self, direction, speed):  #TODO: Talvez colocar uma velocidade default
        """Move focuser to a position
        Args: 
            direction (int): 1 for IN, 0 for OUT.
            speed microns/s(integer)
        """   
        try:
            self.communicating_to_motor = True
            if int(speed) != Config.max_speed:
                self.handle_speed(int(speed))
            if direction == 1:
                # FOCUS IN
                self.device.focus_in_out(int(direction))
                self.logger.info(f'Moving FOCUSIN')
            elif direction == 0:
                # FOCUS OUT
                self.device.focus_in_out(int(direction))
                self.logger.info(f'Moving FOCUSOUT')
            time.sleep(.1)
            self._is_busy = True
            self.communicating_to_motor = False
        except Exception as e:
            self.communicating_to_motor = False
            self.status["alarm"] = self.device.alarm
            self.status["error"] = str(e)
            self.logger.error(f'Moving FOCUS IN | OUT')
            self._pub_status()

    def handle_move(self, pos, speed):
        """Move focuser to a position
        Args: 
            position microns (integer)
            speed microns/s(integer)
        """   
        try:
            self.communicating_to_motor = True
            self.device.move(int(pos))
            self.communicating_to_motor = False
            self.logger.info(f'Moving to {pos} position')
            time.sleep(.1)
            self._is_busy = True
        except Exception as e:
            self.communicating_to_motor = False
            self.status["alarm"] = self.device.alarm
            self.status["error"] = str(e)
            self.logger.error(f'Moving {pos}: {str(e)}')
            self._pub_status()

    def _update_status(self):
        """Verifies if there is a change in state variables, 
        such as _is_moving, _homing and _position and publishes in ZeroMQ"""
        if self._position != self.previous_pos:
            self.status["position"] = self._position
            self.previous_pos = self._position
            self._flag_change = True
            # self._pub_status()
            self.encoder = int(self._position * Config.enc_2_microns)

        if self.is_moving != self.previous_is_mov:
            self.status["isMoving"] = self.is_moving
            self.previous_is_mov = self.is_moving 
            self.status["initialized"] = self.device.initialized
            self._flag_change = True
            # self._pub_status()

        if self._homing != self.previous_homing:
            self.status["homing"] = self._homing            
            self.previous_homing = self._homing
            self._flag_change = True
            # self._pub_status()
        
        self._read_motor_status()               # Issues command to read the current motor status.

        if self._flag_change:   # Publishes in 0MQ if a change occurred
            self._flag_change = False
            self._pub_status()

        # if self._is_moving and self._homing:
        #     self.status["clientId"] = 0

    def reply(self, msg):
        self.replier.send_string(msg)

    @property
    def clientID(self):
        return self._client_id
    @clientID.setter
    def clientID(self, ID: int):
        self._client_id = ID
        if ID != 0:
            self._signal_client_id.emit(str(ID))
        else:
            self._signal_client_id.emit("")

    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, value: int):
        self._position = value
        self._signal_position.emit(str(value))

    @property
    def encoder(self):
        return self._encoder
    @encoder.setter
    def encoder(self, value: int):
        self._encoder = value
        self._signal_encoder.emit(str(value))

    @property
    def router_reachable(self):
        return self._router_reachable
    @router_reachable.setter
    def router_reachable(self, value: bool):
        self._router_reachable = value
        # self._signal_router_reachable_bool.emit(value)
        self._signals_router.status.emit(value)

    @property
    def motor_reachable(self):
        return self._motor_reachable
    @motor_reachable.setter
    def motor_reachable(self, value: bool):
        self._motor_reachable = value
        self._signals_motor.status.emit(value)

    @property
    def server_connected(self):
        return self._server_connected
    @server_connected.setter
    def server_connected(self, value: bool):
        self._server_connected = value
        # self._signal_server_started_bool.emit(value)
        if value:
            self._signals_server.emit(value,"statusLed", "OK")
        else:
            self._signals_server.emit(value,"statusLed", "NOK")

    @property
    def communicating_to_motor(self):
        return self._communicating_to_motor
    @communicating_to_motor.setter
    def communicating_to_motor(self, value: bool):
        self._communicating_to_motor = value
        self._signal_communicating_to_motor_bool.emit(value)
        if value:
            self._statusBar_led.emit(QPixmap(icon_con_ok))
        else:
            if (not self.motor_reachable) or (self._server_connected is False):
                self._statusBar_led.emit(QPixmap(icon_con_nok))
            else:
                self._statusBar_led.emit(QPixmap(icon_con_wait))

    @property
    def transaction_id(self):
        return self._transaction_id
    @transaction_id.setter
    def transaction_id(self, value: int):
        self._transaction_id = value
        self._signal_transaction_id.emit(str(value))
    

    @property
    def is_moving(self):
        return self._is_moving
    @is_moving.setter
    def is_moving(self, value: bool):
        self._is_moving = value
        if value:
            # self._signal_moving_status.emit(QPixmap(icon_con_ok))
            # self._signal_moving_status.emit("statusLed", "OK")
            self._signals_moving.emit(value, "statusLed", "OK")
        else:
            # self._signal_moving_status.emit(QPixmap(icon_con_nok))
            # self._signal_moving_status.emit("statusLed", "NOK")
            self._signals_moving.emit(value, "statusLed", "NOK")

    @property
    def status_lim_minus(self):
        return self._status_lim_minus
    @status_lim_minus.setter
    def status_lim_minus(self, value: bool):
        self._status_lim_minus = value
        if value:
            self._signals_lim_min.emit(value, "statusLed", "OK")
        else:
            self._signals_lim_min.emit(value, "statusLed", "NOK")

    @property
    def status_lim_max(self):
        return self._status_lim_max
    @status_lim_max.setter
    def status_lim_max(self, value: bool):
        self._status_lim_max = value
        if value:
            self._signals_lim_max.emit(value, "statusLed", "OK")
        else:
            self._signals_lim_max.emit(value, "statusLed", "NOK")

    def run(self):
        """Server Main Loop
        
        The server main loop is responsible for:
        - Receiving commands from clients
        - Publishing status
        - Checking connectivity status
        """
        self._client_id = 0                                         # Starts client not busy
        command_handlers = {                                        # Handles for the methods to be executed according to the commands
            'HOME': self.handle_home,
            'HALT': self.handle_halt,
            'CONNECT': self.handle_connect,
            'DISCONNECT': self.handle_disconnect,
            'STATUS': self._pub_status,
        }
        self.start_server()                                         # Starts the ZMQ server and publishes the current status
        self._stop_var = False                                       # Initializes variable used that keep the thread loop running
        self.status["connected"] = self.device.connected            # Reads "_connected" from the motor
        while not self._stop_var:                                    # Start of the thread loop
            t0 = time.time()                                        # Keeps the time when the loop began
            current_time = datetime.now()                           # Reads current time

            self._signal_firmware_status.emit(self.device.get_firmware_status())

            # if -1 >= (current_time.second - self.last_pub.second) or (current_time.second - self.last_pub.second) >= 1:       #TODO: Não daria pra só checar se o valor absoluto for >= 1?
            if abs(current_time.second - self.last_pub.second) >= 1:                                                            # Updates position and publishes status every 1 second
                # self.device.position 
                self.position = self.device.position                                                                            # Reads motor current position
                self.status["position"] = self.position
                self.last_pub = self._pub_status()                                                                              # Publishes status  #TODO: Não adianta atualizar "_position" se não colocar em "Status" para publicar
                # self.last_pub = current_time                                                                                    # Updates las publish moment
            if self.device and self.device.connected and self.poller:                                                           # Continues the loop if the device is configured and connected and the poller is configured
                socks = dict(self.poller.poll(50))                                                                              # Polls the information from the ZMQ to receive commands from the client
                if socks.get(self.replier) == zmq.POLLIN:                                                                       # If the socket is configured as Pollin   #TODO: Necessário?
                    msg_rep = self.replier.recv_string()                                                                        # Receives the JSON from the client
                    try:
                        msg_rep = json.loads(msg_rep)                                                                           # Deserializes the JSON
                        cmd = msg_rep.get("action")                                                                             # Reads the "action" from the JSON
                        if not 'STATUS' in cmd and (msg_rep.get("clientId") == self._client_id or self._client_id == 0):        #TODO: Definir melhor os comandos que podem ser executados quando o dispositivo está ocupado        
                            # Only accept commands (except for status request) if not busy or if it 
                            # was requested by the same client
                            self.status["cmd"] = msg_rep                                                                        # Reads the "cmd" from the JSON
                            # self._client_id = msg_rep.get("clientId")                                                           # Reads the "clientID" from the JSON
                            self.clientID = msg_rep.get("clientId")
                            self.transaction_id = msg_rep.get("clientTransactionId")
                    except Exception as e:
                        print(e)
                        self.reply('NAK')                                                                                       # If an error occurred during the reading of the JSON return 'NAK' to the client
                    try:
                        # Handle all possible commands
                        self.status["error"] = ""                                                                               # Resets "error" status

                        command_processed = False                                                                               # Initializes "command_processed"

                        if "MOVE=" in cmd and self.busy_id == 0:                                                                # If the server is not busy and received the command "MOVE"
                            self.handle_move(cmd[5:], Config.max_speed)                                                         # Calls function to handle move with the desired position and default speed
                            self.reply('ACK')                                                                                   # Return 'ACK' to the client
                            command_processed = True                                                                            # Sets "command_processed"

                        if "FOCUSIN" in cmd and self.busy_id == 0:                                                              # If the server is not busy and received the command "FOCUSIN"
                            self.handle_in_out(1, cmd[8:])                                                                      # Calls the function to handle FOCUSIN and FOCUSOUT with '1' to select FOCUSIN
                            self.reply('ACK')                                                                                   # Return 'ACK' to the client
                            command_processed = True                                                                            # Sets "command_processed"

                        if "FOCUSOUT" in cmd and self.busy_id == 0:                                                             # If the server is not busy and received the command "FOCUSOUT"
                            self.handle_in_out(0, cmd[9:])                                                                      # Calls the function to handle FOCUSIN and FOCUSOUT with '0' to select FOCUSOUT    
                            self.reply('ACK')                                                                                   # Return 'ACK' to the client            
                            command_processed = True                                                                            # Sets "command_processed"            

                        if "HALT" in cmd and (self._client_id == self.busy_id or self.busy_id == 0):                            # If the server is not busy or the client is the same previously connected and the command "HALT" is received                            
                            self.handle_halt()                                                                                  # Calls the function that handles "HALT"        
                            self.reply('ACK')                                                                                   # Return 'ACK' to the client                    
                            command_processed = True                                                                            # Sets "command_processed"                 

                        if cmd in command_handlers and self.busy_id == 0:                                                       # If server not busy and other command is received              #TODO: O comando HALT está tanto no "command_handlers" quanto no `if` acima
                            command_handlers[cmd]()                                                                             # Calls the appropriate function to handle the received command #TODO: Todoas as funções podem ser chamadas dessa forma 
                            self.reply('ACK')                                                                                   # Return 'ACK' to the client 
                            command_processed = True                                                                            # Sets "command_processed"

                        if not command_processed:                                                                               # If command was NOT processed
                            self.reply('NAK')                                                                                   # Return 'NAK' to client

                        self.status["connected"] = self.device.connected                                                        # Updates connection status of the motor

                    except Exception as e:                                                                                      # If an exception occurs during the handling of the command 
                        self._pub_status()                                                                                       # Published current status
                        self.logger.error(f'Error: {str(e)}')                                                                   # Logs error


                self._check_motor_moving()                  # Verifies if the motor is moving as expected.
                                          
                                           
                                           
                                                                                               # Updates motor position             
                if self._homing:                                # (self._homing == True) indicates that the homing was not performed
                    self._homing = self.device.homing           # This means that while the homing is not performed this will keep checking if it was performed        #TODO: Qual o motivo de `_homing` ter que ser `true` para chamar `device.homing` para checar se está executando a rotina de inicialização?
                if not self._homing and not self._is_moving:    # (self._homing == False) indicates that the homing was performed
                                                                # The homing was performed and the motor is not moving -> Indicates the motor is not busy
                    self.clientID = 0                         # Sets client not busy
                    self.status["cmd"] =  {                     # Resets "cmd" 
                                            "clientId": self._client_id,                #TODO: Esse valor pode ser 0? Checar arquivo do Ramon e documentação Alpaca. Talvez o 0 seja reservado para "not busy"
                                            "clientTransactionId": 0,                   
                                            "clientName": "",
                                            "action": ""
                                            }                    
                
                # self._position = self.device.position
                self.busy_id = self.clientID                                              # Keeps the ID of the client that sent the last command
                self._update_status()                                                        # Updates motor readings and publishes the current status to ZMQ             
                self.status["alarm"] = 0                                                    # Resets "alarm"
                self.communicating_to_motor = False
            else:                                                                       # If the device is not configured or not connected or the poller is not configured              
                # if (abs(current_time.second - self.last_ping_time.second) >= 5) or (self._router_reachable is False):           # Runs every 5 seconds
                # if self._router_reachable is False:
                self.router_reachable = self.ping_router()                                                                     # Updates if router is reachable      #INFO: self.reach_device() já faz esses dois
                self.motor_reachable = self.ping_server()                                                                      # Updates if moto is reachable
                self.reach_device()                                                                                             # Tries to reach device
                
                self.status["connected"] = self.device.connected                                                                # Updates "connected" state
                self._statusMessage.emit("")                                                                                    # Clears status message
            # self.connection_speed = f"interval:  {round(time.time()-t0, 3)}"                                                # Calculates time to run thread loop
            self._connection_speed.emit(f"{round(time.time()-t0, 3)}")      
    #----Code that needs to be executed when the server is disconnected
        # Updates signals status
        self.server_connected = False
        self._signals_motor_connection("waiting")
        self._signals_router_connection("waiting")
        self.communicating_to_motor = False
        self._connection_speed.emit(" ")                                                                                   # Clears connection speed value message


    def _check_motor_moving(self):
        """Verifies if the motor is moving as expected.
        If the motor is indicating that it should be moving but the position 
        is not changing between reads than a 'timeout' must be issued.
        If a 'timeout' occurs the servers issues a 'halt' command to the motor.

        Raises
        ------
        Exception
            Informs that the motor is stalled
        """
        if self.is_moving:                             #TODO: Qual o motivo de `_is_moving` ter que ser `true` para chamar `device.is_moving` para checar se está em movimento?
            try:
                self._read_motor_status()    
                pos_delta = self.position - self.device.position
                if pos_delta == 0 and self.status_lim_minus == False:                                                      # If the driver says the motor is moving but there is no change in position reading than the motor is stalled
                    # raise AlpacaExceptions.DriverException(1300, "Stalled Motor")       # Raises exception according to Alpaca      #TODO: Definir direito o código e a mensagem

                    print("Stalled Motor")   
                    _loop_count = 0                                                         # TODO: Isso pode ser configurável
                    while self.is_moving and _loop_count < 5:                               # If a stall occurs the server issues a 'halt' command and verifies if the motor responds as expected
                        self.handle_halt()
                        self.reply('ACK')
                        self._read_motor_status()                                           # Issues command to read the current motor status.
                        _loop_count+=1
                    if _loop_count == 5:
                        raise Exception("Motor is stalled and driver didn't respond to stop command after 5 tries")
                    self.status["timeout"]= True
                    self._pub_status()

                # Resets status. Required to accept new commands
                    self._homing = False
                    self._is_busy = False
                    self.clientID = 0                         # Sets client not busy
                    self.status["cmd"] =  {                     # Resets "cmd" 
                                            "clientId": self._client_id,                #TODO: Esse valor pode ser 0? Checar arquivo do Ramon e documentação Alpaca. Talvez o 0 seja reservado para "not busy"
                                            "clientTransactionId": 0,                   
                                            "clientName": "",
                                            "action": ""
                                            }         

                else:
                    self.position = self.device.position
                    self.status["timeout"] = False
                    self._pub_status()   
            except Exception as e:                                                      # At this point could the exception also be due to a communication issue?
                                                                                     # If an exception occurs during the handling of the command 
                self._pub_status()                                                                                       # Published current status
                self.logger.error(f'Error: {str(e)}')                                                                   # Logs error



    def _read_motor_status(self):
        """Issues command to read the current motor status.
        """
        try:
            resp = format(int(self.device.motor_status), '012b')        # TODO: Ver um jeito de converter para binário sem ser string
            motor_status = "".join(reversed(resp))                          # This is only done so that the bit order is as shown in table 7 of the manual of the motor (DMX-ETH)
            # print(motor_status)


            if(motor_status[0] == '1'):        
                self.is_moving = True
            else:
                self.is_moving = False

            if(motor_status[4] == '1'):        
                self.status_lim_minus = True
            else:
                self.status_lim_minus = False

            if(motor_status[5] == '1'):        
                self.status_lim_max = True
            else:
                self.status_lim_max = False
            


        except Exception as e:                                              # TODO: Verificar o que tem que ser feito se não conseguir obter essa informação 
            print(e)


    def reset_timeout(self):
        self.status["timeout"] = False


#=== Methods to pass signals ===#
    def _signals_router_connection(self, status: str):
        """Updates the signals related to the router connection

        Parameters
        ----------
        status : str
            waiting -> not connected
            connecting -> not connected and trying to connect
            connected -> connected
        """
        if status == "connected":
            self._signals_router.info.emit("conStatusBar", "connected")
            self._signals_router.info.emit("statusLed", "OK")
            self.router_reachable = True
        else:
            self._signals_router.info.emit("conStatusBar", status)      # status = "connecting" or "waiting"
            self._signals_router.info.emit("statusLed", "NOK")
            self.router_reachable = False

    def _signals_motor_connection(self, status: str):
        """Updates the signals related to the motor connection

        Parameters
        ----------
        status : str
            waiting -> not connected
            connecting -> not connected and trying to connect
            connected -> connected
        """
        if status == "connected":
            self._signals_motor.info.emit("conStatusBar", "connected")
            self._signals_motor.info.emit("statusLed", "OK")
            self.motor_reachable = True
        else:
            self._signals_motor.info.emit("conStatusBar", status)      # status = "connecting" or "waiting"
            self._signals_motor.info.emit("statusLed", "NOK")
            self.motor_reachable = False

    def _signals_communicating_to_motor(self, status: bool):
        self._communicating_to_motor.emit(status)
        if status:
            self._statusBar_led.emit(QPixmap(icon_con_ok))
        else:
            if (not self.motor_reachable) or (self._server_connected is False):
                self._statusBar_led.emit(QPixmap(icon_con_nok))
            else:
                self._statusBar_led.emit(QPixmap(icon_con_wait))