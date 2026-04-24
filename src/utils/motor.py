
from enum import Enum, IntEnum
from PyQt6.QtCore import QObject, pyqtSignal

from typing import NamedTuple
from dataclasses import dataclass

#The Driver must be imported after the definition of "MotoParams"
from src.interface.motor_driver import Driver
from src.interface.driver_DMX import  DriverDMX
from src.interface.driver_AMP import DriverAMP
from src.utils.constants import MotorModels, MotorParamsIdx, ServerCommands, constants
from src.utils.signals import PropertySignals, MultiSignal


@dataclass
class MotorParameter():
    IDX: MotorParamsIdx
    NAME: str
    VALUE: int | bool


class MotorSignals(QObject):
    connected = pyqtSignal(bool)
    # position = pyqtSignal(int)
    # homing = pyqtSignal(bool)
    parking = pyqtSignal(bool)
    # moving = pyqtSignal(bool)
    alarm = pyqtSignal(bool)
    # status = pyqtSignal(int)
    firmware_status = pyqtSignal(str)

    moving = PropertySignals()
    lim_min = PropertySignals()
    lim_max = PropertySignals()
    position = MultiSignal()
    encoder = pyqtSignal(str)
    initialized = PropertySignals()

    

class Motor():

    signals = MotorSignals()

    def __init__(self, model: MotorModels, ID: str = '0', ):
        
        # General Information
        self.model = model
        self.driver: Driver
        self.ID: str = ID
        self.firmware_version: str = ''

        self.parameters = {
            MotorParamsIdx.MOTOR_IP : MotorParameter(MotorParamsIdx.MOTOR_IP, "MOTOR_IP", 0),
            MotorParamsIdx.BACKLASH : MotorParameter(MotorParamsIdx.BACKLASH, "BACKLASH", 0),
            MotorParamsIdx.MAX_POS : MotorParameter(MotorParamsIdx.MAX_POS, "MAX_POS", 0),
            MotorParamsIdx.PARK_POS : MotorParameter(MotorParamsIdx.PARK_POS, "PARK_POS", 0),
            MotorParamsIdx.MAX_SPEED : MotorParameter(MotorParamsIdx.MAX_SPEED, "MAX_SPEED", 0),
            MotorParamsIdx.NORMAL_SPEED : MotorParameter(MotorParamsIdx.NORMAL_SPEED, "NORMAL_SPEED", 0),
            MotorParamsIdx.LOW_SPEED : MotorParameter(MotorParamsIdx.LOW_SPEED, "LOW_SPEED", 0),
            MotorParamsIdx.MAX_STEP : MotorParameter(MotorParamsIdx.MAX_STEP, "MAX_STEP", 0)
        }

        self._connected: bool = False
        self._position: int = constants.INVALID_RESPONSE
        self.last_position: int = constants.INVALID_RESPONSE
        self._is_moving: bool = False
        self._encoder: int = constants.INVALID_RESPONSE
        self._homing: bool = False
        self._parking: bool = False
        self._initialized: bool = False
        self._alarm: bool = False
        self._firmware_status: str = 'invalid'
        self._status: str = ""

        if model == MotorModels.ARCUS_DMX_ETH:
            self.driver = DriverDMX(model)
        elif model == MotorModels.AMP_MOTOR:
            self.driver = DriverAMP(model)
        else:
            raise RuntimeError(f'Motor driver model {model} is invalid')

   #region  ========== PROPERTIES ========== # 

    @property
    def connected(self) -> bool:
        """Motor connected status

        :getter: Returns motor connection status.
        :rtype: bool
        """
        return self._connected
    @connected.setter
    def connected(self, status: bool):
        self._connected = status
        self.signals.connected.emit(status)

    
    @property
    def is_moving(self) -> bool:
        return self._is_moving
    @is_moving.setter
    def is_moving(self, val: bool):
        if val != self._is_moving:
            self._is_moving = val
            if val:
                self.signals.moving.emit(val, "statusLed", "OK")
            else:
                self.signals.moving.emit(val, "statusLed", "NOK")


    @property
    def position(self) -> int:
        """Motor position in microns

        :getter: Reads the current motor position. If the value read is different from
                the last position the position is updated and a signal is emited.
        :setter: Sends to the driver a command to move the motor to a new position.
        :rtype: int
        """
        encoder_pos = self.encoder
        pos = self.driver.conv_position(encoder_pos)
        if pos != self._position:
            self.last_position = self._position
            self._position = pos
            self.signals.position.emit(pos)
        return self._position
    @position.setter
    def position(self, value: int) -> str:
        try:
            if self._is_moving:
                raise Exception('[Device] Cannot start a movement while the focuser is already moving')
            if value <= 0 or value >= self.parameters[MotorParamsIdx.MAX_STEP]:
                raise Exception(f'[Device] Invalid Target Position: {value}')     
            resp = self.driver.set_position(value)
            if resp == "OK":
                return f'[Device] move={str(value)}'
        except Exception as e:
            self.disconnect()
            raise e
            # return str(e)
    
    @property
    def encoder(self) -> int:
        """Motor encoder position

        :getter: Reads the current motor encoder position. If the value read is different from
                the last encoder position the value is updated and a signal is emited.
        :rtype: int
        """
        encoder_pos = self.driver.read_encoder()
        if encoder_pos != self._encoder:
            self._encoder = encoder_pos
            self.signals.encoder.emit(str(self._encoder))

        return self._encoder
    
    @property
    def homing(self) -> bool | str:
        """Motor homing status

        :getter: Checks if the motor is performing a 'homing'. If the value changes emits a signal.
        :rtype: bool
        """
        try:
            val = self.driver.read_homing()
            if val != self._homing:
                self._homing = val
                # self.signals.homing.emit(self._homing)
                if self._homing:
                    self.signals.initialized.emit(False, "statusLed", "WAIT")
            return self._homing
        except Exception as e:
            self.disconnect()
            raise e
            # return f'[Device] Could not retrieve homing information: Error -> {str(e)}'


    @property
    def parking(self) -> bool:
        """Motor parking status

        :getter: Checks if the motor is performing a 'parking'. If the value changes emits a signal.
        :rtype: bool
        """
        try:
            val = self.driver.read_parking()
            if val != self._parking:
                self._parking = val
                self.signals.parking.emit(self._parking)
            return self._parking
        except Exception as e:
            self.disconnect()
            raise e
            # return f'[Device] Could not retrieve parking information: Error -> {str(e)}'
    
    @property
    def initialized(self) -> bool:
        """Motor initialized status

        :getter: Checks if the motor performed a 'home' cycle and the position readings are valid. If the
                value changes emits a signal.
        :rtype: bool
        """
        try:
            val = self.driver.read_initialized()
            if val != self._initialized:
                self._initialized = val
                # self.signals.initialized.emit(self._initialized)
                if self._initialized:
                    self.signals.initialized.emit(True, "statusLed", "OK")
                elif not self._homing:
                    self.signals.initialized.emit(False, "statusLed", "NOK")
            return self._initialized
        except Exception as e:
            self.disconnect()
            raise e
            # return f'[Device] Could not retrieve initialized information: Error -> {str(e)}'
    
#endregion

                                        #TODO: A formatação do status é diferente, então vai ser necessário padronizar isso 
    def update_status(self) -> str:    #       entre os motores e fazer com que a resposta de 'read_satus' seja independente do motor.
        """Reads motor status. If the value changes emits a signals.

        :return: motor status
        :rtype: str
        """
        #TODO: Precisa ser ajustado de acordo com o formato do status do motor do IAG
        try:
            if not self._homing and not self._initialized:
                self.signals.initialized.emit(False, "statusLed", "NOK")

            motor_status = self.driver.read_status()
            if motor_status != self._status and motor_status != "NOK":
                self._status = motor_status

                if(motor_status[0] == '1' or motor_status[1] == '1' or motor_status[2] == '1'):     #| Bit '0' indicates the 'moving' status
                    self.is_moving = True                                                           #| Bit '1' indicates acceleration           
                else:                                                                               #| Bit '2' indicates deceleration
                    self.is_moving = False                                                          #|  If any are set the motor is moving

                if(motor_status[4] == '1'):                     #| Bit '4' indicates the lim minus microswitch status
                    self.signals.lim_min.emit(True, "statusLed", "OK")      #|
                else:                                           #|
                    self.signals.lim_min.emit(False, "statusLed", "NOK")    #|

                if(motor_status[5] == '1'):                     #| Bit '5' indicates the lim max microswitch status
                    self.signals.lim_max.emit(True, "statusLed", "OK")      #|
                else:                                           #|
                    self.signals.lim_max.emit(False, "statusLed", "NOK")     #|

            return self._status
        except Exception as e:
            self.disconnect()
            raise e
            # raise RuntimeError(f'[Device] Could not retrieve motor status information: Error -> {str(e)}')

    
    @property
    def alarm(self) -> bool:    #TODO: Talvez já colocar um tratamento para checar qual é o alarme
        """Motor alarm status
        The motor alarm is read using the 'status' property, this is only a way to
        read the alarm.
        
        :getter: Returns the motor alarm status
        :rtype: bool
        """
        return self._alarm
    
    @property
    def firmware_status(self) -> str: 
        try:
            val = self.driver.read_firmware_status()
            if val != self._firmware_status:
                self._firmware_status = val
                self.signals.firmware_status.emit(self._firmware_status)
            return self._firmware_status
        except Exception as e:
            self.disconnect()
            raise e
            # return f'[Device] Could not retrieve firmware status information: Error -> {str(e)}'


    
    def connect(self, max_retries: int = 5, delay: float = 0.1) -> bool:
        """Connects to the motor

        :param max_retries: Max tries to connect to the motor, defaults to 5
        :type max_retries: int, optional
        :param delay: Delay between tries, defaults to 0.1
        :type delay: float, optional
        :return: Connection was successful [OK / NOK] #TODO: Talvez possibilitar mais informações na resposta
        :rtype: str
        """
        if not self.connected:
            try:
                resp = self.driver.connect_motor(max_retries=max_retries, delay=delay)
                if resp == "OK":
                    # self._connected = True
                    # self.signals.connected.emit(self._connected)
                    self.connected = True

                    print('Motor Connected')
                    # self.logger.info('Motor Connected')
                    return True
                else:
                    return False
            except Exception as e:
                print('Failed to establish a connection to the motor')
                # self.logger.error('Failed to establish a connection to the motor')
                raise e
                # return  False
            
    def disconnect(self) -> str:
        """Disconnects the motor

        :return: Disconnection was successful [OK / NOK] #TODO: Talvez possibilitar mais informações na resposta
        :rtype: str
        """
        if self.connected:
            resp = self.driver.disconnect_motor()
            if resp == "OK":
                # self._connected = False
                # self.signals.connected.emit(self._connected)
                self.connected = False
                print("Motor disconnected")

                self._reset_state()

                return "OK"
            else:
                print('Failed to disconnect the motor')
                return "NOK"
        return "OK"

    def _reset_state(self):
        """Resets the motor state to the default values. 
        Also resets the signals."""
        self._connected = False
        self._position = constants.INVALID_RESPONSE
        self.last_position = constants.INVALID_RESPONSE
        self._is_moving = False
        self._encoder = constants.INVALID_RESPONSE
        self._homing = False
        self._parking = False
        self._initialized = False
        self._alarm = False
        self._firmware_status = 'invalid'
        self._status = ""


    def ping(self) -> bool:
        """Pings the motor to check if it is reachable

        :return: Ping was successful [OK / NOK]
        :rtype: str
        """
        resp = self.driver.ping_motor()
        if resp == "OK":
            print('Ping to motor successful')
            return True
        else:
            print('Failed to ping motor')
            return False

    def set_param(self, ParamIndex: MotorParamsIdx, value: int | bool | str) -> str:
        """Sets values for motor parameters

        :param ParamIndex: Motor parameter to be set
        :type ParamIndex: MotorParams
        :param value: Value to be set to the parameter
        :type value: int | bool | str
        :raises ValueError: If an invalid parameter index is received
        :return: Parameter change successful [OK / NOK]
        :rtype: str
        """
        try:
            var = self.parameters[ParamIndex]
            if var.IDX in self.driver.param_methods:  
                resp = self.driver.param_methods[var.IDX](value)
                if resp == "OK":
                    var.VALUE = value
                    self.parameters[var.IDX] = var
                    return resp
                else:
                    raise Exception(f'[Device] Error setting parameter "{var.NAME.upper()}": {resp}')
            else:
                raise ValueError(f'Invalid command. Motor variable "{var.NAME.upper()}" is not defined.')
        except Exception as e:
            self.disconnect()
            raise e
        
    def get_param(self, ParamIndex: MotorParamsIdx) -> int | str | bool:
        """Reads a parameter value from the motor

        :param ParamIndex: Motor parameter to be read
        :type ParamIndex: MotorParams
        :raises ValueError: If an invalid parameter index is received
        :return: Parameter read from the motor
        :rtype: int | str | bool
        """
        try:
            var = self.parameters[ParamIndex]
            if var.IDX in self.driver.param_methods:
                resp = self.driver.param_methods[var.IDX]()
                if resp != "NOK":
                    var.VALUE = resp
                    self.parameters[var.IDX] = var
                    return resp
                else:
                    raise Exception(f'[Device] Failed to read parameter {var.NAME.upper()} from the motor')
            else:
                raise ValueError(f'Invalid command. Motor variable "{var.NAME.upper()}" is not defined.')
        except Exception as e:
            self.disconnect()
            raise e

    def send_command(self, cmd: dict) -> str:
        try:
            if hasattr(ServerCommands, cmd["COMMAND"]):
                if cmd['PARAMETER']:
                    return self.driver.command_methods[cmd["COMMAND"]](cmd["PARAMETER"])
                else:
                    return self.driver.command_methods[cmd["COMMAND"]]()
            else:
                raise RuntimeError(f'"{cmd["COMMAND"]}" is not a valid command')
        except Exception as e:
            self.disconnect()
            raise e


