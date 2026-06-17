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
import os
import sys
from threading import Thread

from misc.client_sample import TEST_SETUP
from src.core.config import Config
import src.core.exceptions as AlpacaExceptions
from src.utils.constants import constants, MotorModels, ReachStatus, MotorParamsIdx, ServerCommands, MotorValidCommands, FocuserHardwareStatus, FocuserSignalsNames, TimeDelays
from src.utils.constants import ServerMessageValidation as SVal
from src.utils.constants import ServerJsonKeys as SJson
from src.utils.signals import PropertySignals, MultiSignal
from src.utils.motor import Motor
from src.interface.zmq_comm import zmqComm
from src.core.log import init_logging
from logging import shutdown
import socket

from src.utils.constants import MotorProgramStatus, motor_program_errors_mask, MotorAlarmInfo  #TODO: remover apos teste

# from src.interface.dmx_eth import FocuserDriver as Focuser
# from src.interface.focuser_driver import FocuserDriver as Focuser

TESTE_TCSPD = False             #TEST: Colocar em True para realizar teste com o tcspd

def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # No executável, sys._MEIPASS é a raiz da pasta temporária
        base_path = sys._MEIPASS
    else:
        # No desenvolvimento, a base é a pasta raiz do projeto (onde está o main4.py)
        # Como este arquivo está em src/core, pegamos o avô dele
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

    return os.path.normpath(os.path.join(base_path, relative_path))

icon_con_ok = resource_path('assets/ui/icons/status.png')
icon_con_nok = resource_path('assets/ui/icons/status-busy.png')
icon_con_wait = resource_path('assets/ui/icons/status-away.png')

class ServerSignals(QObject):
    server_status = PropertySignals()
    router_status = PropertySignals()
    motor_status = PropertySignals()
    status_message = pyqtSignal(str)
    connection_speed = pyqtSignal(str)
    socket_ip = pyqtSignal(str)
    port_pub = pyqtSignal(str)
    port_rep = pyqtSignal(str)
    
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
    last_command = pyqtSignal(dict)
    communicating_to_motor = pyqtSignal(bool)
    client_id = pyqtSignal(str)
    transaction_id = pyqtSignal(str)

    processing_command = PropertySignals()

    create_new_log = pyqtSignal(bool)

    teste = PropertySignals()

class Server(QObject):

    signals = ServerSignals()


    def __init__(self, logger: Logger):
        super(Server, self).__init__()
        self.logger = logger                            # Instantiates logger
    
        # Network (ZMQ)
        self.zmq_comm: zmqComm = None

        # Control variables

        self._stop_loop = False                          #|
        self.previous_is_mov = False                    #|
        self.previous_homing = False                    #|
        self.previous_initialized = False               #|
        self.previous_parking = False                   #|  Control variables initialization
        self.previous_pos = 0                           #|
        self.last_ping_time = datetime.now()            #|
        self.last_pub_time:datetime = datetime.now()                  #|
        self._flag_change = False                       #|
        self._driver_timeout = False
        self._log_creation_day: int = 0

        # Variables for status request
        self._client_id = 0 # '0' 
        self.busy_id = 0
        self._router_reachable = False 
        self._motor_reachable = False
        self.motor:Motor = None                               # Instantiates motor as None
        
        self._reaching_device_thread = None
        self._processing_command: bool = False

        # self.focuser_hdw_current_status = FocuserHardwareStatus(
        #     lim_switch_min=False,
        #     lim_switch_max=False,
        #     initialized=False,
        #     manual_movement=False
        # )
        self.focuser_hdw_current_status = FocuserHardwareStatus()

        self.last_command = {
            SJson.TIMESTAMP: datetime.now(),
            SJson.CMD_CLIENT_NAME: "",
            SJson.CMD_CLIENT_ID:  0,
            SJson.CMD_CLIENT_TRANSACTION_ID: 0,
            SJson.CMD_ACTION : "",
            "PARAMETER": ""
        }

        # Status Message
        if TESTE_TCSPD:                                 #TEST: O json do tcspd não está atualizado então é necessário usar o antigo para testar com o tcspd
            self.status = {
                SJson.ABSOLUTE: Config.absolute,            
                SJson.ALARM: 0,
                SJson.BROKER: "Focuser160",
                SJson.CMD: {
                    SJson.CMD_CLIENT_ID : self._client_id,
                    SJson.CMD_CLIENT_TRANSACTION_ID: 0,
                    SJson.CMD_CLIENT_NAME: "",
                    SJson.CMD_ACTION: ""
                },
                SJson.CONNECTED: False,
                SJson.CONTROLLER: Config.name,
                SJson.DEVICE: Config.device_name,
                SJson.ERROR: "",
                SJson.HOMING: False,            # Homing solicited
                SJson.INITIALIZED: False,       # Homing finalized
                SJson.IS_MOVING: False,          # Executing a function inside the motor
                SJson.MAX_SPEED: Config.max_speed,
                SJson.MAX_STEP: Config.max_step,
                SJson.POSITION: 0,
                SJson.TEMP_COMP: Config.temp_comp,
                SJson.TEMP_COMP_AVAIABLE: Config.tempcompavailable,
                SJson.TEMPERATURE: 0,
                SJson.TIMESTAMP: datetime.isoformat(datetime.now(), timespec='milliseconds'),
                SJson.VERSION: "1.0.0",            #TODO: Pegar a versão do arquivo config.toml
            }
        else:
            self.status = {
                SJson.ABSOLUTE: Config.absolute,            
                SJson.ALARM: 0,
                SJson.BROKER: "Focuser160",
                SJson.CMD: {
                    SJson.CMD_CLIENT_ID : self._client_id,
                    SJson.CMD_CLIENT_TRANSACTION_ID: 0,
                    SJson.CMD_CLIENT_NAME: "",
                    SJson.CMD_ACTION: ""
                },
                SJson.CONNECTED: False,
                SJson.CONTROLLER: Config.name,
                SJson.DEVICE: Config.device_name,
                SJson.ERROR: "",
                SJson.HOMING: False,            # Homing solicited
                SJson.INITIALIZED: False,       # Homing finalized
                SJson.IS_MOVING: False,          # Executing a function inside the motor
                SJson.MAX_SPEED: Config.max_speed,
                SJson.MAX_STEP: Config.max_step,
                SJson.POSITION: 0,
                SJson.TEMP_COMP: Config.temp_comp,
                SJson.TEMP_COMP_AVAIABLE: Config.tempcompavailable,
                SJson.TEMPERATURE: 0,
                SJson.TIMESTAMP: datetime.isoformat(datetime.now(), timespec='milliseconds'),
                SJson.VERSION: "1.0.0",            #TODO: Pegar a versão do arquivo config.toml
                SJson.PARKING: False,               # Executing Parking
                SJson.DEVICE_IP: "127.0.0.1",       # Motor IP
                SJson.DEVICE_ID: "",                # Motor ID
                SJson.DEVICE_FIRMWARE_VERSION: "",  # Motor firmware version
                SJson.TIMEOUT: False,               # Timeout
            }

            self.test_var = 14.2

#region  ========== PROPERTIES ========== # 

    @property
    def stop_loop(self) -> bool:
        """ Get or set the server stop loop flag. Setting the stop loop will
        stop the server main loop."""
        return self._stop_loop
    @stop_loop.setter
    def stop_loop(self, value: bool):
        self._stop_loop = value

    @property
    def server_online(self) -> bool:
        """Gets or sets the server status. Setting server status will also emit
        the signal to update the status throughout the program.
        """
        return self._server_connected
    @server_online.setter
    def server_online(self, value: bool):
        self._server_connected = value
        if value:
            self.signals.server_status.emit(value,"statusLed", "OK")          # When server is connected the 'statusLed' is green (defined in the stylesheet)
            self.signals.socket_ip.emit(self.zmq_comm.ip_address)
            self.signals.port_pub.emit(self.zmq_comm.port_pub)
            self.signals.port_rep.emit(self.zmq_comm.port_rep)
        else:
            self.signals.server_status.emit(value,"statusLed", "NOK")         # When server is NOT connected the 'statusLed' is red (defined in the stylesheet)
            self.signals.socket_ip.emit('')
            self.signals.port_pub.emit('')
            self.signals.port_rep.emit('')

    @property
    def router_reachable(self) -> bool:
        """Gets or sets the status of the router reachability. When the value
        is set the signal 'router_status' is emitted to update the value where needed."""
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
        """Gets or sets the status of the motor reachability. When the value
        is set the signal 'motor_status' is emitted to update the value where needed."""
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
            self.status[SJson.CONNECTED] = True
            self.signals.motor_status.emit(True, "statusLed", "OK")
            self._motor_reachable = True
        else:
            self.status[SJson.CONNECTED] = False
            self.signals.motor_status.emit(False, "statusLed", "NOK")
            self._motor_reachable = False

    @property
    def communicating_to_motor(self) -> bool:   #TODO: Verificar se vai ser usada essa informação
        """Status of the communication between server and motor. 
        Indicates if a message is being sent from the server to the motor.
        Setting a new value will update the communication status and emit '_signal_communicating_to_motor_bool'.
        Also emits the signal 'communicating_to_motor'"""
        return self._communicating_to_motor
    @communicating_to_motor.setter
    def communicating_to_motor(self, value: bool):
        self._communicating_to_motor = value
        self.signals.communicating_to_motor.emit(value)

    @property
    def driver_timeout(self) -> bool:
        return self._driver_timeout
    @driver_timeout.setter
    def driver_timeout(self, value: bool):
        self._driver_timeout = value
        self.status[SJson.TIMEOUT] = value
        if value:
            self.logger.warning("CLP communication timeout")
            self.motor_reachable = ReachStatus.WAITING
            
    @property
    def processing_command(self) -> bool:
        return self._processing_command
    @processing_command.setter
    def processing_command(self, value: bool):
        self._processing_command = value
        if value:
            self.signals.processing_command.emit(value, 'statusLed', 'NOK')
        else:
            self.signals.processing_command.emit(value, 'statusLed', 'OFF')



#endregion




#region ========== METHODS ========== # 
    def teste(self):
        # self.motor._alarm = not self.motor._alarm
        # self.motor.driver.sendCommand("POL=0")
        # self.motor.driver.sendCommand("SR1=1")

        # self.motor.set_param(MotorParamsIdx.BACKLASH, self.test_var)
        # self.test_var += 2

        # self.motor.set_param(MotorParamsIdx.MOTOR_IP, "192.168.1.100")
        # self.test_var += 112.3
        # self.status[SJson.POSITION] = self.test_var
        # self.motor.signals.position.emit(self.test_var)

        stat = 43011
        msg = "Flags ativadas: "
        msg += self.motor.driver._extract_flags_info(stat, MotorProgramStatus)
        # for flag in MotorProgramStatus:
        #     if stat & flag:
        #         stat = stat - flag
        #         if stat > 0:
        #             msg += f"{flag.name} & "
        #         else:
        #             msg += f"{flag.name}"

        print(msg)



        msg_error = ''
        alc = 4548
        # alc = MotorAlarmInfo(alc_int)



        sastat_alarm_int = stat & motor_program_errors_mask
        # sastat_alarm = MotorProgramStatus(sastat_alarm_int)

        # if alc > 0:
        #     msg_error += 'Alarms ALC: '
        #     for error in MotorAlarmInfo:
        #         if alc & error:
        #             alc = alc - error
        #             if alc > 0:
        #                 msg_error += f"{error.name} & "
        #             else:
        #                 msg_error += f"{error.name}"

        # if sastat_alarm_int > 0:
        #     msg_error += f"\nAlarms SASTAT: "
        #     for error in MotorProgramStatus:
        #         if sastat_alarm_int & error:
        #             sastat_alarm_int = sastat_alarm_int - error
        #             if sastat_alarm_int > 0:
        #                 msg_error += f"{error.name} & "
        #             else:
        #                 msg_error += f"{error.name}"

        if alc > 0:
            msg_error += 'Alarms ALC: '
            msg_error += self.motor.driver._extract_flags_info(alc, MotorAlarmInfo)
        if sastat_alarm_int > 0:
            msg_error += f"\nAlarms SASTAT: "
            msg_error += self.motor.driver._extract_flags_info(sastat_alarm_int, MotorProgramStatus)

        print(msg_error)

    def _start_server(self):
        """Starts server communication
        
        The server communication is based on the ZMQ protocol,
        with a PUB and a REP port.
        The PUB port is used to publish the server status and the 
        REP port is used to reply to clients commands."""
        # Checks if the server communication was already started
        if self.zmq_comm:
            self.logger.info(f'Trying to start the server but the server is already running')
            return
        
        # Instantiates the server ZMQ communication according to the Config file
        self.zmq_comm = zmqComm(Config.ip_address,
                                    port_pub=str(Config.port_pub),
                                    port_rep=str(Config.port_rep)
                                )
        # Tries to connect the ZMQ
        try:
            self.server_online = self.zmq_comm.connect()
            self.logger.info(f"Publisher binded to {self.zmq_comm.ip_address}:{self.zmq_comm.port_pub}")
            self.logger.info(f"REP binded to {self.zmq_comm.ip_address}:{self.zmq_comm.port_rep}")
            self.logger.info(f'Server started')
        except Exception as e:
            self.server_online = False
            self.logger.error(e)

    def disconnect(self):
        """Disconnects motor and stops server communication
        
        When the server is stopped the motor is disconnected 
        and one last pub is performed with the current server status
        before the server communication is closed."""
        if self.server_online:
            try:
                self.logger.info(f'Disconnecting motor')
                self.motor.disconnect()
                self.status[SJson.CONNECTED] = self.motor.connected
                self.zmq_comm.pub(self.status)
                self.logger.info(f'Disconnecting Server')
                self.server_online = self.zmq_comm.disconnect()
                self.zmq_comm = None
                self.logger.info(f'Server disconnected')
            except Exception as e:
                print(e)
                self.logger.error(e)

    def stop_poll(self):
        """Stops the ZMQ poller"""
        self.zmq_comm.stop_poller()

    def init_device(self, motor_model: MotorModels):
        """Initializes the motor driver according to the selected focuser

        :param motor_model: Motor model
        :type motor_model: MotorModels
        :raises ValueError: Raises exception if the motor model is not valid
        """
        if self.motor == None:
            self.motor = Motor(motor_model) 

            self.motor.driver.driver_comm.timeout.connect(lambda value: setattr(self, 'driver_timeout', value))
            self.motor.signals.alarm.status.connect(lambda val: self.logger.error(f'{self.motor._alarm_info}') if val == True else ... )

            self.motor.signals.lim_max.status.connect(self._log_update)
            self.motor.signals.lim_min.status.connect(self._log_update)
            self.motor.signals.initialized.status.connect(self._log_update)
            self.motor.driver.driver_comm.manual_movement.status.connect(self._log_update)
            self.motor.driver.driver_comm.run_focus_in.status.connect(self._update_current_movement)
            self.motor.driver.driver_comm.run_focus_out.status.connect(self._update_current_movement)
            self.motor.driver.driver_comm.run_park.status.connect(self._update_current_movement)
            self.motor.signals.initialized.status.connect(self._update_current_movement)
            self.motor.signals.moving.status.connect(lambda val: self.logger.warning("FOCUSER MOVING") if val else self.logger.warning(f"FOCUSER STOPPED at {self.motor.position}"))

            self.motor.signals.error_msg.connect(lambda msg: self.logger.error(f'{msg}'))
        else:
            raise ValueError("Invalid motor model")

    def _reach_gateway(self):
        try:
            if not self.router_reachable:                                                           # If the router is not reachable
                self.router_reachable = ReachStatus.CONNECTING                                           # Emits signals for GUI update (Router attempting connection)
                self.motor_reachable = ReachStatus.WAITING                                               # Emits signals for GUI update (Motor waiting)
                self.communicating_to_motor = False                                                     # Not communicating to the motor
                            
                for _try in range(5):                                                                   # Tries 5 times to ping the router
                    time.sleep(TimeDelays.RETRY_TIMEOUT)             # delay between tries                         
                    self.signals.status_message.emit(f"Trying Connect to Router...")                      # Emits signals for GUI update
                    reachable = ping(Config.gateway_ip, count=1, timeout=0.6, privileged=False).is_alive         # Tries to ping the router IP
                    print(f'trying to ping gateway at {Config.gateway_ip}')
                    if reachable:                                                                               # If the ping is succesful
                        self.router_reachable = ReachStatus.CONNECTED
                        self.signals.status_message.emit(f"Connection succesfull after {_try+1} tries")                         # Emits signals for GUI update
                        break                                                                                   # Exits for loop
            else:                                                                                   # If router already reachable
                self.router_reachable = ReachStatus.CONNECTED                                           # Emits signals for GUI update (Router connected)
        except Exception as e:
            self.logger.error(f'{str(e)}') 

    def _reach_motor(self):
        try:
            if self.router_reachable and not self.motor_reachable:                                  # If the router is reachable and the motor is not reachable
                time.sleep(0.3) 
                self.motor_reachable = ReachStatus.CONNECTING                                            # Emits signals for GUI update (Motor attempting connection)
                self.communicating_to_motor = False                                                     # Not communicating to the motor
                
                for _try in range(5):                                                                   # Tries 5 times to ping the router
                    time.sleep(TimeDelays.RETRY_TIMEOUT)             # delay between tries
                    self.signals.status_message.emit(f"Trying Connect to Motor...")               # Emits signals for GUI update
                    print(f'Trying to ping motor at {Config.device_ip}:{Config.device_port}')
                    reachable = self.motor.ping()                                              # Tries to ping the motor IP
                    if reachable:                                                               # If the ping is successful
                        self.motor_reachable = ReachStatus.CONNECTED
                        self.signals.status_message.emit(f"Connection succesfull after {_try+1} tries")                 # Emits signals for GUI update
                        self.driver_timeout = False
                        break                   # Exits for loop
        except Exception as e:
            self.logger.error(f'{str(e)}') 

    def _link_device(self):
        """Verifies if the router and the motor are reachable. 
        If its reachable connects to the motor and updates status information"""
        _try = 0
        self.last_ping_time = datetime.now()                                                    # Saves the time when the method was called
        try:
                            
            if self.motor_reachable:                                                                # If the motor is reachable
                self.router_reachable = ReachStatus.CONNECTED                                            # Emits signals for GUI update
                self.motor_reachable = ReachStatus.CONNECTED                                           # Emits signals for GUI update
                self.signals.status_message.emit("Connecting motor")       
                time.sleep(0.2)                
                # try:
                self.processing_command = False
                self.motor.connect()                                                        # Creates the socket and connects the server to the motor
                self.signals.status_message.emit("Configuring motor...")         
                self.motor.signals.progress.value.emit(True)
                self.motor.signals.progress.string.emit(0)
                self.motor.update_status()
                self._get_motor_params()
                
                self.motor.signals.progress.string.emit(0)
                self.signals.status_message.emit("Updating parameters...")          
                self.motor._update_motor_params()
                self._update_status()
                self.motor.signals.progress.value.emit(False) 
                self.signals.status_message.emit("")                   
                self.status[SJson.DEVICE_IP] = self.motor.get_param(MotorParamsIdx.MOTOR_IP)
                self.status[SJson.DEVICE_ID] = self.motor.ID
                self.status[SJson.DEVICE_FIRMWARE_VERSION] = self.motor.firmware_version

                # self._check_homing()                                                                # Emits homing signals      #TODO: Trocar nome do método

        #     #--- Emits max pos and backlash to update GUI. The value is different in the test setup due to the size and gear differences
                if self.motor.model == MotorModels.ARCUS_DMX_ETH:
                    if TEST_SETUP:
                        self.signals.max_pos.emit(int(self.motor.get_param(MotorParamsIdx.MAX_POS)) + 5)             # A small gap at the end to account the distance to the lim+ uswitch 
                        self.signals.backlash.emit(-(int(self.motor.get_param(MotorParamsIdx.BACKLASH)) + 10))       # A small gap at the end to account the distance to the lim+ uswitch 
                    else:
                        # TODO: Definir valores de excursão na montagem real
                        self.signals.max_pos.emit(int(self.motor.get_param(MotorParamsIdx.MAX_POS)))                 # A small gap at the end to account the distance to the lim+ uswitch 
                        self.signals.backlash.emit(-(int(self.motor.get_param(MotorParamsIdx.BACKLASH))))            # A small gap at the end to account the distance to the lim+ uswitch 
                else:
                    self.signals.max_pos.emit(int(self.motor.get_param(MotorParamsIdx.MAX_POS)))             # A small gap at the end to account the distance to the lim+ uswitch
                    self.signals.backlash.emit(-(int(self.motor.get_param(MotorParamsIdx.BACKLASH))))            # A small gap at the end to account the distance to the lim+ us


                self.logger.info(f'Motor Reached and connected.')
        except Exception as e:
            self.logger.error(f'{str(e)}')  
  
        # if self._reaching_device_thread:
        #     self._reaching_device_thread = None

    def _update_status(self):
        """Updates motor status and saves to JSON"""
        self.status[SJson.CONNECTED] = self.motor.connected
        if self.motor.initialized:
            # self.status[SJson.POSITION] = self.motor.position
            self.motor.position
            self.status[SJson.POSITION] = self.motor.driver.conv_position_show(type="float")
        else:
            self.motor.position # Updates the position but does not save it to the JSON since the motor is not initialized and the position value is not reliable
            self.status[SJson.POSITION] = constants.INVALID_RESPONSE
        self.status[SJson.INITIALIZED] = self.motor.initialized
        self.status[SJson.HOMING] = self.motor.homing
        self.status[SJson.PARKING] = self.motor.parking
        self.status[SJson.IS_MOVING] = self.motor.is_moving
        self.status[SJson.ALARM] = self.motor.alarm
        self.motor.firmware_status

        if self.motor.alarm_info:
            if self.motor.alarm_info != self.status[SJson.ERROR]:
                self.status[SJson.ERROR] = self.motor.alarm_info
                self.logger.error(self.status[SJson.ERROR])
        else:
            if self.status[SJson.ERROR] != "":
                self.logger.info("Previous errors resolved")
            self.status[SJson.ERROR] = ""

    def _get_motor_params(self):
        """Updates the motor parameters in the JSON"""
        #TODO: Adicionar os outros parâmetros no JSON
        p = 0
        for param in MotorParamsIdx:
            print(param)
            p += 1
            self.motor.signals.progress.string.emit(int(p/len(MotorParamsIdx)*100))
            time.sleep(0.05)            # Just for better visualization of ui update
            if param in MotorParamsIdx:
                self.motor.get_param(param)
        self.status[SJson.DEVICE_IP] = self.motor.parameters[MotorParamsIdx.MOTOR_IP].VALUE
        self.status[SJson.MAX_SPEED] = self.motor.parameters[MotorParamsIdx.MAX_SPEED].VALUE
        self.status[SJson.MAX_STEP] = self.motor.parameters[MotorParamsIdx.MAX_STEP].VALUE

    # def _update_motor_params(self):
    #     """Sends to the CLP the updated values of the configurations"""
    #     for param_idx in MotorParamsIdx:
    #         if param_idx != MotorParamsIdx.MOTOR_IP:
    #             self.motor.set_param(param_idx, int(float(self.motor.parameters[param_idx].VALUE)))

    #     for param_idx in MotorParamsIdx:
    #         print(f"{self.motor.parameters[param_idx].NAME} - {self.motor.parameters[param_idx].VALUE}")

    #     # self.motor.set_param(MotorParamsIdx.BACKLASH, Config.backlash)
    #     self.logger.info("Motor parameters initialized")
        
        


    def run(self):  #TODO: Considerar forma de parar o 
        """Server Main Loop (Runs on a thread started by main)
        
        The server loop is stopped when the GUI issues a stop command
        """
        self.stop_loop = False
        self._client_id = 0
        self._start_server()

        while not self.motor_reachable and self._stop_loop == False:
            self._reach_gateway()    
            self._reach_motor() 
            self._link_device()
        
        self.status[SJson.CONNECTED] = self.motor.connected
        while self._stop_loop == False:
            t0 = time.time()                                        # Keeps the time when the loop began
            
            current_time = datetime.now()                           # Reads current time
            
            # A new log file must be created at noon if the log reference date
            # is different from the current date
            if current_time.day != self.logger.reference_date.day:
                if current_time.hour >= 12:
                    self.logger = init_logging()

            try:

                if abs(current_time.second - self.last_pub_time.second) >= Config.pub_interval and self.server_online:   # Publishes status every second
                    self.last_pub_time = self.zmq_comm.pub(self.status)

                # Motor must be connected, poller defined and the 'reach_device' thread must have finished
                if self.motor.connected and self.zmq_comm.poller:
                    
                    
                    socks = dict(self.zmq_comm.poller.poll(50))  # poll(50)                                                                           # Polls the information from the ZMQ to receive commands from the client
                    if socks.get(self.zmq_comm.replier) == zmq.POLLIN:                                                                       # If the socket is configured as Pollin   #TODO: Necessário?
                        
                        received_client_msg = self.zmq_comm.replier.recv_string()
                        try:
                            msg_json = json.loads(received_client_msg)
                            parsed_cmd = self._parse_client_command(msg_json)                   # Parses client command
                            self._command_validation(parsed_cmd)                                # Validates the received command
                            self._handle_command(parsed_cmd)                                    # Executes the command
                            self.status[SJson.CMD] = msg_json                                   # Updates status with the current command being executed
                            self.zmq_comm.reply('ACK')                                          # Replies 'ACK' to inform the client that everything went ok
                            # self.signals.last_command.emit(self.status)
                            self.signals.last_command.emit(self.last_command)
                        except Exception as e: 
                            print(e)
                            self.zmq_comm.reply('NAK')          # Replies 'NAK' to inform the client that an error occured                     
                            self.zmq_comm.pub(self.status)  
                            self.processing_command = False
                            self.logger.error(e)
                    
                    self._update_status()
                    self.motor.update_status()

                    self._reset_client_info()

                    if( self.motor.driver.sendCommand("V39") == '1' ):  # V39 used to test motor firmware
                        self.signals.teste.emit(True, "statusLed", "OK")
                    else:
                        self.signals.teste.emit(True, "statusLed", "NOK")

                    # print(f"V25 = {self.motor.driver.sendCommand("V25")}")
                    # print(f"V24 = {self.motor.driver.sendCommand("V24")}")



                else:
                    
                    # If the connection was lost the server verifies if the gateway is reachable, if so then 
                    # the server tries to reach the motor. 
                    self.processing_command = False
                    for _try in range(5):                                                                   # Tries 5 times to ping the router
                        time.sleep(TimeDelays.RETRY_TIMEOUT)             # delay between tries                         
                        self.signals.status_message.emit(f"Trying Connect to Router...")                      # Emits signals for GUI update
                        reachable = ping(Config.gateway_ip, count=1, timeout=0.6, privileged=False).is_alive         # Tries to ping the router IP
                        print(f'trying to ping gateway at {Config.gateway_ip}')
                        if reachable:                                                                               # If the ping is succesful
                            self.router_reachable = ReachStatus.CONNECTED
                            self.signals.status_message.emit(f"Connection succesfull after {_try+1} tries")                         # Emits signals for GUI update
                            break 
                        else:
                            self.router_reachable = ReachStatus.WAITING                                                                                        # Exits for loop

                    if self.router_reachable:
                        self._reach_motor()
                        self._link_device()
                    # else:
                    #     self._link_device()
                        
                
                self.signals.connection_speed.emit(f"{round(time.time()-t0, 3)}")

            except Exception as e:
                self.logger.error(f"{e}")

        if self._reaching_device_thread and self._reaching_device_thread.is_alive():
            self._reaching_device_thread.join()                                 # Joins the thread to wait until it is finished
            self._reaching_device_thread = None

        self.router_reachable = False
        self.motor_reachable = False
        self.communicating_to_motor = False 

    
    def _parse_client_command(self, msg_json: json) -> dict:
        """Parses received command and updates status

        :param msg: received command
        :type msg: str
        :return: Dictionary containing the command and parameters
        :rtype: dict
        """
        cmd = msg_json.get(SJson.CMD_ACTION)

        parsed = {  SJson.TIMESTAMP: self.status[SJson.TIMESTAMP],
                    SJson.CMD_CLIENT_NAME: msg_json.get(SJson.CMD_CLIENT_NAME),
                    SJson.CMD_CLIENT_TRANSACTION_ID: msg_json.get(SJson.CMD_CLIENT_TRANSACTION_ID),
                    SJson.CMD_CLIENT_ID: msg_json.get(SJson.CMD_CLIENT_ID),   #TODO: Verificar como checar qual cliente enviou a mensagem, nem todo cliente vai ter um "CLIENT NAME"
                    SJson.CMD_ACTION: cmd,
                    'PARAMETER': None }

        p = cmd.find('=')                   # The '=' sign separates the command and its parameter

        # 'p == -1' indicates that there is no '=' sign so the command has no parameter, in this case the 
        # parsed message dont need to be changed. 
        if p != -1:        
            parsed[SJson.CMD_ACTION] = cmd[:p]
            parsed["PARAMETER"] = int(cmd[p+1:])

        # If the client json do not contain a 'clientName' it is set as 'UNIDENTIFIED'
        if parsed[SJson.CMD_CLIENT_NAME] is None:
            parsed[SJson.CMD_CLIENT_NAME] = "UNIDENTIFIED"
            msg_json[SJson.CMD_CLIENT_NAME] = parsed[SJson.CMD_CLIENT_NAME]  
        print(parsed)

        return parsed    
    
    def _command_validation(self, cmd: dict) -> bool:
        """Validates the command received from the client

        Rules for validation:
            - 'Status' command is always accepted.
            - If the motor is NOT in movement any command will be accepted
            - If the motor is already in movement then only commands sent
                by the same client that started the movement will be accepted.

        :param msg: Message received from the client
        :type msg: str
        :return: Bool indicating if the command can be processed
        :rtype: bool
        """

        if cmd[SJson.CMD_ACTION] == ServerCommands.STATUS:
            return True

        if not self.processing_command:
            program_status = self.motor.firmware_status
            if  program_status == "Idle":
                return True
            elif program_status == "Running":
                print(cmd[SJson.CMD_ACTION])
                if cmd[SJson.CMD_ACTION] == ServerCommands.HALT:
                    return True
                else:
                    raise RuntimeError(f"The focuser is already running the command '{self.last_command[SJson.CMD_ACTION].upper()}' requested by client ID '{self.last_command[SJson.CMD_CLIENT_ID]}'")
            else:
                raise RuntimeError(f"Cannot run command due to current motor program status '{program_status.upper()}'")
        else:
            raise RuntimeError(f"Server already processing a command...")
        
        # if cmd["COMMAND"] == ServerCommands.STATUS:     # 'STATUS' is a command to the server
        #     return

        # elif cmd["COMMAND"] in MotorValidCommands:
        #     if self.motor.is_moving: 
        #         print(f"CLIENTE ATUAL: {self.status[SJson.CMD][SJson.CMD_CLIENT_ID]}")
        #         if  cmd["CLIENT"] == self.status[SJson.CMD][SJson.CMD_CLIENT_ID]:     # If the command was sent by the same client that sent the last command
        #             return 
        #         else:
        #             raise RuntimeError(f'Motor already moving: Client "{self.status[SJson.CMD][SJson.CMD_CLIENT_NAME]}" '
        #                                f'started the movement and client "{cmd["CLIENT"]}" tried to '
        #                                f'start another movement')
        #     else:
        #         return 
        # else:
        #     raise ValueError(f'Command "{cmd}" is not a valid command')


    def _handle_command(self, cmd: dict):
        """Handles the command received by the client

        :param cmd: Parsed command
        :type cmd: dict
        :raises RuntimeError: Returns an error if the motor responds 'NOK'
        """
 
        # self.status["error"] = ""             # Resets "error" status #TODO: Realizar um tratamento correto de erro

        # 'STATUS' is a command to the server and not to the motor
        if cmd[SJson.CMD_ACTION] == ServerCommands.STATUS:
            self.zmq_comm.pub(self.status)                  #TODO: Atualizar o status antes de publicar?
        else:
            self.processing_command = True
            self.communicating_to_motor = True              #TODO: Na verdade não é somente nesse ponto que está comunicando, as propriedades também comunicam com o motor
            motor_response = self.motor.send_command(cmd)
            self.communicating_to_motor = False
            self.processing_command = False
            if motor_response == "NOK":
                self.processing_command = False
                raise RuntimeError(f'Motor returned \033[31m"NOK"\033[0m trying to run command "{cmd[SJson.CMD_ACTION].upper()}"')
        
        # self.zmq_comm.reply('ACK')                  # Replies 'ACK' to inform the client that everything went ok
        self.logger.info(f'Command issued: {cmd}')
        # self.last_command[SJson.CMD_CLIENT_ID.value] = cmd[SJson.CMD_CLIENT_ID.value]
        # self.last_command[SJson.CMD_ACTION.value] = cmd[SJson.CMD_ACTION.value]
        if cmd["PARAMETER"] is not None:
            cmd[SJson.CMD_ACTION] = cmd[SJson.CMD_ACTION] + " : " + str(cmd["PARAMETER"])
        self.last_command = cmd                         # Motor recognized and returned OK to command so updates last command

    def _reset_client_info(self):
        """Verifies if the motor ended the execution of the
        last command and resets the command information"""
        # print(self.status)
        time.sleep(TimeDelays.WAIT_PARAM) # Time to allow CLP to update internal variables in IAG controller
        if self.motor.firmware_status == 'Idle' and \
            self.status[SJson.CMD][SJson.CMD_CLIENT_ID] != 0:   

            self.status[SJson.CMD][SJson.CMD_CLIENT_ID] = 0
            self.status[SJson.CMD][SJson.CMD_CLIENT_TRANSACTION_ID] = 0
            self.status[SJson.CMD][SJson.CMD_CLIENT_NAME] = ''
            self.status[SJson.CMD][SJson.CMD_ACTION] = ''


    def _log_update(self, val: bool):
        """Updates the logger according to the signal received"""

        if val:
            val_str = "ACTIVATED"
        else:
            val_str = "DEACTIVATED"

        if self.sender().objectName() == FocuserSignalsNames.LIM_SWITCH_MIN:
            if self.focuser_hdw_current_status.lim_switch_min != val:
                self.focuser_hdw_current_status.lim_switch_min = val
                self.logger.warning(f"Limit switch min {val_str}")

        if self.sender().objectName() == FocuserSignalsNames.LIM_SWITCH_MAX:
            if self.focuser_hdw_current_status.lim_switch_max != val:
                self.focuser_hdw_current_status.lim_switch_max = val
                self.logger.warning(f"Limit switch max {val_str}")

        if self.sender().objectName() == FocuserSignalsNames.INITIALIZED:
            if self.focuser_hdw_current_status.initialized != val:
                self.focuser_hdw_current_status.initialized = val
                if val == True:
                    self.logger.info(f"Focuser is INITIALIZED")

        if self.sender().objectName() == FocuserSignalsNames.MANUAL_MOVEMENT:
            if self.focuser_hdw_current_status.manual_movement != val:
                self.focuser_hdw_current_status.manual_movement = val
                if val == True:
                    self.logger.warning(F"Started MANUAL MOVEMENT - {self.focuser_hdw_current_status.movement_info}")
                else:
                    self.logger.warning("Ended MANUAL MOVEMENT")

    def _update_current_movement(self, val: bool):
        print(self.sender().objectName())
        self.focuser_hdw_current_status.movement_info = self.sender().objectName()

        # The manual movement signal has a delay that may affect the signal in '_log_update' if different movements
        # occur close to each other so the verification is done when a new movement begins
        if self.focuser_hdw_current_status.manual_movement == True:
            if self.sender().objectName() == FocuserSignalsNames.RUN_FOCUS_IN:
                if val != self.motor.driver.focus_in_status:
                    self.logger.warning(F"Started MANUAL MOVEMENT - {self.focuser_hdw_current_status.movement_info}")
            elif self.sender().objectName() == FocuserSignalsNames.RUN_FOCUS_OUT:
                if val != self.motor.driver.focus_out_status:
                    self.logger.warning(F"Started MANUAL MOVEMENT - {self.focuser_hdw_current_status.movement_info}")


#endregion
