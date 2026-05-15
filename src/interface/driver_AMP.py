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
        ...
    
    
    def conv_position(self, val_enc: int = None) -> int:
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
    ...

    
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

    
    def param_max_step(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    
    def param_acceleration(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    
    def param_deceleration(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    
    def param_idle_current(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    
    def param_run_current(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    
    def param_acc_current(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
    ...

    
    def read_firmware_version(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...  

    
    def read_alarm_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...      

    
    def parse_alarm_info(self) -> bool:
        """Precisa ser implementada pelo driver"""

    
    def read_firmware_status(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...
            
    
    def sendCommand(self, command: str) -> str:
        """Precisa ser implementada pelo driver"""
             
    
    def move_to(self, pos: str) -> str:
        """Precisa ser implementada pelo driver"""
             
    
    def focus_in(self, speed: str) -> str:
        """Precisa ser implementada pelo driver""" 
             
    
    def focus_out(self, speed: str) -> str:
        """Precisa ser implementada pelo driver""" 
             
    
    def halt(self) -> str:
        """Precisa ser implementada pelo driver""" 
             
    
    def home(self) -> str:
        """Precisa ser implementada pelo driver"""
             
    
    def park(self) -> str:
        """Precisa ser implementada pelo driver""" 