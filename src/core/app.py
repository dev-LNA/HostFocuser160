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
from datetime import datetime
# from pythonping import ping
from icmplib import ping
from os import path
import sys

from misc.client_sample import TEST_SETUP
from src.core.config import Config
import src.core.exceptions as AlpacaExceptions
from src.utils.constants import constants
from src.utils.signals import PropertySignals

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
    _signal_position_str = pyqtSignal(str)
    _signal_position_int = pyqtSignal(int)
    _signal_encoder = pyqtSignal(str)
    
    _signal_firmware_status = pyqtSignal(str)

    _signals_moving = PropertySignals()
    _signals_lim_min = PropertySignals()
    _signals_lim_max = PropertySignals()
    _signals_initialized = PropertySignals()
    _signals_parking = PropertySignals()

    _signal_max_pos = pyqtSignal(int)
    _signal_backlash = pyqtSignal(int)

    _signals_server = PropertySignals()


    _signal_last_command = pyqtSignal(dict)


    

    def __init__(self, logger: Logger):
        super(App, self).__init__()
        self.logger = logger                            # Instantiates logger
    
        # Network Settings
        self.context = None                             #|
        self.ip_address = Config.ip_address             #|
        self.port_pub = Config.port_pub                 #|  Network settings initialization
        self.port_rep = Config.port_rep                 #|
        self.poller = None                              #|
        self.connection_speed = 0                       #|

        # Control variables
        self._stop_var = False                          #|
        self.previous_is_mov = False                    #|
        self.previous_homing = False                    #|
        self.previous_initialized = False               #|
        self.previous_parking = False                   #|  Control variables initialization
        self.previous_pos = 0                           #|
        self.last_ping_time = datetime.now()            #|
        self.last_pub = datetime.now()                  #|
        self._flag_change = False                       #|

        # Variables for status request
        self._is_moving = False                         #|
        self._is_busy = False                           #|
        self._position = 0                              #|
        self._homing = False                            #|
        self._parking = False                           #| 
        self._initialized = False                       #|
        self._stopping = False                          #|  Status initialization
        self._client_id = 0                             #|
        self.busy_id = 0                                #|
        self._current_speed = Config.max_speed          #|
        self._encoder = 0                               #|
        self._status_lim_minus = False                  #|
        self._status_lim_max = False                    #|
        self._transaction_id = 0                        #|
        self.router_reachable = False                   #|
        self.motor_reachable = False                    #|

        # Status Message
        if TESTE_TCSPD:                                 #TEST: O json do tcspd não está atualizado então é necessário usar o antigo para testar com o tcspd
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
                "version": "1.0.0",            #TODO: Pegar a versão do arquivo config.toml
            }
        else:
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
                "version": "1.0.0",            #TODO: Pegar a versão do arquivo config.toml
                "parking": False,               # Executing Parking
                "device_IP": "127.0.0.1",       # Motor IP
                "device_ID": "",                # Motor ID
                "device_Firmware_Version": "",  # Motor firmware version
                "timeout": False,               # Timeout
            }

        self.device = None              # Initiates motor as None


#----TESTES #TEST
    def _testes(self):        
        self.device.acionar()
    
        # num_bits = self.device._conv_num_bits(-123456789,32)
        # high = num_bits[16:]
        # low = num_bits[:16]
        # print(high)
        # print(low)

        # self.device.mb_server.server.data_bank.set_discrete_inputs(825, high)
        # self.device.mb_server.server.data_bank.set_discrete_inputs(825+16, low)




#----TESTES
    def init_device(self, motor_model: str):
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
        if self.device == None:                                                         # If motor was not instantiated
            if motor_model == constants.ARCUS_DMX_ETH:                                      # Checks motor model
                from src.interface.driver_dmx_eth import FocuserDriver as Focuser               # If motor is Arcus DMX-ETH imports 'driver_dmx_eth'
            elif motor_model == constants.AMP_MOTOR:                    
                # from src.interface.driver_amp import FocuserDriver as Focuser                   # If motor im AMP imports 'driver_amp'
                from src.interface.driver_amp_modbus import FocuserDriver as Focuser                   # If motor im AMP imports 'driver_amp_modbus'
            
            self.device = Focuser(self.logger, motor_model)                                 # Instantiates the motor according to the selected focuser
            self.device.model = motor_model                                                 # Initiates motor model
        else:
            raise ValueError("Invalid motor model")                                         # Raises an exception if the motor value is not valid

    def reach_device(self):
        """Ping device and reads the position and initialized variables"""
        _try = 0
        self.last_ping_time = datetime.now()                                                    # Saves the time when the method was called

        if not self.router_reachable:                                                           # If the router is not reachable
            self._signals_router_connection("connecting")                                           # Emits signals for GUI update (Router attempting connection)
            self._signals_motor_connection("waiting")                                               # Emits signals for GUI update (Motor waiting)
            self.communicating_to_motor = False         # Communication to motor ended                                                     # Not communicating to the motor
                        
            for _try in range(5):                                                                   # Tries 5 times to ping the router
                # print(f"Trying Connect to Router: Try number {_try+1}")                         
                self._statusMessage.emit(f"Trying Connect to Router: Try number {_try+1}")              # Emits signals for GUI update
                self.router_reachable = self.ping_router()                                              # Tries to ping the router IP
                if self.router_reachable:                                                               # If the ping is succesful
                    # print("Connection succesfull after", (_try+1), "tries" )
                    self._statusMessage.emit(f"Connection succesfull after {_try+1} tries")                 # Emits signals for GUI update
                    # self._signals_router_connection("connected")
                    break                                                                                   # Exits for loop
        else:                                                                                   # If router already reachable
            self._signals_router_connection("connected")                                            # Emits signals for GUI update (Router connected)

        if self.router_reachable and not self.motor_reachable:                                  # If the router is reachable and the motor is not reachable
            self._signals_motor_connection("connecting")                                            # Emits signals for GUI update (Motor attempting connection)
            self.communicating_to_motor = False         # Communication to motor ended                                                     # Not communicating to the motor
            
            for _try in range(5):                                                                   # Tries 5 times to ping the router
                # print(f"Trying Connect to Motor: Try number {_try+1}")
                self._statusMessage.emit(f"Trying Connect to Motor: Try number {_try+1}")               # Emits signals for GUI update
                self._motor_reachable = self.ping_motor()                                              # Tries to ping the motor IP
                if self._motor_reachable:                                                               # If the ping is successful
                    # print("Connection succesfull after", (_try+1), "tries" )
                    self._statusMessage.emit(f"Connection succesfull after {_try+1} tries")                 # Emits signals for GUI update
                    break                                                                                   # Exits for loop
            
        if self.motor_reachable:                                                                # If the motor is reachable
            self._signals_router_connection("connected")                                            # Emits signals for GUI update
            self._signals_motor_connection("connected")                                             # Emits signals for GUI update
                            
            try:
                self.device.connected = True                                                        # Creates the socket and connects the server to the motor
                self.position =self.device.position                                                 # Reads current motor position
                self.status["position"] = self.position                                             # Updates status
                self.status["initialized"] = self.device.initialized                                # Updates status
                self.status["device_IP"] = self.device.device_IP                                    # Updates status
                self.status["device_ID"] = self.device.device_ID                                    # Updates status
                self.status["device_Firmware_Version"] = self.device.device_Firmware_Version        # Updates status

                self._check_homing()                                                                # Emits homing signals      #TODO: Trocar nome do método

            #--- Emits max pos and backlash to update GUI. The value is different in the test setup due to the size and gear differences
                if TEST_SETUP:
                    self._signal_max_pos.emit(int(self.device.max_pos) + 5)             # A small gap at the end to account the distance to the lim+ uswitch 
                    self._signal_backlash.emit(-(int(self.device.backlash) + 10))       # A small gap at the end to account the distance to the lim+ uswitch 
                else:
                    # TODO: Definir valores de excursão na montagem real
                    self._signal_max_pos.emit(int(self.device.max_pos))                 # A small gap at the end to account the distance to the lim+ uswitch 
                    self._signal_backlash.emit(-(int(self.device.backlash)))            # A small gap at the end to account the distance to the lim+ uswitch 
                
                self.logger.info(f'Device Reached.')
            except Exception as e:
                self.logger.error(f'Error reaching device: {str(e)}')     

    def start_server(self): 
        """ Starts Server ZeroMQ, creating context 
        then binding PUB and REP sockets"""

        if self.context:                                                                # If context already created returns
            self.server_connected = True                                                    # Updates connected value
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
        self._pub_status()                              # Publishes current status
        self.server_connected = True
        
    
    def _close_connection(self):
        """Unbind all sockets and destroy context"""
        self.device.disconnect()                                                        # Disconnects motor and closes socket
        self.status["connected"] = self.device.connected                                # Updates status
        self._pub_status()                              # Publishes current status
        try:    
            if(self.publisher):                                                         # If publisher is instantiated
                self.publisher.unbind(f"{self.publisher.last_endpoint.decode()}")           # Unbinds publisher considering last endpoint
                self.logger.info(f'Disconnecting Publisher')                                #TODO: Será que precisa fazer self.publisher = None ?
        except Exception as e:
            self.logger.error(f'Error closing Publisher connection: {str(e)}')
        try:
            if(self.replier):                                                           # If replier is instantiated
                self.replier.unbind(f"{self.replier.last_endpoint.decode()}")               # Unbinds replier considering last endpoint    
                self.logger.info(f'Disconnecting Replier')                                  #TODO: Será que precisa fazer self.replier = None ? 
        except Exception as e:
            self.logger.error(f'Error closing Replier connection: {str(e)}')
        
        if self.context is not None:                                                    # If context is instantiated
            self.context.destroy()                                                          # Destroy context
            self.context = None                                                             # Reassign context to allow for new instantiation

    def disconnect(self):
        """Stops main loop and close all sockets"""
        # self._stop()                                  # This function was separated in "stop_server_loop" and "stop_poller" to allow correct order of disconnection
        self._close_connection()                        # Closes the connection to the motor and unbinds the ZMQ sockets
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
            self.logger.debug(f'Status published: {self.status}')                                            # If no error occurred while publishing logs the published JSON string
            return datetime.now()                                                                           # Returns time after publish #TODO: Isso não é necessário
        except Exception as e:
            self.logger.error(f'Error: {str(e)}')
            return datetime.now()                                                                           #TODO: Isso não é necessário
    
    def stop_server_loop(self):
        """Sets flag to stop the execution of the server loop - stops the 'run' function"""
        self._stop_var = True                                                                               # Sets stop flag

    def stop_poller(self):
        """Unregisters the ZMQ poller"""
        if self.poller:                                         # If poller is defined
            self.poller.unregister(self.replier)                    # Unregisters poller
            self.poller = None                                      # Reassigns poller to allow new instantiation
            time.sleep(.2)                                          # Delay     #TODO: É necessário esse tempo?


    def _stop(self):
        """(Deprecated) - Use 'stop_server_loop' and 'stop_poller' separately in the correct order to avoid disconnection problems
        Stop main loop and unregister zmq.POLL"""
        self._stop_var = True
        if self.poller:
            self.poller.unregister(self.replier)
            self.poller = None
            time.sleep(.2)
    
    def ping_motor(self) -> bool:
        """Check if motor is reachable

        Returns
        -------
        bool
            True -> Motor reachable
            False -> Motor NOT reachable
        """
        return self.device.ping()       # The way the ping is realized depends on the motor

    def ping_router(self) -> bool:
        """Check if router is reachable

        Returns
        -------
        bool
            True -> Router reachable
            False -> Router NOT reachable
        """
        response = ping(Config.router_ip, count=1, timeout=0.6, privileged=False)         # Ping the motor
        if(response.is_alive):       
            return True
        else:
            return False

    def handle_home(self):
        """Executes the INIT routine, which means moving motor axis to the LIM-
        microswitch and then removing the backlash until the encoder return 0"""
        try:
            self.communicating_to_motor = True              # Communication to motor started
            res = self.device.home()                        # Sends INIT command to motor
            self.communicating_to_motor = False         # Communication to motor ended
            time.sleep(.1)                                  # Delay after command sent              #TODO: É necessário esse delay?
            if res == "OK":                                 # If the motor recognized the command
                self._homing = self.device._homing              # Updates homing state
                # self._homing = True
                self._is_busy = True                            # Motor is busy (homing)    #TODO: Mudar essa lógica do 'is_busy'
            else:
                self.logger.error(f'Device failed to start homing process')
                self.status["alarm"] = self.device.alarm    #TODO: Acho que isso não faz nada pq o ALM no DMX é só relacionado à temperatura    
        except Exception as e:      
            self.communicating_to_motor = False         # Communication to motor ended
            self.status["alarm"] = self.device.alarm        #TODO: Acho que isso não faz nada pq o ALM no DMX é só relacionado à temperatura
            self.status["error"] = str(e)                   # Sets JSON error
            self.logger.error(f'Homing {e}')
            self._pub_status()                              # Publishes current status

    def _handle_park(self):
        """Executes the PARK routine, which means running a INIT and then moving 
        the focus to a pre-defined value."""
        try:
            self.communicating_to_motor = True              # Communication to motor started
            res = self.device.park()                        # Sends PARK command to motor
            self.communicating_to_motor = False         # Communication to motor ended
            time.sleep(.1)                                  # Delay after command sent              #TODO: É necessário esse delay?
            if res == "OK":                                 # If the motor recognized the command
                self._parking = self.device._parking            # Updates parking state
                self._is_busy = True                            # Motor is busy (parking)    #TODO: Mudar essa lógica do 'is_busy'
            else:
                self.logger.error(f'Device failed to start parking process')
                self.status["error"] = "Error during parking"
        except Exception as e:
            self.communicating_to_motor = False         # Communication to motor ended
            self.status["alarm"] = self.device.alarm        #TODO: Acho que isso não faz nada pq o ALM no DMX é só relacionado à temperatura
            self.status["error"] = str(e)
            self.logger.error(f'Parking {e}')               # Sets JSON error
            self._pub_status()                              # Publishes current status


    def handle_halt(self):
        """Stops the motor movement"""
        self.communicating_to_motor = True              # Communication to motor started
        if self.device.Halt():                          # Sends HALT command to motor and if the motor recognized the command
            self.communicating_to_motor = False         # Communication to motor ended
            time.sleep(.1)                                  # Delay after command sent              #TODO: É necessário esse delay?
            self._is_busy = True                            # Motor is busy (parking)    #TODO: Mudar essa lógica do 'is_busy'
            self.logger.info(f'Device Stopped')
        else:                                           # If the motor do not recognize the command
            self.communicating_to_motor = False         # Communication to motor ended
            self.status["alarm"] = self.device.alarm    #TODO: Acho que isso não faz nada pq o ALM no DMX é só relacionado à temperatura
            self.logger.info(f'Halt Fail')

    def handle_speed(self, vel):
        """Configures the motor's speed"""
        if vel > Config.max_speed:                          #| 
            vel = Config.max_speed                          #| Checks if the velocity is whithin the min and max value
        elif vel <=0:                                       #|
            vel = Config.max_speed                          #|    
        try:
            self.communicating_to_motor = True              # Communication to motor started
            if self.device.speed(vel):                      # Sends change vel command to motor and if the motor recognized the command
                self.communicating_to_motor = False             # Communication to motor ended
                time.sleep(.1)                                  # Delay after command sent              #TODO: É necessário esse delay?
                self.logger.info(f'Speed changed')
            else:                                           # If the motor do not recognize the command
                self.communicating_to_motor = False             # Communication to motor ended
                self.logger.info(f'Speed change Fail')
        except Exception as e:
            self.communicating_to_motor = False             # Communication to motor ended
            self.logger.error(f"Error speed {str(e)}")

    def handle_connect(self):
        """(Deprecated) - Self explained"""
        self.logger.info(f'Device Connected')
        self.communicating_to_motor = True              # Communication to motor started
        self.device.position
        self.communicating_to_motor = False         # Communication to motor ended
        self._pub_status()                              # Publishes current status

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
            self.communicating_to_motor = True              # Communication to motor started
            if int(speed) != Config.max_speed:              # If the movement speed is different from the default max speed
                self.handle_speed(int(speed))                   # Configures the movement speed
            if direction == 1:                              # Direction 1 indicates FOCUSIN
                # FOCUS IN
                self.device.focus_in_out(int(direction))        # Sends FOCUSIN command to the motor
                self.logger.info(f'Moving FOCUSIN')         
            elif direction == 0:                            # Direction 0 indicates FOCUSOUT
                # FOCUS OUT
                self.device.focus_in_out(int(direction))        # Sends FOCUSOUT command to the motor
                self.logger.info(f'Moving FOCUSOUT')
            time.sleep(.1)                              # Delay after command sent              #TODO: É necessário esse delay?
            self._is_busy = True                        # Motor is busy (focusin/focusout)    #TODO: Mudar essa lógica do 'is_busy'
            self.communicating_to_motor = False         # Communication to motor ended
        except Exception as e:
            self.communicating_to_motor = False         # Communication to motor ended
            self.status["alarm"] = self.device.alarm    #TODO: Acho que isso não faz nada pq o ALM no DMX é só relacionado à temperatura    
            self.status["error"] = str(e)
            self.logger.error(f'Moving FOCUS IN | OUT')
            self._pub_status()                              # Publishes current status

    def handle_move(self, pos, speed):
        """Move focuser to a position
        Args: 
            position microns (integer)
            speed microns/s(integer)
        """   
        try:
            self.communicating_to_motor = True              # Communication to motor started
            self.device.move(int(pos))                      # Sends MOVETO command to motor
            self.communicating_to_motor = False             # Communication to motor ended
            self.logger.info(f'Moving to {pos} position')       
            time.sleep(.1)                                  # Delay after command sent              #TODO: É necessário esse delay?
            self._is_busy = True                            # Motor is busy (focusin/focusout)    #TODO: Mudar essa lógica do 'is_busy'
        except Exception as e:
            self.communicating_to_motor = False             # Communication to motor ended
            self.status["alarm"] = self.device.alarm        #TODO: Acho que isso não faz nada pq o ALM no DMX é só relacionado à temperatura    
            self.status["error"] = str(e)
            self.logger.error(f'Moving {pos}: {str(e)}')
            self._pub_status()                              # Publishes current status

    def _update_status(self):
        """Verifies if there is a change in state variables, 
        such as _is_moving, _homing and _position and publishes in ZeroMQ"""
        if self._position != self.previous_pos:
            self.status["position"] = self._position
            self.previous_pos = self._position
            self._flag_change = True
            # self._pub_status()                              # Publishes current status
            self.encoder = int(self._position * Config.enc_2_microns)

        if self.is_moving != self.previous_is_mov:
            self.status["isMoving"] = self.is_moving
            self.previous_is_mov = self.is_moving 
            # self._check_homing()
            self._flag_change = True
            # self._pub_status()                              # Publishes current status

        if self._initialized != self.previous_initialized:
            self.previous_initialized = self._initialized
            self.status["initialized"] = self._initialized        # This method checks if the homing was performed
            self._check_homing()
            self._flag_change = True

        if self._homing != self.previous_homing:    
            self.status["homing"] = self._homing            
            self.previous_homing = self._homing
            self._check_homing()
            self._flag_change = True
            # self._pub_status()                              # Publishes current status
        
        if self._parking != self.previous_parking:    
            self.status["parking"] = self._parking            
            self.previous_parking = self._parking
            self._check_parking()
            self._flag_change = True

        self._read_motor_status()               # Issues command to read the current motor status.

        if self._flag_change:   # Publishes in 0MQ if a change occurred
            self._flag_change = False
            # self._check_homing()
            self._check_parking()
            self._pub_status()                              # Publishes current status

        # if self._is_moving and self._homing:
        #     self.status["clientId"] = 0

    def _check_homing(self):    #TODO: Change the method name
        """Emits the HOMING status signal according to the current status.
        The transmitted signals will be aqcquired by every object that connects to it"""
        if self.status["homing"]:                                           # If 'Homing' is 'True'
            self._signals_initialized.emit(False,"statusLed", "WAIT")           # Emits WAIT status to indicator LED (While homing the led is YELLOW)
        elif self.status["initialized"]:                                    # If 'Initialized' is 'True'
            self._signals_initialized.emit(True,"statusLed", "OK")              # Emits OK status to indicator LED (When homing was performed the led is GREEN)
        else:                                                               # If none of the above is true
            self._signals_initialized.emit(False,"statusLed", "NOK")            # Emits NOK status to indicator LED (When homing was NOT performed the led is RED)

    def _check_parking(self):    #TODO: Change the method name
        """Emits the PARKING status signal according to the current status.
        The transmitted signals will be aqcquired by every object that connects to it"""
        if self.status["parking"]:                                          # If current parking status is 'True'
            self._signals_parking.emit(True,"statusLed", "WAIT")                # Emits WAIT status to indicator LED (While parking the led is YELLOW)
        else:                                                               # If parking is not being performed
            self._signals_parking.emit(False,"statusLed", "NOK")                # Emits NOK status to indicator LED (When parking is NOT being performed the led is RED)


    def reply(self, msg: str):
        """Replies to the client

        Parameters
        ----------
        msg : str
            Response message to be sent to the client
        """
        self.replier.send_string(msg)

    @property
    def clientID(self):
        """The ID of the client

        Setting a new value will update the client ID and emit '_signal_client_id' to
        update the value in the GUI wherever it is needed.
        """
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
        """The current position of the focuser in microns

        Setting a new value will update the position and emit '_signal_position_str' and '_signal_position_int'.

        '_signal_position_str' is used where a string is needed to show the value in the GUI.
        '_signal_position_int' is used where an int value is needed.                            #TODO: Talvez dê para unificar em um tipo de signal que possui str e int
        """
        return self._position
    @position.setter
    def position(self, value: int):
        self._position = value
        self._signal_position_str.emit(str(value))
        self._signal_position_int.emit(value)

    @property
    def encoder(self):
        """The current position of the encoder
        
        Setting a new value will update the encoder position an emit '_signal_encoder'.
        """
        return self._encoder
    @encoder.setter
    def encoder(self, value: int):
        self._encoder = value
        self._signal_encoder.emit(str(value))

    @property
    def router_reachable(self):
        """Status of the reachability of the router
        
        Setting a new value will update the reachable status and emit '_signals_router.status' """
        return self._router_reachable
    
    @router_reachable.setter
    def router_reachable(self, value: bool):
        self._router_reachable = value
        # self._signal_router_reachable_bool.emit(value)
        self._signals_router.status.emit(value)

    @property
    def motor_reachable(self):
        """Status of the reachability of the motor
        
        Setting a new value will update the reachable status and emit '_signals_motor.status' """
        return self._motor_reachable
    @motor_reachable.setter
    def motor_reachable(self, value: bool):
        self._motor_reachable = value
        self._signals_motor.status.emit(value)

    @property
    def server_connected(self):
        """Status of server
        
        Setting a new value will update the server status and emit '_signals_server' """
        return self._server_connected
    @server_connected.setter
    def server_connected(self, value: bool):
        self._server_connected = value
        # self._signal_server_started_bool.emit(value)
        if value:
            self._signals_server.emit(value,"statusLed", "OK")          # When server is connected the 'statusLed' is green (defined in the stylesheet)
        else:
            self._signals_server.emit(value,"statusLed", "NOK")         # When server is NOT connected the 'statusLed' is red (defined in the stylesheet)

    @property
    def communicating_to_motor(self):
        """Status of the communication between server and motor. Indicates that a message is being sent from the server to the motor.
        
        Setting a new value will update the communication status and emit '_signal_communicating_to_motor_bool'.
        Also emits the signal '_statusBar_led' to update the status bar led         #TODO: mudar esse signal"""
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
        """Client transaction ID
        
        Setting a new value will update the client transaction ID and emit '_signal_transaction_id' """
        return self._transaction_id
    @transaction_id.setter
    def transaction_id(self, value: int):
        if self.clientID:                                   # The transaction ID must be related to a client
            self._transaction_id = value
            self._signal_transaction_id.emit(str(value))
        else:
            self._transaction_id = 0
            self._signal_transaction_id.emit("")
    

    @property
    def is_moving(self):
        """Motor moving status
        
        Setting a new value will update the motor moving status and emit '_signals_moving'"""
        return self._is_moving
    @is_moving.setter
    def is_moving(self, value: bool):
        self._is_moving = value
        if value:
            self._signals_moving.emit(value, "statusLed", "OK")
        else:
            self._signals_moving.emit(value, "statusLed", "NOK")

    @property
    def status_lim_minus(self):
        """LIM min status. 
        
        Indicates that the lim min microswitch is activated
        
        Setting a new value will update the LIM min status and emit '_signals_lim_min'"""
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
        """LIM max status. 
        
        Indicates that the lim max microswitch is activated
        
        Setting a new value will update the LIM max status and emit '_signals_lim_max'"""
        return self._status_lim_max
    @status_lim_max.setter
    def status_lim_max(self, value: bool):
        self._status_lim_max = value
        if value:
            self._signals_lim_max.emit(value, "statusLed", "OK")
        else:
            self._signals_lim_max.emit(value, "statusLed", "NOK")

    @property
    def initialized(self):
        """Initialized status. 
        
        Indicates if the Home was performed and the position value is valid.
        
        Setting a new value will update the initialized status"""           #TODO: Não teria que emitir um signal aqui?
        return self._initialized
    @initialized.setter
    def initialized(self, value: bool):
        self._initialized = value
        self.status["initialized"] = self._initialized

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
            # 'HALT': self.handle_halt,
            'CONNECT': self.handle_connect,
            'DISCONNECT': self.handle_disconnect,
            'STATUS': self._pub_status,
            'PARK': self._handle_park
        }
        self.start_server()                                         # Starts the ZMQ server and publishes the current status
        self._stop_var = False                                       # Initializes variable used that keep the thread loop running
        self.status["connected"] = self.device.connected            # Reads "_connected" from the motor
        while not self._stop_var:                                    # Start of the thread loop
            t0 = time.time()                                        # Keeps the time when the loop began
            current_time = datetime.now()                           # Reads current time

            self._signal_firmware_status.emit(self.device.get_firmware_status())

            self.position = self.device.position    # Updates position every cycle

            # if -1 >= (current_time.second - self.last_pub.second) or (current_time.second - self.last_pub.second) >= 1:       #TODO: Não daria pra só checar se o valor absoluto for >= 1?
            if abs(current_time.second - self.last_pub.second) >= 1:                                                            # Updates position and publishes status every 1 second
                # self.device.position 
                # self.position = self.device.position                                                                            # Reads motor current position
                self.status["position"] = self.position
                self.last_pub = self._pub_status()                              # Publishes current status                                                                              # Publishes status  #TODO: Não adianta atualizar "_position" se não colocar em "Status" para publicar
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

                        if command_processed:
                            self._signal_last_command.emit(self.status)
                        else:                                                                                                   # If command was NOT processed
                            self.reply('NAK')                                                                                   # Return 'NAK' to client

                        self.status["connected"] = self.device.connected                                                        # Updates connection status of the motor

                    except Exception as e:                                                                                      # If an exception occurs during the handling of the command 
                        self._pub_status()                              # Publishes current status                                                                                       # Published current status
                        self.logger.error(f'Error: {str(e)}')                                                                   # Logs error

                self._check_motor_moving()                  # Verifies if the motor is moving as expected.
                                          
                self.initialized = self.device.initialized
                self._homing = self.device.homing   
                self._parking = self.device.parking                        
                                                                                               # Updates motor position             
                # if self._homing:                                # (self._homing == True) indicates that the homing was not performed
                #     self._homing = self.device.homing           # This means that while the homing is not performed this will keep checking if it was performed        #TODO: Qual o motivo de `_homing` ter que ser `true` para chamar `device.homing` para checar se está executando a rotina de inicialização?
                if self._initialized and not self._is_moving:    # indicates that the homing was performed
                                                                # The homing was performed and the motor is not moving -> Indicates the motor is not busy
                    self.clientID = 0                           # Sets client not busy
                    self.transaction_id = 0                     # Resets transaction ID
                    self.status["cmd"] =  {                     # Resets "cmd" 
                                            "clientId": self.clientID,                #TODO: Esse valor pode ser 0? Checar arquivo do Ramon e documentação Alpaca. Talvez o 0 seja reservado para "not busy"
                                            "clientTransactionId": 0,                   
                                            "clientName": "",
                                            "action": ""
                                            }                    
                
                # self._position = self.device.position
                # self.busy_id = self.clientID                                              # Keeps the ID of the client that sent the last command
                self._update_status()                                                        # Updates motor readings and publishes the current status to ZMQ             
                self.status["alarm"] = 0                                                    # Resets "alarm"
                self.communicating_to_motor = False         # Communication to motor ended
            
            
            if self.device.connected:
                pass

            else:                                                                       # If the device is not configured or not connected or the poller is not configured              
                # if (abs(current_time.second - self.last_ping_time.second) >= 5) or (self._router_reachable is False):           # Runs every 5 seconds
                # if self._router_reachable is False:
                # self.router_reachable = self.ping_router()                                                                     # Updates if router is reachable      #INFO: self.reach_device() já faz esses dois
                # self.motor_reachable = self.ping_motor()                                                                      # Updates if motor is reachable
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
        self.communicating_to_motor = False         # Communication to motor ended
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
            # If the driver says the motor is moving but there is no change in position reading means the motor is stalled
                if pos_delta == 0 and self.status_lim_minus == False and self.status_lim_max == False and self.position != 0:          
                    # raise AlpacaExceptions.DriverException(1300, "Stalled Motor")       # Raises exception according to Alpaca      #TODO: Definir direito o código e a mensagem
                    self.logger.error("Motor stalled during movement.")
                    print("Stalled Motor")   
                    _loop_count = 0                                                         # TODO: Isso pode ser configurável
                    while self.is_moving and _loop_count < 5:                               # If a stall occurs the server issues a 'halt' command and verifies if the motor responds as expected
                        # self.handle_halt()
                        print(f" Resp V42=1 -> {self.device.sendCommand("V42=1")}")
                        print(f" Resp STOP -> {self.device.sendCommand("STOP")}")
                        print(f" Resp SR0=0 -> {self.device.sendCommand("SR0=0")}")
                        
                        print("ponto 1")
                        print(self.device.sendCommand("EO=0"))
                        print("ponto 2")
                        # print(f" Resp GS31 -> {self.device.sendCommand("GS31")}")
                        print("ponto 3")
                        # self.reply('ACK')
                        self._read_motor_status()                                           # Issues command to read the current motor status.
                        print("ponto 4")
                        print(self.is_moving)
                        _loop_count+=1
                    if _loop_count == 5:
                        raise Exception("Motor is stalled and driver didn't respond to stop command after 5 tries")
                    self.status["timeout"]= True
                    self.device.home("reset")                       # If a timeout occurs must reset Home since the position is not valid anymore
                    self.initialized = self.device.initialized

                    
                    # self._pub_status()                              # Publishes current status

                # Resets status. Required to accept new commands
                    self.initialized = self.device.initialized
                    self._homing = self.device.homing   
                    self._parking = self.device.parking  
                    self.clientID = 0                         # Sets client not busy
                    self.status["cmd"] =  {                     # Resets "cmd" 
                                            "clientId": self._client_id,                #TODO: Esse valor pode ser 0? Checar arquivo do Ramon e documentação Alpaca. Talvez o 0 seja reservado para "not busy"
                                            "clientTransactionId": 0,                   
                                            "clientName": "",
                                            "action": ""
                                            }         
                    self.status["homing"] = self._homing
                    self.status["parking"] = self._parking

                else:
                    self.position = self.device.position
                    self.status["timeout"] = False
                    self._pub_status()                              # Publishes current status   
            except Exception as e:                                                      # At this point could the exception also be due to a communication issue?
                                                                                     # If an exception occurs during the handling of the command 
                self._pub_status()                              # Publishes current status                                                                                       # Published current status
                self.logger.error(f'Error: {str(e)}')                                                                   # Logs error



    def _read_motor_status(self):   #TODO: mover método para dentro do driver do motor DMX_ETH e fazer outro para o motor AMP
        """Issues command to read the current motor status.
        """
        try:
            resp = format(int(self.device.motor_status), '012b')        # TODO: Ver um jeito de converter para binário sem ser string
            motor_status = "".join(reversed(resp))                      # This is only done so that the bit order is as shown in table 7 of the manual of the motor (DMX-ETH)
            # print(motor_status)


            if(motor_status[0] == '1' or motor_status[1] == '1' or motor_status[2] == '1'):     #| Bit '0' indicates the 'moving' status
                self.is_moving = True                                                           #| Bit '1' indicates acceleration           
            else:                                                                               #| Bit '2' indicates deceleration
                self.is_moving = False                                                          #|  If any are set the motor is moving

            if(motor_status[4] == '1'):         #| Bit '4' indicates the lim minus microswitch status
                self.status_lim_minus = True    #|
            else:                               #|
                self.status_lim_minus = False   #|

            if(motor_status[5] == '1'):         #| Bit '5' indicates the lim max microswitch status
                self.status_lim_max = True      #|
            else:                               #|
                self.status_lim_max = False     #|

            # print(f"Motor status -> {motor_status}")
            


        except Exception as e:                  # TODO: Verificar o que tem que ser feito se não conseguir obter essa informação 
            print(e)


    def _reset_timeout(self):
        """Resets the timeout in the JSON"""
        self.status["timeout"] = False          # Sets 'timeout' to false in the JSON


#=== Methods to pass signals ===#
    def _signals_router_connection(self, status: str):              #TODO: Isso pode ser feito dentro da propriedade 'router_reachable'
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

    def _signals_motor_connection(self, status: str):               #TODO: Isso pode ser feito dentro da propriedade 'motor_reachable'
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
