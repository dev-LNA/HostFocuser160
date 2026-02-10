# app.py - Connections to Sockets (ZeroMQ) an control management
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

from PyQt6.QtCore import pyqtSignal, QObject

from logging import Logger

import time
import zmq
import json
import socket
from datetime import datetime
from pythonping import ping

from src.core.config import Config

from src.interface.dmx_eth import FocuserDriver as Focuser

class App(QObject):

    _router_con_status = pyqtSignal(str, str)
    _motor_con_status = pyqtSignal(str, str)

    _server_started_status = pyqtSignal(str, str)
    _server_started_bool = pyqtSignal(bool)

    _statusMessage = pyqtSignal(str)

    _router_reachable = False
    _motor_reachable  = False

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
        self._position = 0
        self._homing = False
        self._stopping = False
        self._client_id = 0
        self.busy_id = 0
        self._current_speed = Config.max_speed
        self.encoder = 0

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
        
        self.device = Focuser(self.logger)

    # Reaching the device and starting the server at this point is not necessary        
        # self.reach_device()
        # self.start_server()

    def reach_device(self):
        """Ping device and reads the position and initialized variables"""
        _try = 0
        self.last_ping_time = datetime.now()

        if not self._router_reachable:
            self._signals_router_connection("connecting")
            self._signals_motor_connection("waiting")
            
            
            for _try in range(5):
                print(f"Trying Connect to Router: Try number {_try+1}")
                self._statusMessage.emit(f"Trying Connect to Router: Try number {_try+1}")
                self._router_reachable = self.ping_router()
                if self._router_reachable:
                    print("Connection succesfull after", (_try+1), "tries" )
                    self._statusMessage.emit(f"Connection succesfull after {_try+1} tries")
                    self._signals_router_connection("connected")
                    break


        if self._router_reachable:
            self._signals_router_connection("connected")
            self._signals_motor_connection("connecting")
            
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
                    self._position =self.device.position
                    self.status["position"] = self._position
                    self.status["initialized"] = self.device.initialized
                    self.status["device_IP"] = self.device.get_device_IP
                    self.status["device_ID"] = self.device.get_device_ID
                    self.status["device_Firmware_Version"] = self.device.get_device_Firmware_Version
                    
                    self.logger.info(f'Device Reached.')
                except Exception as e:
                    self.logger.error(f'Error reaching device: {str(e)}') 


    def _signals_router_connection(self, status: str):
        """Updates the signals related to the router connection

        Parameters
        ----------
        status : str
            waiting -> not connected
            connecting -> not connected and trying to connect
            connected -> connected
        """
        if status is "connected":
            self._router_con_status.emit("conStatusBar", "connected")
            self._router_con_status.emit("statusLed", "OK")
        elif status is "connecting":
            self._router_con_status.emit("conStatusBar", "connecting")
            self._router_con_status.emit("statusLed", "NOK")
        else:
            self._router_con_status.emit("conStatusBar", "waiting")
            self._router_con_status.emit("statusLed", "NOK")

    def _signals_motor_connection(self, status: str):
        """Updates the signals related to the motor connection

        Parameters
        ----------
        status : str
            waiting -> not connected
            connecting -> not connected and trying to connect
            connected -> connected
        """
        if status is "connected":
            self._motor_con_status.emit("conStatusBar", "connected")
            self._motor_con_status.emit("statusLed", "OK")
        elif status is "connecting":
            self._motor_con_status.emit("conStatusBar", "connecting")
            self._motor_con_status.emit("statusLed", "NOK")
        else:
            self._motor_con_status.emit("conStatusBar", "waiting")
            self._motor_con_status.emit("statusLed", "NOK")

    def _signals_server_connection(self, status: bool):
        """Updates the signals related to the server connection

        Parameters
        ----------
        status : bool
            True -> Server initialized
            False -> Server not initialized
        """
        self._server_started_bool.emit(status)
        if status:
            self._server_started_status.emit("statusLed", "OK")
        else:
            self._server_started_status.emit("statusLed", "NOK")

       

    def start_server(self): 
        """ Starts Server ZeroMQ, creating context 
        then binding PUB and REP sockets"""

        if self.context:                                                                # If context already created returns
            self._signals_server_connection(True)
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
            self._signals_server_connection(False)
            return

        try:
            # Command REP
            self.replier = self.context.socket(zmq.REP)                                 # Creates REP
            self.replier.bind(f"tcp://{self.ip_address}:{self.port_rep}")               # Binds REP to * IP adress and configured REP port
            print(f"REP binded to {self.ip_address}:{self.port_rep}")
        except Exception as e:
            self.logger.error(f'Error Binding Replier: {str(e)}')
            self._signals_server_connection(False)
            return

        # Poller
        self.poller = zmq.Poller()                                                      # Creates Poller
        self.poller.register(self.replier, zmq.POLLIN)                                  # Register poller to monitoring REP
        self.logger.info(f'Server Started')
        self._pub_status()                                                               # Publishes current status to ZMQ
        self._signals_server_connection(True)
        
    
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

    # Updates signals status
        self._signals_server_connection(False)
        self._signals_motor_connection("waiting")
        self._signals_router_connection("waiting")

        self.logger.info(f'Server Disconnecting')
    
    def _pub_status(self):
        """Publishes status via ZeroMQ"""
        self.status["timestamp"] = datetime.isoformat(datetime.now(), timespec='milliseconds')              # Sets status timestamp
        json_string = json.dumps(self.status)                                                               # Serializes the current Status in a JSON formatted string
        try:      
            self.publisher.send_string(json_string)                                                         # Publishes Status JSON string
            self.logger.info(f'Status published: {self.status}')                                            # If no error occurred while publishing logs the published JSON string
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
            res = self.device.home()
            time.sleep(.1)
            if res == "OK":
                self._homing = True
                self._is_moving = True
            else:
                self.status["alarm"] = self.device.alarm
            self.logger.info(f'Device Homing {res}')
        except Exception as e:
            self.status["alarm"] = self.device.alarm
            self.status["error"] = str(e)
            self.logger.error(f'Homing {e}')
            self._pub_status()

    def handle_halt(self):
        """Stops the motor"""
        if self.device.Halt():
            time.sleep(.1)
            self._is_moving = True # set _is_moving to true so the main loop can realy check if the motor is moving or not  #TODO: Verificar o motivo disso ser necessário
            self.logger.info(f'Device Stopped')
        else:
            self.status["alarm"] = self.device.alarm
            self.logger.info(f'Halt Fail')

    def handle_speed(self, vel):
        """Change the motor's speed"""
        if vel > Config.max_speed:
            vel = Config.max_speed
        elif vel <=0:
            vel = Config.max_speed
        try:
            if self.device.speed(vel):
                time.sleep(.1)
                self.logger.info(f'Speed changed')
            else:
                self.logger.info(f'Speed change Fail')
        except Exception as e:
            self.logger.error(f"Error speed {str(e)}")

    def handle_connect(self):
        """(Deprecated) - Self explained"""
        self.logger.info(f'Device Connected')
        self.device.position
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
            self._is_moving = True
        except Exception as e:
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
            self.device.move(int(pos))
            self.logger.info(f'Moving to {pos} position')
            time.sleep(.1)
            self._is_moving = True
        except Exception as e:
            self.status["alarm"] = self.device.alarm
            self.status["error"] = str(e)
            self.logger.error(f'Moving {pos}: {str(e)}')
            self._pub_status()

    def update_status(self):
        """Verifies if there is a change in state variables, 
        such as _is_moving, _homing and _position and publishes in ZeroMQ"""
        if self._position != self.previous_pos:
            self.status["position"] = self._position
            self.previous_pos = self._position
            self._flag_change = True
            # self._pub_status()
            self.encoder = int(self._position * Config.enc_2_microns)

        if self._is_moving != self.previous_is_mov:
            self.status["isMoving"] = self._is_moving
            self.previous_is_mov = self._is_moving 
            self.status["initialized"] = self.device.initialized
            self._flag_change = True
            # self._pub_status()

        if self._homing != self.previous_homing:
            self.status["homing"] = self._homing            
            self.previous_homing = self._homing
            self._flag_change = True
            # self._pub_status()
        
        # resp = format(int(self.device.get_motor_status), '012b')        # TODO: Ver um jeito de converter para binário sem ser string
        # motor_status = "".join(reversed(resp))                          
        # print(motor_status)
        
        # if(motor_status[0] == '1'):                                   # TODO: Adicionar lógica para mostrar o status atual do motor e substituir pela lógica atual
        #     print("motor em movimento")
        # else:
        #     print("motor parado")
        # if(motor_status[1] == '1'):
        #     print("motor acelerando")
        # if(motor_status[2] == '1'):
        #     print("motor desacelerando")

        if self._flag_change:   # Publishes in 0MQ if a change occurred
            self._flag_change = False
            self._pub_status()

        # if self._is_moving and self._homing:
        #     self.status["clientId"] = 0

    def reply(self, msg):
        self.replier.send_string(msg)

    def run(self):
        """Main Loop"""
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
            # if -1 >= (current_time.second - self.last_pub.second) or (current_time.second - self.last_pub.second) >= 1:       #TODO: Não daria pra só checar se o valor absoluto for >= 1?
            if abs(current_time.second - self.last_pub.second) >= 1:                                                            # Updates position and publishes status every 1 second
                # self.device.position 
                self._position = self.device.position                                                                           # Reads motor current position
                self._pub_status()                                                                                               # Publishes status  #TODO: Não adianta atualizar "_position" se não colocar em "Status" para publicar
                self.last_pub = current_time                                                                                    # Updates las publish moment
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
                            self._client_id = msg_rep.get("clientId")                                                           # Reads the "clientID" from the JSON
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

                if self._is_moving:                             #TODO: Qual o motivo de `_is_moving` ter que ser `true` para chamar `device.is_moving` para checar se está em movimento?
                    self._is_moving = self.device.is_moving                                                                     # Checks if the motor is in movement        #TODO: Na verdade está checando se alguma função está sendo executada no motor
                    time.sleep(.05)
                    self._position = self.device.position                                                                       # Updates motor position             
                if self._homing:                                # (self._homing == True) indicates that the homing was not performed
                    self._homing = self.device.homing           # This means that while the homing is not performed this will keep checking if it was performed        #TODO: Qual o motivo de `_homing` ter que ser `true` para chamar `device.homing` para checar se está executando a rotina de inicialização?
                if not self._homing and not self._is_moving:    # (self._homing == False) indicates that the homing was performed
                                                                # The homing was performed and the motor is not moving -> Indicates the motor is not busy
                    self._client_id = 0                         # Sets client not busy
                    self.status["cmd"] =  {                     # Resets "cmd" 
                                            "clientId": self._client_id,                #TODO: Esse valor pode ser 0? Checar arquivo do Ramon e documentação Alpaca. Talvez o 0 seja reservado para "not busy"
                                            "clientTransactionId": 0,                   #TODO: Esse valor pode ser 0? Checar arquivo do Ramon e documentação Alpaca. Talvez o 0 seja reservado para "not busy"
                                            "clientName": "",
                                            "action": ""
                                            }                    
                
                # self._position = self.device.position
                self.busy_id = self._client_id                                              # Keeps the ID of the client that sent the last command
                self.update_status()                                                        # Updates motor readings and publishes the current status to ZMQ             
                self.status["alarm"] = 0                                                    # Resets "alarm"
                                                    
            else:                                                                       # If the device is not configured or not connected or the poller is not configured              
                if (abs(current_time.second - self.last_ping_time.second) >= 5) or (self._router_reachable is False):           # Runs every 5 seconds
                    self._router_reachable = self.ping_router()                                                                     # Updates if router is reachable      #INFO: self.reach_device() já faz esses dois
                    self._motor_reachable = self.ping_server()                                                                      # Updates if moto is reachable
                    self.reach_device()                                                                                             # Tries to reach device
                self.status["connected"] = self.device.connected                                                                # Updates "connected" state
                self._statusMessage.emit("")                                                                                    # Clears status message
            self.connection_speed = f"interval:  {round(time.time()-t0, 3)}"                                                # Calculates time to run thread loop

