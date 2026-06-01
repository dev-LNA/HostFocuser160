
from enum import Enum, IntEnum
from PyQt6.QtCore import QObject, pyqtSignal

from typing import NamedTuple
from dataclasses import dataclass

#The Driver must be imported after the definition of "MotoParams"
from src.interface.motor_driver import Driver
from src.interface.driver_DMX import  DriverDMX
from src.interface.driver_AMP import DriverAMP
from src.utils.constants import MotorModels, MotorParamsIdx, ServerCommands, constants, MotorParameter, MotorStatusFlags, MotorAlarmInfo, MotorProgramStatus
from src.utils.signals import PropertySignals, MultiSignal

from src.utils.modbus_regs import dig_inputs_regs


class MotorSignals(QObject):
    connected = pyqtSignal(bool)
    # position = pyqtSignal(int)
    # homing = pyqtSignal(bool)
    # moving = pyqtSignal(bool)
    # status = pyqtSignal(int)
    firmware_status = pyqtSignal(str)
    firmware_version = pyqtSignal(str)

    moving = PropertySignals()
    lim_min = PropertySignals()
    lim_max = PropertySignals()
    position = MultiSignal()
    encoder = pyqtSignal(str)
    initialized = PropertySignals()
    parking = PropertySignals()
    alarm = PropertySignals()

    # progress.value must be true or false indicating if the load bar will be shown in the GUI,
    # progress.string must be the value of the progress in percentage 
    progress = MultiSignal()    

    

class Motor():

    signals = MotorSignals()

    def __init__(self, model: MotorModels = MotorModels.ARCUS_DMX_ETH, ID: str = '0', ):
        
        # General Information
        self.model = model
        self.driver: Driver
        self.ID: str = ID
        self._firmware_version: str = ''

        self.parameters = {
            MotorParamsIdx.MOTOR_IP : MotorParameter(MotorParamsIdx.MOTOR_IP, "MOTOR_IP", dig_inputs_regs.TX_IP_A, 0),
            MotorParamsIdx.BACKLASH : MotorParameter(MotorParamsIdx.BACKLASH, "BACKLASH", dig_inputs_regs.TX_V74, 0),
            MotorParamsIdx.MAX_POS : MotorParameter(MotorParamsIdx.MAX_POS, "MAX_POS", dig_inputs_regs.TX_V71, 0),
            MotorParamsIdx.PARK_POS : MotorParameter(MotorParamsIdx.PARK_POS, "PARK_POS", dig_inputs_regs.TX_V83, 0),
            MotorParamsIdx.MAX_SPEED : MotorParameter(MotorParamsIdx.MAX_SPEED, "MAX_SPEED", dig_inputs_regs.TX_V75, 0),
            MotorParamsIdx.NORMAL_SPEED : MotorParameter(MotorParamsIdx.NORMAL_SPEED, "NORMAL_SPEED", dig_inputs_regs.TX_V77, 0),
            MotorParamsIdx.LOW_SPEED : MotorParameter(MotorParamsIdx.LOW_SPEED, "LOW_SPEED", dig_inputs_regs.TX_V76, 0),
            MotorParamsIdx.MAX_STEP : MotorParameter(MotorParamsIdx.MAX_STEP, "MAX_STEP", dig_inputs_regs.TX_DUMMY, 0),
            MotorParamsIdx.ACCELERATION : MotorParameter(MotorParamsIdx.ACCELERATION, "ACCELERATION", dig_inputs_regs.TX_V80, 0),
            MotorParamsIdx.DECELERATION : MotorParameter(MotorParamsIdx.DECELERATION, "DECELERATION", dig_inputs_regs.TX_V79, 0),
            MotorParamsIdx.IDLE_CURRENT : MotorParameter(MotorParamsIdx.IDLE_CURRENT, "IDLE_CURRENT", dig_inputs_regs.TX_V78, 0),
            MotorParamsIdx.RUN_CURRENT : MotorParameter(MotorParamsIdx.RUN_CURRENT, "RUN_CURRENT", dig_inputs_regs.TX_V81, 0),
            MotorParamsIdx.ACC_CURRENT : MotorParameter(MotorParamsIdx.ACC_CURRENT, "ACC_CURRENT", dig_inputs_regs.TX_V82, 0),
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
        self._status: int = 0

        self.SASTAT: int = 0

        self._alarm_info: str = ''

        if model == MotorModels.ARCUS_DMX_ETH:
            self.driver = DriverDMX(self)
        elif model == MotorModels.AMP_MOTOR:
            self.driver = DriverAMP(self)
        else:
            raise RuntimeError(f'Motor driver model {model} is invalid')
        
        self.driver.driver_comm.status.connect(lambda val: setattr(self, 'connected', val))

#region  ========== PROPERTIES ========== # 

    @property
    def teste_property(self):
        print("***PROPRIEDADE DO MOTOR RETORNADA***")
    @teste_property.setter
    def teste_property(self, value:bool):
        print(f"***PROPRIEDADE DO MOTOR ALTERADA PARA {value}! ***")

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
                self.signals.moving.emit(val, "statusLed", "OFF")


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
        if self.initialized:
            if pos != self._position:
                self.last_position = self._position
                self._position = pos
                self.signals.position.emit(pos)
        else:
            self.signals.position.emit(pos, "???")
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
            # self.disconnect()
            self.driver._reset_communication()
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
        if self.initialized:
            if encoder_pos != self._encoder:
                self._encoder = encoder_pos
                self.signals.encoder.emit(str(self._encoder))
        else:
            self.signals.encoder.emit("???")

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
            # self.disconnect()
            self.driver._reset_communication()
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
                if self._parking:
                    self.signals.parking.emit(self._parking, "statusLed", "WAIT")
                else:
                    self.signals.parking.emit(self._parking, "statusLed", "OFF")
            return self._parking
        except Exception as e:
            # self.disconnect()
            self.driver._reset_communication()
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
                    self.signals.initialized.emit(False, "statusLed", "OFF")
            return self._initialized
        except Exception as e:
            # self.disconnect()
            self.driver._reset_communication()
            raise e
            # return f'[Device] Could not retrieve initialized information: Error -> {str(e)}'
    
    @property
    def alarm(self) -> bool:
        """Motor alarm status
        The motor alarm is read using the 'status' property, this is only a way to
        read the alarm.
        
        :getter: Returns the motor alarm status
        :rtype: bool
        """
        return self._alarm
    @alarm.setter
    def alarm(self, val):    #TODO: Talvez já colocar um tratamento para checar qual é o alarme

        # try:
            # val = self.driver.read_alarm_status()
        if val != self._alarm:
            self._alarm = val
            if self._alarm:
                self.alarm_info = self.driver.parse_alarm_info()
                self.signals.alarm.emit(True, "statusLed", "NOK")
            else:
                self.signals.alarm.emit(False, "statusLed", "OFF")

        return self._alarm
        # except Exception as e:
        #     self.disconnect()
        #     raise e
    
    @property
    def alarm_info(self):
        return self._alarm_info
    @alarm_info.setter
    def alarm_info(self, msg: str) -> str:
        # self._alarm_info = "Alarm details: "
        # for error in msg:
        #     self._alarm_info += error.name + " / "
        
        # self._alarm_info = self._alarm_info.removesuffix(" / ")
        
        return self._alarm_info

    @property
    def firmware_status(self) -> str: 
        try:
            val = self.driver.read_firmware_status()
            if val != self._firmware_status:
                self._firmware_status = val
                self.signals.firmware_status.emit(self._firmware_status)
            return self._firmware_status
        except Exception as e:
            # self.disconnect()
            self.driver._reset_communication()
            raise e
            # return f'[Device] Could not retrieve firmware status information: Error -> {str(e)}'

    @property
    def firmware_version(self) -> str:
        try:
            val = self.driver.read_firmware_version()
            if val != self._firmware_version:
                self._firmware_version = val
                self.signals.firmware_version.emit(self._firmware_version)
            return self._firmware_version
        except Exception as e:
            # self.disconnect()
            self.driver._reset_communication()
            raise e

#endregion


#region  ========== METHODS ========== # 

                                        #TODO: A formatação do status é diferente, então vai ser necessário padronizar isso 
    def update_status(self) -> int:    #       entre os motores e fazer com que a resposta de 'read_satus' seja independente do motor.
        """Reads motor status. If the value changes emits a signals.

        :return: motor status
        :rtype: str
        """
        #TODO: Adicionar os status específicos do IAG
        try:
            if not self._homing and not self._initialized:
                self.signals.initialized.emit(False, "statusLed", "OFF")

            motor_status = self.driver.read_status()
            if motor_status != MotorStatusFlags.INVALID:
                self._status = motor_status

                if(motor_status & MotorStatusFlags.MOVING):
                    self.is_moving = True
                else:
                    self.is_moving = False

                if(motor_status & MotorStatusFlags.LIM_MIN):
                        self.signals.lim_min.emit(True, "statusLed", "NOK")
                else:
                    if self._position < 0:
                        self.signals.lim_min.emit(False, "statusLed", "WAIT")
                    else:
                        self.signals.lim_min.emit(False, "statusLed", "OFF")

                if(motor_status & MotorStatusFlags.LIM_MAX):
                        self.signals.lim_max.emit(True, "statusLed", "NOK")
                else:
                    if self._position > int(self.parameters[MotorParamsIdx.MAX_POS].VALUE):
                        self.signals.lim_max.emit(False, "statusLed", "WAIT")
                    else:
                        self.signals.lim_max.emit(False, "statusLed", "OFF")

                self.alarm = self.driver.read_alarm_status()                # Reads the alarm status
                # if(motor_status & MotorStatusFlags.ALARM):    
                #     self.alarm = True
                # else:
                #     self.alarm = False

                return self._status
            else:
                raise ValueError('Invalid Motor Status Reading')
        except Exception as e:
            # self.disconnect()
            self.driver._reset_communication()
            raise e
        

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
                    self.connected = True
                    # self.ID = '2'                                                 #TODO: Cada motor deve ter um ID específico?
                    self.firmware_version

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
        # The driver may not be connected but trying to connect the motor
        if self.connected or self.driver is not None:
            resp = "NOK"
            while resp != "OK":
                resp = self.driver.disconnect_motor()
            if resp == "OK":
                # self._connected = False
                # self.signals.connected.emit(self._connected)
                self.connected = False
                print("Motor disconnected")

                self._reset_state()

                return "OK"
            # else:
            #     print('Failed to disconnect the motor')
            #     return "NOK"
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
        try:
            resp = self.driver.ping_motor()

        except Exception as e:
            print('Failed to ping the motor')
            raise e

        if resp == "OK":
            print('Ping to motor successful')
            return True
        else:
            print('Failed to ping motor')
            return False

    def _update_motor_params(self):
        """Sends to the motor/CLP the updated values of the configurations"""
        # TODO: Por enquanto somente é válido para o motor do IAG

        self.driver._update_all_parameters()


        # if self.model == MotorModels.AMP_MOTOR:
        #     for param_idx in MotorParamsIdx:
        #         if param_idx != MotorParamsIdx.MOTOR_IP:
        #             self.set_param(param_idx, int(float(self.motor.parameters[param_idx].VALUE)))

        #     for param_idx in MotorParamsIdx:
        #         print(f"{self.parameters[param_idx].NAME} - {self.motor.parameters[param_idx].VALUE}")

            # self.motor.set_param(MotorParamsIdx.BACKLASH, Config.backlash)
            # self.logger.info("Motor parameters initialized")

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
            # self.disconnect()
            self.driver._reset_communication()
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
            # self.disconnect()
            self.driver._reset_communication()
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
            # self.disconnect()
            self.driver._reset_communication()
            raise e


#endregion