
from enum import IntEnum
from PyQt6.QtCore import QObject, pyqtSignal

from typing import NamedTuple
from dataclasses import dataclass

class MotorParamsIdx(IntEnum):     
    MOTOR_IP=0,
    BACKLASH=1,
    MAX_POS=2,
    PARK_POS=3,
    MAX_SPEED=4,
    NORMAL_SPEED=5,
    LOW_SPEED=6,
    MAX_STEP=7,
    INVALID=-1

#The Driver must be imported after the definition of "MotoParams"
from src.interface.motor_driver import Driver
from src.interface.driver_DMX import  DriverDMX
from src.interface.driver_AMP import DriverAMP

from src.utils.constants import Constants


@dataclass
class MotorParameter():
    IDX: MotorParamsIdx
    NAME: str
    VALUE: int | bool


class MotorSignals(QObject):
    connected = pyqtSignal(bool)
    position = pyqtSignal(int)
    encoder = pyqtSignal(int)
    homing = pyqtSignal(bool)
    parking = pyqtSignal(bool)
    moving = pyqtSignal(bool)
    initialized = pyqtSignal(bool)
    alarm = pyqtSignal(bool)
    status = pyqtSignal(int)
    status_lim_min = pyqtSignal(bool)
    status_lim_max = pyqtSignal(bool)

    

class Motor():

    signals = MotorSignals()

    def __init__(self, model: Constants, ID: int = 0):
        
        # General Information
        self.model: Constants = model
        self.driver: Driver
        self.ID: int = ID
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
        self._position: int = 0
        self.last_position: int = 0
        self._is_moving: bool = False
        self._encoder: int = 0
        self._homing: bool = False
        self._parking: bool = False
        self._initialized: bool = False
        self._alarm: bool = False

        if model == 'DMX':
            self.driver = DriverDMX(model)
        elif model == 'AMP':
            self.driver = DriverAMP(model)

    #_____PROPERTIES_____

    @property
    def connected(self) -> bool:
        """Motor connected status

        :getter: Returns motor connection status.
        :setter: Changes the connection status and emits a signal.
        :rtype: bool
        """
        return self._connected
    @connected.setter
    def connected(self, value: bool):
        self._connected = value
        self.signals.connected.emit(self._connected)

    @property
    def position(self) -> int:
        """Motor position in microns

        :getter: Reads the current motor position. If the value read is different from
                the last position the position is updated and a signal is emited.
        :setter: Sends to the driver a command to move the motor to a new position.
        :rtype: int
        """
        val = self.driver.read_position()
        if val != self._position:
            self.last_position = self._position
            self._position = val
            self.signals.position.emit(val)
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
            return str(e)
    
    @property
    def encoder(self) -> int:
        """Motor encoder position

        :getter: Reads the current motor encoder position. If the value read is different from
                the last encoder position the value is updated and a signal is emited.
        :rtype: int
        """
        val = self.driver.read_encoder()
        if val != self._encoder:
            self._encoder = val
            self.signals.encoder.emit(self._encoder)
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
                self.signals.homing.emit(self._homing)
            return self._homing
        except Exception as e:
            return f'[Device] Could not retrieve homing information: Error -> {str(e)}'


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
            return f'[Device] Could not retrieve parking information: Error -> {str(e)}'
    
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
                self.signals.initialized.emit(self._initialized)
            return self._initialized
        except Exception as e:
            return f'[Device] Could not retrieve initialized information: Error -> {str(e)}'
    
    @property                   #TODO: A formatação do status é diferente, então vai ser necessário padronizar isso 
    def status(self) -> str:    #       entre os motores e fazer com que a resposta de 'read_satus' seja independente do motor.
        """Motor status                          

        :getter: Reads motor status. If the value changes emits a signals.
        :rtype: int
        """
        try:
            val = self.driver.read_status()
            if val != self._status:
                self._status = val
                self.signals.status.emit(self._status)
            return self._status
        except Exception as e:
            return f'[Device] Could not retrieve motor status information: Error -> {str(e)}'

    
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
    def firmware_status(self) -> int:

    
    def connect(self, max_retries: int = 5, delay: float = 0.1) -> str:
        """Connects to the motor

        :param max_retries: Max tries to connect to the motor, defaults to 5
        :type max_retries: int, optional
        :param delay: Delay between tries, defaults to 0.1
        :type delay: float, optional
        :return: Connection was successful [OK / NOK] #TODO: Talvez possibilitar mais informações na resposta
        :rtype: str
        """
        if not self.connected:
            resp = self.driver.connect_motor(max_retries=max_retries, delay=delay)
            if resp == "OK":
                self.connected = True
                print('Motor Connected')
                # self.logger.info('Motor Connected')
                return "OK"
            else:
                print('Failed to establish a connection to the motor')
                # self.logger.error('Failed to establish a connection to the motor')
                return  "NOK"
            
    def disconnect(self) -> str:
        """Disconnects the motor

        :return: Disconnection was successful [OK / NOK] #TODO: Talvez possibilitar mais informações na resposta
        :rtype: str
        """
        if self.connected:
            resp = self.driver.disconnect_motor()
            if resp == "OK":
                self.connected = False
                print("Motor disconnected")
                # self.logger.info('Motor Disconnected')
                return "OK"
            else:
                print('Failed to disconnect the motor')
                # self.logger.error('Failed to disconnect the motor')
                return "NOK"

    def ping(self) -> str:
        """Pings the motor to check if it is reachable

        :return: Ping was successful [OK / NOK]
        :rtype: str
        """
        resp = self.driver.ping_motor()
        if resp == "OK":
            print('Ping to motor successful')
        else:
            print('Failed to ping motor')
        return resp

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
        var = self.parameters[ParamIndex]
        if var.IDX in self.driver.methods:  
            resp = self.driver.methods[var.IDX](value)
            if resp == "OK":
                var.VALUE = value
                self.parameters[var.IDX] = var
                return resp
            else:
                raise Exception(f'[Device] Error setting parameter "{var.NAME.upper()}": {resp}')
        else:
            raise ValueError(f'Invalid command. Motor variable "{var.NAME.upper()}" is not defined.')
        
    def get_param(self, ParamIndex: MotorParamsIdx) -> int | str | bool:
        """Reads a parameter value from the motor

        :param ParamIndex: Motor parameter to be read
        :type ParamIndex: MotorParams
        :raises ValueError: If an invalid parameter index is received
        :return: Parameter read from the motor
        :rtype: int | str | bool
        """
        var = self.parameters[ParamIndex]
        if var.IDX in self.driver.methods:
            resp = self.driver.methods[var.IDX]()
            if resp != "NOK":
                var.VALUE = resp
                self.parameters[var.IDX] = var
                return resp
            else:
                raise Exception(f'[Device] Failed to read parameter {var.NAME.upper()} from the motor')
        else:
            raise ValueError(f'Invalid command. Motor variable "{var.NAME.upper()}" is not defined.')

