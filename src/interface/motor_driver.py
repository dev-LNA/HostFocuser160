from abc import ABC, abstractmethod
from typing import NamedTuple

from PyQt6.QtCore import pyqtSignal, QObject
from src.utils.constants import MotorParamsIdx, ServerCommands

class DriverCommunicator(QObject):
    status = pyqtSignal(bool)

class Driver(ABC):
    def __init__(self, model: str):
        self._model = model

        self.driver_comm = DriverCommunicator()

        self.param_methods = {
            MotorParamsIdx.MOTOR_IP : self.param_IP,
            MotorParamsIdx.BACKLASH : self.param_backlash,
            MotorParamsIdx.MAX_POS : self.param_max_pos,
            MotorParamsIdx.PARK_POS : self.param_park_pos,
            MotorParamsIdx.MAX_SPEED : self.param_max_speed,
            MotorParamsIdx.NORMAL_SPEED : self.param_normal_speed,
            MotorParamsIdx.LOW_SPEED : self.param_low_speed,
            MotorParamsIdx.MAX_STEP : self.param_max_step,
            MotorParamsIdx.ACCELERATION : self.param_acceleration,
            MotorParamsIdx.DECELERATION : self.param_deceleration,
            MotorParamsIdx.IDLE_CURRENT : self.param_idle_current,
            MotorParamsIdx.RUN_CURRENT : self.param_run_current,
            MotorParamsIdx.ACC_CURRENT : self.param_acc_current
        }

        self.command_methods = {
            ServerCommands.MOVE : self.move_to,
            ServerCommands.FOCUSIN : self.focus_in,
            ServerCommands.FOCUSOUT : self.focus_out,
            ServerCommands.HALT : self.halt,
            ServerCommands.HOME : self.home,
            ServerCommands.PARK : self.park
        }    


    @abstractmethod
    def connect_motor(self, max_retries: int = 5, delay: float = 0.1) -> str:
        """Precisa ser implementada pelo driver"""
        ...

    @abstractmethod
    def disconnect_motor(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...

    @abstractmethod
    def ping_motor(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...
    
    @abstractmethod
    def conv_position(self, val_enc: int = None) -> int:
        """Precisa ser implementada pelo driver"""
        ...
    
    @abstractmethod
    def read_encoder(self) -> int:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def read_homing(self) -> bool:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def read_parking(self) -> bool:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def read_initialized(self) -> bool:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def read_status(self) -> int:
        """Precisa ser implementada pelo driver"""
    ...


    @abstractmethod
    def set_position(self, value: int) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_IP(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_backlash(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_max_pos(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_park_pos(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_max_speed(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_normal_speed(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_low_speed(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_max_step(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_acceleration(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_deceleration(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_idle_current(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_run_current(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_acc_current(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def read_firmware_version(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...  

    @abstractmethod
    def read_alarm_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...      

    @abstractmethod
    def parse_alarm_info(self) -> bool:
        """Precisa ser implementada pelo driver"""

    @abstractmethod
    def read_firmware_status(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...
            
    @abstractmethod
    def sendCommand(self, command: str) -> str:
        """Precisa ser implementada pelo driver"""
             
    @abstractmethod
    def move_to(self, pos: str) -> str:
        """Precisa ser implementada pelo driver"""
             
    @abstractmethod
    def focus_in(self, speed: str) -> str:
        """Precisa ser implementada pelo driver""" 
             
    @abstractmethod
    def focus_out(self, speed: str) -> str:
        """Precisa ser implementada pelo driver""" 
             
    @abstractmethod
    def halt(self) -> str:
        """Precisa ser implementada pelo driver""" 
             
    @abstractmethod
    def home(self) -> str:
        """Precisa ser implementada pelo driver"""
             
    @abstractmethod
    def park(self) -> str:
        """Precisa ser implementada pelo driver""" 



    def _store_to_flash(self) -> str:
        """Pode ser implementada pelo driver caso necessário"""
        print("Motor driver does not implement flash storage. Ignoring command.")

    def is_convertible_to_int(self, value):
        try:
            int(value)
            return True
        except:
            return False
    

    def __repr__(self):
        return f"<Driver do motor {self._model}>"