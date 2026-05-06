from src.interface.motor_driver import Driver
from src.utils.constants import MotorProgramStatus

class DriverAMP(Driver):
    def __init__(self, model):
        super().__init__(model)
    
    
    def connect_motor(self, max_retries: int = 5, delay: float = 0.1) -> str:
        """Precisa ser implementada pelo driver"""
        ...

    def disconnect_motor(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...

    def ping_motor(self) -> str:
        """Precisa ser implementada pelo driver"""
        return "OK"

    def conv_position(self) -> int:
        """Precisa ser implementada pelo driver"""
        ...

    def read_encoder(self) -> int:
        """Precisa ser implementada pelo driver"""
    ...

    def read_homing(self) -> bool:
        """Precisa ser implementada pelo driver"""
    ...

    def read_parking(self) -> bool:
        """Precisa ser implementada pelo driver"""
        return False

    def read_initialized(self) -> bool:
        """Precisa ser implementada pelo driver"""
    ...

    def read_status(self) -> int:
        """Precisa ser implementada pelo driver"""
    ...

    def set_position(self, value: int) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    def param_IP(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    def param_backlash(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    def param_max_pos(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    def param_park_pos(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    def param_max_speed(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    def param_normal_speed(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    def param_low_speed(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    def read_firmware_status(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...