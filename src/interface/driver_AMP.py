from src.interface.motor_driver import Driver
from src.utils.constants import MotorProgramStatus

from PyQt6.QtCore import QObject, pyqtSignal

from src.interface.modbus_server import ModbusServer
# from pyModbusTCP.server import DataBank
from src.interface.modbus_data_bank import MB_DataBank

from logging import Logger
from threading import Lock, Timer, Thread

from src.core.config import Config
from src.core.exceptions import DriverException
from src.utils.constants import constants
from src.utils.modbus_regs import RegsInfo, RegType, coils_regs, dig_inputs_regs, DB_size, CLP_Owned, TwosComplementReg

import time



class DriverAMP(Driver):
    def __init__(self, model):
        super().__init__(model)

        self.mb_server: ModbusServer = None
    
    




    @property
    def running(self):
        """Indicates the modbus server status

        Returns:
            bool: Modbus server status
        """
        return self.mb_server.running
    
    @running.setter
    def running(self, status: bool, max_retries=5, delay=.1):
        """Starts the modbus server

        Args:
            connect (bool): Sets the connected state
            max_retries (int, optional): Max attempts to start the modbus server. Defaults to 5.
            delay (float, optional): Delay between attempts. Defaults to .1.
        """
        retries = 0
        _con = False
        while retries < max_retries and not _con:
            try:
                dataBank_config = MB_DataBank(coils_size=DB_size.COIL_LAST_ADDRESS+1, coils_default_value=False,        #|      
                                d_inputs_size=DB_size.DI_LAST_ADDRESS+1, d_inputs_default_value=False,               #|  Config value for the modbus data bank.
                                h_regs_size=0, h_regs_default_value=0,                          #|  
                                i_regs_size=0, i_regs_default_value=0)                          #|
                self.mb_server = ModbusServer(host='0.0.0.0', port=5005 ,no_block=True, data_bank=dataBank_config)
                self.mb_server.start()
                self.mb_server.signal_stop.connect(self._stop_server)
                self.mb_run_thread = Thread(target=self.mb_server.run)
                self.mb_run_thread.start()
                self.mb_server.running = True
                _con = True
                self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])  #| TX_WAIT e TX_BUSY precisam ser 
                self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [False])  #| inicializados em 0
                print("Modbus server started")
            except Exception as e:
                print(f"Error starting modbus server: {e}")















    def connect_motor(self, max_retries: int = 5, delay: float = 0.1) -> str:
        """Precisa ser implementada pelo driver"""
        ...

    
    def disconnect_motor(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...

    
    def ping_motor(self) -> str:
        """Instantiates and starts the server"""
        if self.mb_server is None:                  #   If the server was not instantiated
            self.running = True                     #   Instantiates and starts the server (needed to read handshake)
            
        if self.running:                         #   Verifies if the modbus server was correctly connected
            if self.mb_server.handshake:                # If handshake was made
                return True                             # Informs that the motor is reachable
        
        return False                                #   Returns False otherwise
    
    
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