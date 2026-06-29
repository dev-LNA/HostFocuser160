from abc import ABC, abstractmethod
from typing import NamedTuple
from enum import IntFlag

from PyQt6.QtCore import pyqtSignal, QObject, pyqtSlot
from src.utils.constants import MotorParamsIdx, ServerCommands, FocuserSignalsNames
from src.utils.signals import PropertySignals
from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.utils.motor import Motor

    
@dataclass
class InternalState():
    focus_in: bool = False
    focus_out: bool = False
    park: bool = False
    homing: bool = False

class DriverCommunicator(QObject):
    status = pyqtSignal(bool)

    run_focus_in = PropertySignals()
    run_focus_out = PropertySignals()
    run_park = PropertySignals()
    manual_movement = PropertySignals()

    timeout = pyqtSignal(bool)

    manual_movement.setObjectName(FocuserSignalsNames.MANUAL_MOVEMENT)
    run_focus_in.setObjectName(FocuserSignalsNames.RUN_FOCUS_IN)
    run_focus_out.setObjectName(FocuserSignalsNames.RUN_FOCUS_OUT)
    run_park.setObjectName(FocuserSignalsNames.RUN_PARK)


class Driver(ABC):
    def __init__(self, motor: Motor):
        self._model = motor.model

        self.motor = motor

        self.driver_comm = DriverCommunicator()

        self.current_state = InternalState()

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
    
    @property
    @abstractmethod
    def focus_out_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...
    @focus_out_status.setter
    def focus_out_status(self, val:bool):
        """Precisa ser implementada pelo driver"""
        ...

    @property
    @abstractmethod
    def focus_in_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...
    @focus_in_status.setter
    def focus_in_status(self, val:bool):
        """Precisa ser implementada pelo driver"""
        ...

    @property
    @abstractmethod
    def park_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...
    @park_status.setter
    def park_status(self, val:bool):
        """Precisa ser implementada pelo driver"""



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
    def conv_position_show(self, val_enc: int | None = None, type: str = "int") -> int | float:
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
    def param_IP(self, value: str | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_backlash(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_max_pos(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_park_pos(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_max_speed(self, value: int | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_normal_speed(self, value: int | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_low_speed(self, value: int | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_max_step(self, value: int | str | bool | None = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_acceleration(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_deceleration(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_idle_current(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_run_current(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    @abstractmethod
    def param_acc_current(self, value: int | float | None = None, converted:bool = False) -> str | None:
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
    def parse_alarm_info(self) -> str:
        """Precisa ser implementada pelo driver"""

    @abstractmethod
    def read_firmware_status(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...
            
    @abstractmethod
    def sendCommand(self, command: str) -> str:
        """Precisa ser implementada pelo driver"""
        ...
             
    @abstractmethod
    def move_to(self, pos: str) -> str:
        """Precisa ser implementada pelo driver"""
        ...
             
    @abstractmethod
    def focus_in(self, speed: str | None = None) -> str:
        """Precisa ser implementada pelo driver""" 
        ...
             
    @abstractmethod
    def focus_out(self, speed: str | None = None) -> str:
        """Precisa ser implementada pelo driver""" 
        ...
             
    @abstractmethod
    def halt(self) -> str:
        """Precisa ser implementada pelo driver""" 
        ...
             
    @abstractmethod
    def home(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...
             
    @abstractmethod
    def park(self) -> str:
        """Precisa ser implementada pelo driver""" 
        ...

    def _extract_flags_info(self, input:int, flags_type:IntFlag, separator: str = "&") -> str:
        """Pode ser implementado pelo driver caso necessário"""
        ...

    def _update_all_parameters(self) -> str:
        """Pode ser implementado pelo driver caso necessário"""
        ...


    def _reset_communication(self):
        """Pode ser implementada pelo driver caso necessário"""
        print("*** Resetting communication...\n\n")
        ...

    def _store_to_flash(self) -> str | None:
        """Pode ser implementada pelo driver caso necessário"""
        print("Motor driver does not implement flash storage. Ignoring command.")
        return None

    def is_convertible_to_int(self, value):
        try:
            int(value)
            return True
        except:
            return False
    

    def __repr__(self):
        return f"<Driver do motor {self._model}>"