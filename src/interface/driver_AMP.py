from abc import abstractmethod

from src.interface.motor_driver import Driver
from src.utils.constants import MotorProgramStatus

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.interface.modbus_server import IAGModbusServer #, TimeoutCheck
# from pyModbusTCP.server import DataBank
from src.interface.modbus_data_bank import MB_DataBank

from threading import Lock, Thread, Timer

from src.core.config import Config
from src.core.exceptions import DriverException
from src.utils.constants import constants, MotorStatusFlags, MotorParamsIdx, MotorAlarmInfo, motor_program_errors_mask, motor_alc_errors_mask, Conversion, TimeDelays
from src.utils.modbus_regs import RegsInfo, RegType, coils_regs, dig_inputs_regs, DB_size, CLP_Mirror, TwosComplementReg, param_vars, holding_regs, PackCMDFlags, PackStatusFlags, PackRSTFlags

from enum import IntFlag
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.utils.motor import Motor


import time



class DriverAMP(Driver):
    def __init__(self, motor: Motor):
        super().__init__(motor)

        self.mb_server: IAGModbusServer | None = None


    @property
    def focus_out_status(self) -> bool:
        return self.current_state.focus_out
    @focus_out_status.setter
    def focus_out_status(self, val:bool):
        if val != self.current_state.focus_out:
            self.current_state.focus_out = val
            if val:
                self.driver_comm.run_focus_out.emit(True, "statusLed", "WAIT")
            else:
                self.driver_comm.run_focus_out.emit(False, "statusLed", "OFF")

    @property
    def focus_in_status(self) -> bool:
        return self.current_state.focus_in
    @focus_in_status.setter
    def focus_in_status(self, val:bool):
        if val != self.current_state.focus_in:
            self.current_state.focus_in = val
            if val:
                self.driver_comm.run_focus_in.emit(True, "statusLed", "WAIT")
            else:
                self.driver_comm.run_focus_in.emit(False, "statusLed", "OFF")

    @property
    def park_status(self) -> bool:
        return self.current_state.park
    @park_status.setter
    def park_status(self, val:bool):
        if val != self.current_state.park:
            self.current_state.park = val
            if val:
                self.driver_comm.run_park.emit(True, "statusLed", "WAIT")
            else:
                self.driver_comm.run_park.emit(False, "statusLed", "OFF")

    def connect_motor(self, max_retries: int = 5, delay: float = 0.1) -> str:
        """Precisa ser implementada pelo driver"""
        retries = 0
        _con = False

        while retries < max_retries and not _con:
            try:
                if self.mb_server:
                    self.mb_server.timeout.reset()
                    self.mb_server.timeout.running = True   # Starts timeout counter

                    self.mb_server.running = True
                    _con = True

                print("Modbus server started")
                return "OK"
            except Exception as e:
                print(f"Error starting modbus server: {e}")
                return "NOK"
        return "NOK"

    def disconnect_motor(self) -> str:
        """Closes the modbus server connection"""
        try:
            if self.mb_server:
                print("Closing modbus server...")
                # time.sleep(0.2)  # Delay 
                self.mb_server.stop_server = True
                self.mb_run_thread.join()
                self.mb_server.stop()
                self.mb_server = None
                print("Server closed")
                return "OK"
            else:
                return "OK"
        except Exception as e:
            raise RuntimeError(f"Error closing modbus server -> {str(e)}")

    
    def ping_motor(self) -> str:
        """Creates a dummy connection to the motor, just to verify if the modbus server
          is correctly connected and the handshake was successfully made."""
        
        retries = 0
        max_retries = 5         #TODO: colocar isso no arquivo de configuração config_IAG.toml
        
        if self.mb_server is None:                  #   If the server was not instantiated
            # self.running = True                     #   Instantiates and starts the server (needed to read handshake)



            _con = False
            # while retries < max_retries and not _con:
            try:
                holding_regs_size = holding_regs[-1].ADDRESS + holding_regs[-1].SIZE + 1

                dataBank_config = MB_DataBank(coils_size=DB_size.COIL_LAST_ADDRESS+1, coils_default_value=False,                #|      
                                d_inputs_size=DB_size.DI_LAST_ADDRESS+1, d_inputs_default_value=False,                          #|  Config value for the modbus data bank.
                                h_regs_size=holding_regs_size, h_regs_default_value=0,                                          #|  
                                i_regs_size=0, i_regs_default_value=0, allowed_ip=Config.clp_ip)                                                          #|
                self.mb_server = IAGModbusServer(data_bank=dataBank_config, host=Config.device_ip, port=Config.device_port ,no_block=True,
                                                 timeout_callback_function=self._reset_communication)

                self.mb_server.mb_comm.task_progress.connect(lambda value: self.motor.signals.progress.string.emit(value))

                self.motor.signals.moving.status.connect(self._check_normal_speed)

                self.mb_server.start()

                self.mb_run_thread = Thread(target=self.mb_server.run)
                self.mb_run_thread.start()

                while self.mb_server.handshake is False and retries < max_retries:
                    time.sleep(TimeDelays.RETRY_TIMEOUT)             # Delay between retries #TODO: colocar isso no arquivo de configuração config_IAG.toml
                    retries += 1
                # If the max retries was reached and the handshake was not made, closes the dummy server and 
                # raises an exception to inform that the handshake was not successful, and the motor is not reachable.
                if retries >= max_retries:
                    print("Max retries reached. Modbus server handshake failed.")
                    # self.logger.error("Max retries reached. Modbus server handshake failed.")
                    if isinstance(self.mb_server.data_bank, MB_DataBank) and self.mb_server.data_bank.ping_allowed == False:
                        raise ConnectionRefusedError(f"Modbus server connection to IP '{self.mb_server.data_bank.client_info.address}' is not allowed")
                    
                    raise RuntimeError("Error pinging modbus server: Max retries reached. Modbus server handshake failed.")

                # If the handshake was successful, continues without raising an exception
                #  and informs that the motor is reachable.
                return "OK"
            except Exception as e:
                print(str(e))
                raise (e)
            
        else:
            try:
                while self.mb_server.handshake is False and retries < max_retries:
                    time.sleep(TimeDelays.RETRY_TIMEOUT)             # Delay between retries #TODO: colocar isso no arquivo de configuração config_IAG.toml
                    retries += 1
                    print(f"***** HANDSHAKE VALUE == {self.mb_server.data_bank.get_coils(coils_regs.HANDSHAKE.ADDRESS, 1)}")
                if retries >= max_retries:
                    print("Max retries reached. Modbus server handshake failed.")
                    # self.logger.error("Max retries reached. Modbus server handshake failed.")
                    raise RuntimeError("Error pinging modbus server: Max retries reached. Modbus server handshake failed.")
                return "OK"
            except Exception as e:
                print(str(e))
                raise (e)

    def _check_normal_speed(self, moving:bool):
        if moving and self.mb_server:
            val = self.mb_server.data_bank.get_holding_registers(holding_regs.TX_V77.ADDRESS, holding_regs.TX_V77.SIZE)
            if val != Config.normal_speed:
                print('**********Setting normal speed back to original value**********')
                self.mb_server.write_param(holding_regs.TX_V77, self._convert_speed(Config.normal_speed))
    
    def conv_position_show(self, encoder_pos: int | None = None, type: str = "int") -> int | float | None:
        """Reads motor encoder position and converts to microns
        Used for PUB and display values

        :raises ValueError: If the reading is not valid
        :return: _description_
        :rtype: int | Exception
        """
        if encoder_pos is None:
            encoder_pos = self.read_encoder()
        # pos = int(round(encoder_pos / Config.enc_2_microns))
        if encoder_pos is not None:
            max_pos = self.param_max_pos()
            if max_pos:
                if type == "int":
                    # Conversão necessário devido a montagem mecânica
                    
                    pos = int(max_pos) - int(round(encoder_pos * Config.enc_2_microns * Conversion.POSITION_VISUALIZATION))
                else:
                    # Conversão necessário devido a montagem mecânica
                    pos = int(max_pos) - round(encoder_pos * Config.enc_2_microns * Conversion.POSITION_VISUALIZATION, 1)
                return pos
        
        return None
    
    def set_position(self, position: int):
        """ DEPRECATED
        Moves the motor to a specific position in microns

        :param position: Target position in microns
        :type position: int
        :raises ValueError: If the position is out of range
        :return: _description_
        :rtype: str | Exception
        """
        if position < 0 or position > Config.max_pos:
            raise ValueError(f"Position value {position} is out of range (0 - {Config.max_pos} microns)")

        # pos_conv = int(round((Config.enc_2_microns * position)))
        pos_conv = int(round((Config.enc_2_microns / position)))




    
    def read_encoder(self) -> int | None:
        """Reads encoder value from the motor and 
        returns it as an integer"""
        if self.mb_server:
            # response = self.mb_server._conv_reg_to_value(coils_regs.RX_EX, self.mb_server.db_shadow)
            response = self.mb_server.data_bank.get_holding_registers(holding_regs.RX_EX.ADDRESS, holding_regs.RX_EX.SIZE)
            if response:
                encoder_val = (response[1] << 16) | response[0]
                # The encoder val is in two's complement so conversion is needed if bigger than 2^31
                # to show negativa numbers
                if encoder_val >= 2147483648:
                    encoder_val = encoder_val - 4294967296

                return encoder_val
            # return response
            # pass

    def read_homing(self) -> bool | None:
        """Precisa ser implementada pelo driver"""
        if self.mb_server:
            val = self.mb_server.data_bank.get_holding_registers(holding_regs.RX_PACKSTATUS.ADDRESS, holding_regs.RX_PACKSTATUS.SIZE)
            if val:
                return bool(val[0] & PackStatusFlags.RX_V15)


    
    def read_parking(self) -> bool:
        """Precisa ser implementada pelo driver"""
        return False

    
    def read_initialized(self) -> bool | None:
        """Precisa ser implementada pelo driver"""
        if self.mb_server:
            val = self.mb_server.data_bank.get_holding_registers(holding_regs.RX_PACKSTATUS.ADDRESS, holding_regs.RX_PACKSTATUS.SIZE)
            if val:
                return bool(val[0] & PackStatusFlags.RX_V44)

    
    def read_status(self) -> int | None:
        """Precisa ser implementada pelo driver"""
        if self.mb_server:
            # return self.mb_server._conv_reg_to_value(coils_regs.RX_MST, self.mb_server.db_shadow)
            mst = self.mb_server.data_bank.get_holding_registers(holding_regs.RX_MST.ADDRESS, holding_regs.RX_MST.SIZE)
            if mst:
                return ( mst[1] << 16) | mst[0]

        # return MotorStatusFlags.ENABLED  #TODO: Implementar a leitura do status do motor, e retornar os flags correspondentes




    
    def param_IP(self, value: str | None = None, converted:bool = False) -> str | None:
        """[DEPRECATED]
        IP value cannot be changed by the server anymore"""
        if value is None:
            if self.mb_server and self.mb_server.data_bank and isinstance(self.mb_server.data_bank, MB_DataBank) and self.mb_server.data_bank.client_info:
                    return self.mb_server.data_bank.client_info.address


    def _convert_pos(self, pos: int | float) -> float:
        """Converts position in microns to steps, since the CLP receives position values in steps."""
        value = pos / Config.enc_2_microns
        return value / Config.steps_2_encoder
        # return int(value / Config.steps_2_encoder)
    
    def param_backlash(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current backlash value from the configuration.
        When a value is provided, writes the new backlash value to the CLP
        Receives value in steps -> range 0 ~ 150 steps => 0 ~ 300 microns
        User defines this value in microns, so must convert to encoder and then to steps
        microns -> encoder -> steps"""
        if value is None:
            if converted == False:
                return str(Config.backlash)
            else: 
                return str(int(self._convert_pos(Config.backlash)))
            # value = Config.backlash
        
        value = value / Config.enc_2_microns
        value = int(value / Config.steps_2_encoder)

        if self.mb_server:  
            return self.mb_server.write_param(holding_regs.TX_V74, value)


        

    
    def param_max_pos(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current maximum position value from the configuration.
        When a value is provided, writes the new maximum position value to the CLP
        Receives value in steps
        User defines this value in microns, so must convert to encoder and then to steps
        microns -> encoder -> steps"""
        if value is None:
            if converted == False:
                return str(Config.max_pos)
            else:
                return str(int(self._convert_pos(Config.max_pos / Conversion.POSITION_VISUALIZATION)  ))

        # Conversion.POSITION_VISUALIZATION = (value - 14560) / 10661.7
        # Conversion.POSITION_COMMAND = 1 / Conversion.POSITION_VISUALIZATION

        print('-' * 50)
        print(f"VALUE: {value}")
        print(f"POSITION VISUALIZATION: {Conversion.POSITION_VISUALIZATION}")
        print(f"POSITION COMMAND: {Conversion.POSITION_COMMAND}")
        
        Config.max_pos = int(value)


        # value = (Config.max_pos * Conversion.POSITION_COMMAND) - value * Conversion.POSITION_COMMAND   # Conversão necessária devido a montagem mecânica
        # value = value / Conversion.POSITION_VISUALIZATION   # Conversao para enviar para o CLP
        value = value / Config.enc_2_microns
        value = int(value / Config.steps_2_encoder)

        print(f"VALUE MOTOR: {value}")

        print('-' * 50)

        # When the max position is changed the park position must also be changed due to
        # the update conversion value
        if self.mb_server:
            if self.mb_server.write_param(holding_regs.TX_V71, value) ==  "OK":
                return self.param_park_pos(value=Config.park_pos)           
            

    
    def param_park_pos(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current parking position value from the configuration.
        When a value is provided, writes the new parking position value to the CLP
        Receives value in steps
        User defines this value in microns, so must convert to encoder and then to steps
        microns -> encoder -> steps"""
        if value is None:
            if converted == False:
                return str(Config.park_pos)
            else:
                return str(int(self._convert_pos((Config.max_pos * Conversion.POSITION_COMMAND) - Config.park_pos * Conversion.POSITION_COMMAND) ) )


        print('_*' * 50)
        print(f"POSITION VISUALIZATION: {Conversion.POSITION_VISUALIZATION}")
        print(f"POSITION COMMAND: {Conversion.POSITION_COMMAND}")
        print(f'PARK POS: {value}')


        value = (Config.max_pos * Conversion.POSITION_COMMAND) - Conversion.POSITION_COMMAND * value   # Conversão necessária devido a montagem mecânica 
        
        value = value / Config.enc_2_microns
        value = int(value / Config.steps_2_encoder)

        value = value + Config.step_offset       # Adjust in steps

        print(f"SEND PARK MOTOR: {value}")
        print('_*' * 50)
        
        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V83, value)

    def _convert_speed(self, speed: int | float) -> int:
        return int(speed * Config.microns_2_rps * 240)
    
    def param_max_speed(self, value: int | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current maximum speed value from the configuration.
        When a value is provided, writes the new maximum speed value to the CLP
        CLP receives value rps/s * 240 
        User defines this value in microns/s
        microns/s -> rps/s -> * 240"""
        if value is None:
            if converted == False:
                return str(Config.max_speed)
            else:
                return str(self._convert_speed(Config.max_speed))

        value = int(value * Config.microns_2_rps * 240)

        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V75, value)

    
    def param_normal_speed(self, value: int | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current normal speed value from the configuration.
        When a value is provided, writes the new normal speed value to the CLP
        CLP receives value rps/s * 240 
        User defines this value in microns/s
        microns/s -> rps/s -> * 240"""
        if value is None:
            if converted == False:
                return str(Config.normal_speed)
            else:
                return str(self._convert_speed(Config.normal_speed))

        value = int(value * Config.microns_2_rps * 240)

        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V77, value)

    
    def param_low_speed(self, value: int | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current low speed value from the configuration.
        When a value is provided, writes the new low speed value to the CLP
        CLP receives value rps/s * 240 
        User defines this value in microns/s
        microns/s -> rps/s -> * 240"""
        if value is None:
            if converted == False:
                return str(Config.low_speed)
            else:
                return str(self._convert_speed(Config.low_speed))

        value = int(value * Config.microns_2_rps * 240)

        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V76, value)

    
    def param_max_step(self, value: int | None = None) -> str | None:
        """deprecated - use param_max_pos instead"""
        if value is None:
            return str(Config.max_pos)
        
        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V79, value)

    def _convert_acceleration(self, acc: int | float) -> int:
        return int(acc * Config.microns_2_rps * 6)

    def param_acceleration(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current acceleration value from the configuration.
        When a value is provided, writes the new acceleration value to the CLP
        CLP receives value in rps/s * 6
        User defines this value in microns/s²
        microns/s² -> rps/s -> *6
        1rps/s = 400 microns/s²"""
        if value is None:
            if converted == False:
                return str(Config.acceleration)
            else:
                return str(self._convert_acceleration(Config.acceleration))

        value = int( value * Config.microns_2_rps * 6 )     # Acceleration can be float but must be converted to int to send to CLP

        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V80, value)

    
    def param_deceleration(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current deceleration value from the configuration.
        When a value is provided, writes the new deceleration value to the CLP
        CLP receives value in rps/s * 6
        User defines this value in microns/s²
        microns/s² -> rps/s -> *6
        1rps/s = 400 microns/s²"""
        if value is None:
            if converted == False:
                return str(Config.deceleration)
            else:
                return str(self._convert_acceleration(Config.deceleration))

        value = int( value * Config.microns_2_rps * 6 )     # Deceleration can be float but must be converted to int to send to CLP

        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V79, value)

    def _convert_current(self, current: int | float) -> int:
        return int(current * 0.1)

    def param_idle_current(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current idle current value from the configuration.
        When a value is provided, writes the new idle current value to the CLP
        CLP receives value Amps * 100 
        User defines this value in mA
        mA -> A * 100 = (mA / 1000) * 100 = mA * 0.1 """
        if value is None:
            if converted == False:
                return str(Config.idle_current)
            else:
                return str(self._convert_current(Config.idle_current))

        value  = int(value * 0.1)     # Current can be float but must be converted to int to send to CLP
        
        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V78, value)

    
    def param_run_current(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current run current value from the configuration.
        When a value is provided, writes the new run current value to the CLP
        CLP receives value Amps * 100 
        User defines this value in mA
        mA -> A * 100 = (mA / 1000) * 100 = mA * 0.1 """
        if value is None:
            if converted == False:
                return str(Config.run_current)
            else:
                return str(self._convert_current(Config.run_current))

        value = int(value * 0.1)

        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V81, value)

    
    def param_acc_current(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """When no value is provided, returns the current acceleration current value from the configuration.
        When a value is provided, writes the new acceleration current value to the CLP
        CLP receives value Amps * 100 
        User defines this value in mA
        mA -> A * 100 = (mA / 1000) * 100 = mA * 0.1 """
        if value is None:
            if converted == False:
                return str(Config.acc_current)
            else:
                return str(self._convert_current(Config.acc_current))

        value = int(value * 0.1)         # Current can be float but must be converted to int to send to CLP
        
        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_V82, value)

    def param_tcp_rtmo(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
        if value is None:
            return str(Config.tcp_retransmission_timeout)

        value = int(value)
        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_TCPRTMO, value)

    def param_tcp_cycle(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
        if value is None:
            return str(Config.tcp_com_cycle_timeout)

        value = int(value)
        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_TCPCYCLE, value)

    def param_tcp_mbtmo(self, value: int | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
        if value is None:
            return str(Config.tcp_modbus_timeout)

        value = int(value)
        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_TCPMBTMO, value)

    def param_tcp_katmo(self, value: int | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
        if value is None:
            return str(Config.tcp_keep_alive_timeout)

        value = int(value)
        if self.mb_server:
            return self.mb_server.write_param(holding_regs.TX_TCPKATMO, value)
            
    def param_clp_auto_restart(self, value: bool | None = None, converted:bool = False) -> bool | str | None:
        """Precisa ser implementada pelo driver"""
        if value is None:
            return Config.clp_auto_restart
        
        if self.mb_server and self.mb_server.data_bank:
            reg_val = self.mb_server.data_bank.get_holding_registers(holding_regs.TX_PACKRST.ADDRESS, holding_regs.TX_PACKRST.SIZE)
            print(f"PARAM CLP AUTO RESTART GET PACKRST: {reg_val}")
            if reg_val and value:
                val = reg_val[0] | PackRSTFlags.CLP 
            elif reg_val and not value:
                val = reg_val[0] & (~PackRSTFlags.CLP)
            print(f"PARAM CLP AUTO RESTART WRITE PACKRST: {val}")
            return self.mb_server.write_param(holding_regs.TX_PACKRST, val)

    def param_motor_auto_restart(self, value: bool | None = None, converted:bool = False) -> bool | str | None:
        """Precisa ser implementada pelo driver"""
        if value is None:
            return Config.motor_auto_restart
    
        if self.mb_server and self.mb_server.data_bank:
            reg_val = self.mb_server.data_bank.get_holding_registers(holding_regs.TX_PACKRST.ADDRESS, holding_regs.TX_PACKRST.SIZE)
            print(f"PARAM MOTOR AUTO RESTART GET PACKRST: {reg_val}")
            if reg_val and value:
                val = reg_val[0] | PackRSTFlags.MOTOR 
            elif reg_val and not value:
                val = reg_val[0] &  (~PackRSTFlags.MOTOR)
            else:
                return None
            print(f"PARAM MOTOR AUTO RESTART WRITE PACKRST: {val}")
            return self.mb_server.write_param(holding_regs.TX_PACKRST, val)

    def read_firmware_version(self) -> str | None:
        """Precisa ser implementada pelo driver"""
        if self.mb_server:
            val = self.mb_server.data_bank.get_holding_registers(holding_regs.RX_V90.ADDRESS, holding_regs.RX_V90.SIZE)
            if val:
                return str(val[0])

    
    def read_alarm_status(self) -> bool | None:
        """Precisa ser implementada pelo driver"""
        if self.mb_server:
            val = self.mb_server.data_bank.get_holding_registers(holding_regs.RX_PACKSTATUS.ADDRESS, holding_regs.RX_PACKSTATUS.SIZE)
            if val:
                return bool(val[0] & PackStatusFlags.RX_ALM)

    
    def parse_alarm_info(self) -> str | None:
        """Precisa ser implementada pelo driver"""
        if self.mb_server:
            # motor_alarm_int = self.mb_server._conv_reg_to_value(coils_regs.RX_ALC, self.mb_server.db_shadow) & motor_alc_errors_mask
            motor_alarm_int = self.mb_server.data_bank.get_holding_registers(holding_regs.RX_ALC.ADDRESS, holding_regs.RX_ALC.SIZE)
            if motor_alarm_int:
                motor_alarm_int = motor_alarm_int[0] & motor_alc_errors_mask
            
                self.read_firmware_status()  # Update the SASTAT value
                sastat_alarm_int = self.motor.SASTAT & motor_program_errors_mask

                alarm_info = ''
                if motor_alarm_int > 0:
                    alarm_info = "Alarm details ALC bits: "
                    alarm_info += self._extract_flags_info(motor_alarm_int, MotorAlarmInfo)
                if sastat_alarm_int > 0:
                    if alarm_info != '':
                        alarm_info += ' | '
                    alarm_info += "Alarm details SASTAT bits: "
                    alarm_info += self._extract_flags_info(sastat_alarm_int, MotorProgramStatus)

                return alarm_info

    def _extract_flags_info(self, input:int, flags_type: type[MotorAlarmInfo] | type[MotorProgramStatus], separator: str = "&") -> str:
        """Extracts the name of the flags that are activated in a given object, the object
        must be an IntFlag

        :param input: Int value that represents the flags
        :type input: int
        :param flags_type: Type of the object
        :type flags_type: IntFlag
        :param separator: Value used to separate the flags in the message, defaults to "&"
        :type separator: str, optional
        :return: String with the parsed message according to the 
        :rtype: str
        """
        msg = ''
        # if input > 0:
        while input > 0:
            for error in flags_type:
                if input & error:
                    input = input - error
                    if input > 0:
                        msg += f"{error.name} {separator} "
                    else:
                        msg += f"{error.name}"

        return msg

    def read_firmware_status(self) -> str | None:
        """Precisa ser implementada pelo driver"""

        flag_status = False
        msg = ''
        if self.mb_server:
            # self.motor.SASTAT = self.mb_server._conv_reg_to_value(coils_regs.RX_SASTAT, self.mb_server.db_shadow)
            temp = self.mb_server.data_bank.get_holding_registers(holding_regs.RX_SASTAT.ADDRESS, holding_regs.RX_SASTAT.SIZE)
            if temp:
                self.motor.SASTAT = (temp[1] << 16) | temp[0]

            # Uses an internal variable that can be changed without affecting the real sastat value
            sastat = self.motor.SASTAT     
            
            self.focus_out_status = ( sastat & MotorProgramStatus.RUN_FOCUS_OUT ) != 0

            self.focus_in_status = (sastat & MotorProgramStatus.RUN_FOCUS_IN) != 0

            self.park_status = (sastat & MotorProgramStatus.RUN_PARK) != 0
            
            if sastat & MotorProgramStatus.NO_INIT:
                sastat -= MotorProgramStatus.NO_INIT
                msg += "Motor firmware not initialized"
                if sastat > 0:
                    msg += ' / '

            if sastat & MotorProgramStatus.READY:
                sastat -= MotorProgramStatus.READY
                msg += "Idle"
                if sastat > 0:
                    msg += ' / '

            if sastat & (MotorProgramStatus.RUN_HOMING | MotorProgramStatus.RUN_FOCUS_IN | MotorProgramStatus.RUN_FOCUS_OUT | MotorProgramStatus.RUN_GOTO | MotorProgramStatus.RUN_PARK):
                if sastat & MotorProgramStatus.RUN_HOMING:
                    sastat -= MotorProgramStatus.RUN_HOMING
                if sastat & MotorProgramStatus.RUN_FOCUS_IN:
                    sastat -= MotorProgramStatus.RUN_FOCUS_IN
                if sastat & MotorProgramStatus.RUN_FOCUS_OUT:
                    sastat -= MotorProgramStatus.RUN_FOCUS_OUT
                if sastat & MotorProgramStatus.RUN_GOTO:
                    sastat -= MotorProgramStatus.RUN_GOTO
                if sastat & MotorProgramStatus.RUN_PARK:
                    sastat -= MotorProgramStatus.RUN_PARK
                
                msg += "Running"
                if sastat > 0:
                    msg += ' / '

            if (sastat > 0) and (sastat & MotorProgramStatus.ERROR_NEED_HOME):
                sastat -= MotorProgramStatus.ERROR_NEED_HOME
                msg += "Must run HOME"
                if sastat > 0:
                    msg += ' / '

            if (sastat > 0) and (sastat & MotorProgramStatus.ERROR_FOCUS_OUT):
                sastat -= MotorProgramStatus.ERROR_FOCUS_OUT
                msg += "Too close to HOME"
                if sastat > 0:
                    msg += ' / '

            if (sastat > 0) and (sastat & MotorProgramStatus.MANUAL_MOVE):
                sastat -= MotorProgramStatus.MANUAL_MOVE
                self.driver_comm.manual_movement.status.emit(True)
                msg += "Manual Move"
                if sastat > 0:
                    msg += ' / '
            else:
                self.driver_comm.manual_movement.status.emit(False)
                    
            if (sastat > 0) and (sastat & MotorProgramStatus.ERROR_RS485):
                sastat -= MotorProgramStatus.ERROR_RS485
                msg += "RS485 error"
                if sastat > 0:
                    msg += ' / '
                    
            if (sastat > 0) and (sastat & MotorProgramStatus.ERROR_PADDLE):
                sastat -= MotorProgramStatus.ERROR_PADDLE
                msg += "Paddle error"
                if sastat > 0:
                    msg += ' / '
                    
            if (sastat > 0) and (sastat & MotorProgramStatus.ERROR_MOTOR_OFF_ID):
                sastat -= MotorProgramStatus.ERROR_MOTOR_OFF_ID
                msg += "Motor off or ID error"
                if sastat > 0:
                    msg += ' / '
                    
            if (sastat > 0) and (sastat & MotorProgramStatus.ERROR_LIM_SWITCH):
                sastat -= MotorProgramStatus.ERROR_LIM_SWITCH
                msg += "Lim-switch error"
                if sastat > 0:
                    msg += ' / '

            if (sastat > 0) and (sastat & MotorProgramStatus.ERROR_OUT_OF_RANGE):
                sastat -= MotorProgramStatus.ERROR_OUT_OF_RANGE
                msg += "Out of range"
                if sastat > 0:
                    msg += ' / '

            # if not flag_status:
            #     msg = "Running"

            # return "Idle" #TESTE
            return msg

            
    
    def sendCommand(self, command: str) -> str:
        """Precisa ser implementada pelo driver"""
        #  In the AMP motor the send command method is implemented by  the modbus server
        ...
    
    def move_to(self, pos_str: str) -> str | None:
        """Precisa ser implementada pelo driver"""
        if self.mb_server:
        # return self.mb_server.send_command(dig_inputs_regs.TX_GS29)
            pos = float(pos_str) 
            if pos < 0:
                pos = 0
            elif pos > Config.max_pos:
                pos = Config.max_pos
            # Sends the position value to the CLP, and then sends the command to start the movement towards the target position
            # command_position = (Config.max_pos * Conversion.POSITION_COMMAND) - Conversion.POSITION_COMMAND * int(pos)   # Conversão necessária devido a montagem mecânica  
            command_position = (Config.max_pos * Conversion.POSITION_COMMAND) - Conversion.POSITION_COMMAND * pos   # Conversão necessária devido a montagem mecânica 
            # command_position = (Config.max_pos * Conversion.POSITION_VISUALIZATION) - Conversion.POSITION_VISUALIZATION * pos   # Conversão necessária devido a montagem mecânica 

            print(f"Moving to position {pos} microns - Command position value: {command_position}")
            print(f"steps: {self._convert_pos(command_position)}  ---  int steps: {round(self._convert_pos(command_position))}")

            print(f'Steps to microns: {   -((round(self._convert_pos(command_position)) * Config.steps_2_encoder * Config.enc_2_microns) - (Config.max_pos * Conversion.POSITION_COMMAND)) / Conversion.POSITION_COMMAND}')

            if self.mb_server.write_param(holding_regs.TX_V20, round(self._convert_pos(command_position) + Config.step_offset)) == "OK":
                time.sleep(TimeDelays.WAIT_PARAM)   # Delay to ensure the position value is written to the CLP before sending the command to start the movement
                return self.mb_server.send_command(PackCMDFlags.TX_GS29)
            else:
                return "NOK"

    def focus_in(self, speed: str | int = Config.normal_speed) -> str | None:
        """Precisa ser implementada pelo driver""" 
        if self.mb_server:
            speed_int = int(speed)
            if speed_int != Config.normal_speed:
                if speed_int <= 2:
                    speed_int = 2

                command_speed = self._convert_speed(speed_int)
            else:
                command_speed = self._convert_speed(Config.normal_speed)

            if self.mb_server.write_param(holding_regs.TX_V77, command_speed) == "OK":
                time.sleep(TimeDelays.WAIT_PARAM)
                return self.mb_server.send_command(PackCMDFlags.TX_GS21)
            else:
                return "NOK"
    
    def focus_out(self, speed: str | int = Config.normal_speed) -> str | None:
        """Precisa ser implementada pelo driver""" 
        if self.mb_server:
            speed_int = int(speed)
            if speed_int != Config.normal_speed:
                if speed_int <= 2:
                    speed_int = 2

                command_speed = self._convert_speed(speed_int)

            else:
                command_speed = self._convert_speed(Config.normal_speed)

            if self.mb_server.write_param(holding_regs.TX_V77, command_speed) == "OK":
                time.sleep(TimeDelays.WAIT_PARAM)
                return self.mb_server.send_command(PackCMDFlags.TX_GS20)
            else:
                return "NOK"
    
    def halt(self) -> str | None:
        """Precisa ser implementada pelo driver""" 
        if self.mb_server:
            return self.mb_server.send_command(PackCMDFlags.TX_V42)


    def home(self) -> str | None:
        """Precisa ser implementada pelo driver"""
        if self.mb_server:
            return self.mb_server.send_command(PackCMDFlags.TX_GS30)
    
    def park(self) -> str | None:
        """Precisa ser implementada pelo driver""" 
        if self.mb_server:
            return self.mb_server.send_command(PackCMDFlags.TX_GS5)
        
    def _reset_communication(self):
        """Resets and tries to re-establish the modbus connection with the CLP.
        Reset process:
            - Signals server that the connection to the motor was lost;
            - Resets modbus server"""
        super()._reset_communication()
        

        self.driver_comm.timeout.emit(True)

        self.motor.connected = False

        if self.mb_server:
            self.mb_server.timeout.running = False  # Stops timeout counter
            self.mb_server.timeout.reset()
            self.mb_server.handshake = False

        
    def _update_all_parameters(self):
        # params = tuple()
        # values = tuple()

        # if self.mb_server:
        #     for param_idx in MotorParamsIdx:
        #             # if param_idx != MotorParamsIdx.MOTOR_IP and param_idx != MotorParamsIdx.MAX_STEP:
        #             params += (self.motor.parameters[param_idx].REGISTER,)
                    
        #             values += (int(self.param_methods[param_idx](converted=True)), )   # Mounts tuple with parameters values 

        #             print(f'{self.motor.parameters[param_idx].REGISTER} - {int(self.param_methods[param_idx](converted=True))}')
                        
        #     self.mb_server.write_param(params, values)
        resp: str = ""
        p = 0
        if self.mb_server:
            for param_idx in MotorParamsIdx:
                p += 1
                self.motor.signals.progress.string.emit(int(p/len(MotorParamsIdx)*100))
                # time.sleep(0.05)            # Just for better visualization of ui update
                resp = self.param_methods[param_idx]()
                try:
                    val = float(resp)
                    print(f'{self.motor.parameters[param_idx]} - {int(self.param_methods[param_idx](converted=True))}')
                except:
                    val = resp
                print(f'{param_idx}, {val}')
                self.param_methods[param_idx](value=val)
                

                    