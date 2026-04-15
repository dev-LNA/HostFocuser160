from abc import ABC, abstractmethod
from typing import NamedTuple

from src.utils.motor import MotorParamsIdx


class Driver(ABC):
    def __init__(self, model: str):
        self._model = model

        self.methods = {
            MotorParamsIdx.MOTOR_IP : self.param_IP,
            MotorParamsIdx.BACKLASH : self.param_backlash,
            MotorParamsIdx.MAX_POS : self.param_max_pos,
            MotorParamsIdx.PARK_POS : self.param_park_pos,
            MotorParamsIdx.MAX_SPEED : self.param_max_speed,
            MotorParamsIdx.NORMAL_SPEED : self.param_normal_speed,
            MotorParamsIdx.LOW_SPEED : self.param_low_speed 
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
    def read_position(self) -> int:
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
    def read_status(self) -> str:
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
    def read_firmware_version(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...  

    @abstractmethod
    def read_firmware_status(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...
            
    @abstractmethod
    def sendCommand(self, command: str) -> str:
        """Precisa ser implementada pelo driver"""
        

    def _store_to_flash(self) -> str:
        """Pode ser implementada pelo driver caso necessário"""
        raise NotImplementedError(f'Motor "{self._model}" driver do not implement "{self._store_to_flash.__name__}" method.')

    def is_convertible_to_int(self, value):
        try:
            int(value)
            return True
        except:
            return False
    

    def __repr__(self):
        return f"<Driver do motor {self._model}>"