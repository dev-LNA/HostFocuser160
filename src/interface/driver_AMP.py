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
from src.utils.constants import constants, MotorStatusFlags
from src.utils.modbus_regs import RegsInfo, RegType, coils_regs, dig_inputs_regs, DB_size, CLP_Owned, TwosComplementReg

import time



class DriverAMP(Driver):
    def __init__(self, model):
        super().__init__(model)

        self.mb_server: ModbusServer = None
    
    

    def connect_motor(self, max_retries: int = 5, delay: float = 0.1) -> str:
        """Precisa ser implementada pelo driver"""
        retries = 0
        _con = False

        dataBank_config = MB_DataBank(coils_size=DB_size.COIL_LAST_ADDRESS+1, coils_default_value=False,        #|      
                d_inputs_size=DB_size.DI_LAST_ADDRESS+1, d_inputs_default_value=False,               #|  Config value for the modbus data bank.
                h_regs_size=0, h_regs_default_value=0,                          #|  
                i_regs_size=0, i_regs_default_value=0)                          #|
                
        while retries < max_retries and not _con:
            try:
                # host => Server IP Address
                self.mb_server = ModbusServer(host='0.0.0.0', port=5005 ,no_block=True, data_bank=dataBank_config)
                self.mb_server.start()
                self.mb_server.signal_stop.connect(self.disconnect_motor)
                self.mb_run_thread = Thread(target=self.mb_server.run)
                self.mb_run_thread.start()
                self.mb_server.running = True
                _con = True
                self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])  #| TX_WAIT e TX_BUSY precisam ser 
                self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [False])  #| inicializados em 0
                print("Modbus server started")
                return "OK"
            except Exception as e:
                print(f"Error starting modbus server: {e}")

    
    def disconnect_motor(self) -> str:
        """Closes the modbus server connection"""
        try:
            if self.mb_server:
                print("Closing modbus server...")
                self.mb_server.stop_server = True
                self.mb_run_thread.join()
                self.mb_server.stop()
                self.mb_server = None
                print("Server closed")
                return "OK"
        except Exception as e:
            raise RuntimeError(f"Error closing modbus server -> {str(e)}")

    
    def ping_motor(self) -> str:
        """Creates a dummy connection to the motor, just to verify if the modbus server
          is correctly connected and the handshake was successfully made."""
        if self.mb_server is None:                  #   If the server was not instantiated
            # self.running = True                     #   Instantiates and starts the server (needed to read handshake)


            retries = 0
            max_retries = 5         #TODO: colocar isso no arquivo de configuração config_IAG.toml
            _con = False
            # while retries < max_retries and not _con:
            try:
                dataBank_config = MB_DataBank(coils_size=DB_size.COIL_LAST_ADDRESS+1, coils_default_value=False,        #|      
                                d_inputs_size=DB_size.DI_LAST_ADDRESS+1, d_inputs_default_value=False,               #|  Config value for the modbus data bank.
                                h_regs_size=0, h_regs_default_value=0,                          #|  
                                i_regs_size=0, i_regs_default_value=0)                          #|
                dummy_mb_server = ModbusServer(host=Config.device_ip, port=Config.device_port ,no_block=True, data_bank=dataBank_config)
                dummy_mb_server.start()

                dummy_mb_server_run_thread = Thread(target=dummy_mb_server.run)
                dummy_mb_server_run_thread.start()

                while dummy_mb_server.handshake is False and retries < max_retries:
                    time.sleep(1)             # Delay between retries #TODO: colocar isso no arquivo de configuração config_IAG.toml
                    retries += 1

                # dummy_mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.HANDSHAKE.ADDRESS, [True])  #| TX_WAIT e TX_BUSY precisam ser

                # time.sleep(2)          # Delay to ensure the handshake is read by the client

                # Closes the dummy server connection, since it was only used to verify the handshake, and is not needed anymore.
                print("Closing modbus server...")
                dummy_mb_server.stop_server = True
                dummy_mb_server_run_thread.join()
                dummy_mb_server.stop()
                dummy_mb_server = None

                # If the max retries was reached and the handshake was not made, closes the dummy server and 
                # raises an exception to inform that the handshake was not successful, and the motor is not reachable.
                if retries >= max_retries:
                    print("Max retries reached. Modbus server handshake failed.")
                    # self.logger.error("Max retries reached. Modbus server handshake failed.")

                    raise RuntimeError("Error pinging modbus server: Max retries reached. Modbus server handshake failed.")

                # If the handshake was successful, continues without raising an exception
                #  and informs that the motor is reachable.
                return "OK"
            except Exception as e:
                print(str(e))
                raise (e)

    
    def conv_position(self, encoder_pos: int = None) -> int:
        """Reads motor encoder position and converts to microns

        :raises ValueError: If the reading is not valid
        :return: _description_
        :rtype: int | Exception
        """
        if encoder_pos is None:
            encoder_pos = self.read_encoder()
        pos = int(round(encoder_pos / Config.enc_2_microns))
        return pos
    
    def set_position(self, position: int) -> str:
        """Moves the motor to a specific position in microns

        :param position: Target position in microns
        :type position: int
        :raises ValueError: If the position is out of range
        :return: _description_
        :rtype: str | Exception
        """
        if position < 0 or position > Config.max_pos:
            raise ValueError(f"Position value {position} is out of range (0 - {Config.max_pos} microns)")

        pos_conv = int(round((Config.enc_2_microns * position)))




    
    def read_encoder(self) -> int:
        """Reads encoder value from the motor and 
        returns it as an integer"""
        response = self.mb_server._conv_reg_to_value(coils_regs.RX_EX, self.mb_server.db_shadow)
        return response
    
    def read_homing(self) -> bool:
        """Precisa ser implementada pelo driver"""
        return False

    
    def read_parking(self) -> bool:
        """Precisa ser implementada pelo driver"""
        return False

    
    def read_initialized(self) -> bool:
        """Precisa ser implementada pelo driver"""
        return False

    
    def read_status(self) -> int:
        """Precisa ser implementada pelo driver"""
        return MotorStatusFlags.ENABLED  #TODO: Implementar a leitura do status do motor, e retornar os flags correspondentes




    
    def param_IP(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return Config.device_ip

    
    def param_backlash(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.backlash)

    
    def param_max_pos(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.max_pos)

    
    def param_park_pos(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.park_pos)

    
    def param_max_speed(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.max_speed)

    
    def param_normal_speed(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.normal_speed)

    
    def param_low_speed(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.low_speed)

    
    def param_max_step(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.max_step)

    
    def param_acceleration(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.acceleration)

    
    def param_deceleration(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.deceleration)

    
    def param_idle_current(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.idle_current)

    
    def param_run_current(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.run_current)

    
    def param_acc_current(self, value: int | str | bool = None) -> str:
        """Precisa ser implementada pelo driver"""
        return str(Config.acc_current)

    
    def read_firmware_version(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...  

    
    def read_alarm_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...      

    
    def parse_alarm_info(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...
    
    def read_firmware_status(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...
            
    
    def sendCommand(self, command: str) -> str:
        """Precisa ser implementada pelo driver"""
        ...
    
    def move_to(self, pos: str) -> str:
        """Precisa ser implementada pelo driver"""
        ...     
    
    def focus_in(self, speed: str) -> str:
        """Precisa ser implementada pelo driver""" 
        ...
    
    def focus_out(self, speed: str) -> str:
        """Precisa ser implementada pelo driver""" 
        ...     
    
    def halt(self) -> str:
        """Precisa ser implementada pelo driver""" 
        ...         
    
    def home(self) -> str:
        """Precisa ser implementada pelo driver"""
        ...     
    
    def park(self) -> str:
        """Precisa ser implementada pelo driver""" 
        ...
        

    def _write(self, value: int | bool, reg: RegsInfo):
        
        # When the register size is 1 the value must be 0, 1 or boolean
        if (reg.SIZE==1 and not ( ( (value==0) or (value==1) or type(value) is bool ) )):
            raise ValueError(f"Cannot write {value} to {reg.TYPE.name}:{reg.ADDRESS}. This Register supports only {reg.SIZE} bit(s).")
        
        # When a boolean was sent to a register that has more bits
        if ( type(value) is bool ) and ( reg.SIZE != 1):
            raise ValueError(f"Cannot write a boolean to {reg.TYPE.name}:{reg.ADDRESS}. This Register has {reg.SIZE} bits")

        tries = 0
        max_tries =5
        # Tries 'max_tries' times to send the data
        while tries < max_tries:
            time.sleep(0.1)
            # The application can only write new data if the CLP is not reading
            if not self.mb_server.data_bank.get_coils(coils_regs.RX_READING.ADDRESS, coils_regs.RX_READING.SIZE)[0]:
                if reg.TYPE is RegType.DISCRETE_INPUT:

                    self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [True])
                    time.sleep(0.05)
                    if (type(value) is bool) or (reg.SIZE==1 and ( (value==0) or (value==1) ) ):                # If the value is a bool or the register has only one bit than no conversion is needed
                        self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS, [value])
                    else:                                                                                       #| If the register has multiple bits than the value must be converted
                        num_bits = self.mb_server._conv_num_bits(value, reg.SIZE)                                         #| The conversion already considers negative values as two's complement
                        if reg.SIZE == 8:                                                                       
                            self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits)          # If the register is only 8 bits the value is saved directly to the register
                        else:                                                                                   
                            self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits[16:])     #|  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address   
                            self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS+16, num_bits[:16])  #| and the lower bits must be saved to next 16 bits

                    self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])  # Informs CLP that there is a valid data ready for readi
                    self.mb_server.wait_confirmation(reg)
                break
            else:
                tries += 1
        if tries == max_tries:
            print(f'Failed to send {value} to register {reg.TAG} after {tries} tries')
            # raise RuntimeError(f'Failed to send {value} to register {reg.TAG} after {tries} tries')
