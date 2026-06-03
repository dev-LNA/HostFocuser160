from abc import abstractmethod

from src.interface.motor_driver import Driver
from src.utils.constants import MotorProgramStatus

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.interface.modbus_server import IAGModbusServer #, TimeoutCheck
# from pyModbusTCP.server import DataBank
from src.interface.modbus_data_bank import MB_DataBank

from logging import Logger
from threading import Lock, Thread, Timer

from src.core.config import Config
from src.core.exceptions import DriverException
from src.utils.constants import constants, MotorStatusFlags, MotorParamsIdx, MotorAlarmInfo, motor_program_errors_mask, POSITION_COMMAND_CONVERSION, POSITION_VISUALIZATION_CONVERTION
from src.utils.modbus_regs import RegsInfo, RegType, coils_regs, dig_inputs_regs, DB_size, CLP_Owned, TwosComplementReg, param_vars

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.utils.motor import Motor


import time



class DriverAMP(Driver):
    def __init__(self, motor: Motor):
        super().__init__(motor)

        self.mb_server: IAGModbusServer = None

        # self._task_progress: int = 0

    # @property
    # def mb_server_task_progress(self):
    #     return self._task_progress
    # @mb_server_task_progress.setter
    # def mb_server_task_progress(self, value: int):
    #     self._task_progress = value
    #     self.motor.signals.progress.string.emit(self._task_progress)



    def connect_motor(self, max_retries: int = 5, delay: float = 0.1) -> str:
        """Precisa ser implementada pelo driver"""
        retries = 0
        _con = False

        # dataBank_config = MB_DataBank(coils_size=DB_size.COIL_LAST_ADDRESS+1, coils_default_value=False,        #|      
        #         d_inputs_size=DB_size.DI_LAST_ADDRESS+1, d_inputs_default_value=False,               #|  Config value for the modbus data bank.
        #         h_regs_size=0, h_regs_default_value=0,                          #|  
        #         i_regs_size=0, i_regs_default_value=0)                          #|
                
        while retries < max_retries and not _con:
            try:
                # host => Server IP Address
                # self.mb_server = IAGModbusServer(host=Config.device_ip, port=Config.device_port,no_block=True, data_bank=dataBank_config)
                # self.mb_server.start()
                # # self.mb_server.signals.signal_stop.connect(self.disconnect_motor)
                # self.mb_run_thread = Thread(target=self.mb_server.run)
                # self.mb_run_thread.start()

                self.mb_server.timeout.reset()
                self.mb_server.timeout.running = True   # Starts timeout counter

                self.mb_server.running = True
                _con = True
                self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])  #| TX_WAIT e TX_BUSY must be
                self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [False])   #| initialized as False

                # self.mb_server.timeout.signal_timeout.connect(self.driver_comm.received_timeout)    # Connects timeout signal to the motor driver
                


                print("Modbus server started")
                return "OK"
            except Exception as e:
                print(f"Error starting modbus server: {e}")

    def disconnect_motor(self) -> str:
        """Closes the modbus server connection"""
        try:
            if self.mb_server:
                print("Closing modbus server...")
                self.mb_server._start_writting_data()
                self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_SVON.ADDRESS, [False])   # Informs the CLP that the Driver is not active anymore
                self.mb_server._stop_writting_data()
                time.sleep(0.2)  # Delay to ensure the CLP reads the change in the SVON register before the server is closed
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
                dataBank_config = MB_DataBank(coils_size=DB_size.COIL_LAST_ADDRESS+1, coils_default_value=False,        #|      
                                d_inputs_size=DB_size.DI_LAST_ADDRESS+1, d_inputs_default_value=False,               #|  Config value for the modbus data bank.
                                h_regs_size=0, h_regs_default_value=0,                          #|  
                                i_regs_size=0, i_regs_default_value=0)                          #|
                self.mb_server = IAGModbusServer(host=Config.device_ip, port=Config.device_port ,no_block=True, data_bank=dataBank_config,
                                                 timeout_callback_function=self._reset_communication)

                self.mb_server.mb_comm.task_progress.connect(lambda value: self.motor.signals.progress.string.emit(value))

                self.mb_server.start()

                self.mb_run_thread = Thread(target=self.mb_server.run)
                self.mb_run_thread.start()

                while self.mb_server.handshake is False and retries < max_retries:
                    time.sleep(0.2)             # Delay between retries #TODO: colocar isso no arquivo de configuração config_IAG.toml
                    retries += 1

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
            
        else:
            try:
                while self.mb_server.handshake is False and retries < max_retries:
                    time.sleep(0.2)             # Delay between retries #TODO: colocar isso no arquivo de configuração config_IAG.toml
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

    
    def conv_position_show(self, encoder_pos: int = None, type: str = "int") -> int | float:
        """Reads motor encoder position and converts to microns
        Used for PUB and display values

        :raises ValueError: If the reading is not valid
        :return: _description_
        :rtype: int | Exception
        """
        if encoder_pos is None:
            encoder_pos = self.read_encoder()
        # pos = int(round(encoder_pos / Config.enc_2_microns))
        if type == "int":
            # Conversão necessário devido a montagem mecânica
            pos = 2510 - int(round(encoder_pos * Config.enc_2_microns * POSITION_VISUALIZATION_CONVERTION))
            # pos = int(round(encoder_pos * Config.enc_2_microns))
        else:
            # Conversão necessário devido a montagem mecânica
            pos = 2510 - round(encoder_pos * Config.enc_2_microns * POSITION_VISUALIZATION_CONVERTION, 1)
            # pos = round(encoder_pos * Config.enc_2_microns, 1)
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

        # pos_conv = int(round((Config.enc_2_microns * position)))
        pos_conv = int(round((Config.enc_2_microns / position)))




    
    def read_encoder(self) -> int:
        """Reads encoder value from the motor and 
        returns it as an integer"""
        response = self.mb_server._conv_reg_to_value(coils_regs.RX_EX, self.mb_server.db_shadow)
        return response
    

    def read_homing(self) -> bool:
        """Precisa ser implementada pelo driver"""
        return self.mb_server.db_shadow.get_coils(coils_regs.RX_V15.ADDRESS, coils_regs.RX_V15.SIZE)[0]

       # return False

    
    def read_parking(self) -> bool:
        """Precisa ser implementada pelo driver"""
        return False

    
    def read_initialized(self) -> bool:
        """Precisa ser implementada pelo driver"""
        return self.mb_server.db_shadow.get_coils(coils_regs.RX_V44.ADDRESS, 1)[0]

    
    def read_status(self) -> int:
        """Precisa ser implementada pelo driver"""

        return self.mb_server._conv_reg_to_value(coils_regs.RX_MST, self.mb_server.db_shadow)


        # return MotorStatusFlags.ENABLED  #TODO: Implementar a leitura do status do motor, e retornar os flags correspondentes




    
    def param_IP(self, value: int | str | bool = None) -> str:
        """When no value is provided, returns the current IP value from the configuration.
        When a value is provided, writes the new IP value to the CLP"""
        if value is None:
            return Config.device_ip
        
        ip_a = value.split(".")[0]
        ip_b = value.split(".")[1]
        ip_c = value.split(".")[2]
        ip_d = value.split(".")[3]

        ip_param_regs = (dig_inputs_regs.TX_IP_A, dig_inputs_regs.TX_IP_B, dig_inputs_regs.TX_IP_C, dig_inputs_regs.TX_IP_D)
        ip_values = (ip_a, ip_b, ip_c, ip_d)
        return self.mb_server.write_param(ip_param_regs, ip_values)

        # return self.mb_server.write_param(dig_inputs_regs.TX_V70, value)

    def _convert_pos(self, pos: int | float) -> int:
        """Converts position in microns to steps, since the CLP receives position values in steps."""
        value = pos / Config.enc_2_microns
        return int(value / Config.steps_2_encoder)
    
    def param_backlash(self, value: int | str | bool = None, converted:bool = False) -> str:
        """When no value is provided, returns the current backlash value from the configuration.
        When a value is provided, writes the new backlash value to the CLP
        Receives value in steps -> range 0 ~ 150 steps => 0 ~ 300 microns
        User defines this value in microns, so must convert to encoder and then to steps
        microns -> encoder -> steps"""
        if value is None:
            if converted == False:
                return str(Config.backlash)
            else: 
                return str(self._convert_pos(Config.backlash))
            # value = Config.backlash

        value = value / Config.enc_2_microns
        value = int(value / Config.steps_2_encoder)

        return self.mb_server.write_param(dig_inputs_regs.TX_V74, value)


        

    
    def param_max_pos(self, value: int | str | bool = None, converted:bool = False) -> str:
        """When no value is provided, returns the current maximum position value from the configuration.
        When a value is provided, writes the new maximum position value to the CLP
        Receives value in steps
        User defines this value in microns, so must convert to encoder and then to steps
        microns -> encoder -> steps"""
        if value is None:
            if converted == False:
                return str(Config.max_pos)
            else:
                return str(self._convert_pos(Config.max_pos / POSITION_VISUALIZATION_CONVERTION)  )


        # value = 25389.8 - value * POSITION_COMMAND_CONVERSION   # Conversão necessária devido a montagem mecânica
        value = value / POSITION_VISUALIZATION_CONVERTION   # Conversao para enviar para o CLP
        value = value / Config.enc_2_microns
        value = int(value / Config.steps_2_encoder)

        return self.mb_server.write_param(dig_inputs_regs.TX_V71, value)
            

    
    def param_park_pos(self, value: int | str | bool = None, converted:bool = False) -> str:
        """When no value is provided, returns the current parking position value from the configuration.
        When a value is provided, writes the new parking position value to the CLP
        Receives value in steps
        User defines this value in microns, so must convert to encoder and then to steps
        microns -> encoder -> steps"""
        if value is None:
            if converted == False:
                return str(Config.park_pos)
            else:
                return str(self._convert_pos(25389.8 - Config.park_pos * POSITION_COMMAND_CONVERSION)  )

        value = 25389.8 - POSITION_COMMAND_CONVERSION * value   # Conversão necessária devido a montagem mecânica 
        
        value = value / Config.enc_2_microns
        value = int(value / Config.steps_2_encoder)

        
        return self.mb_server.write_param(dig_inputs_regs.TX_V83, value)

    def _convert_speed(self, speed: int | float) -> int:
        return int(speed * Config.microns_2_rps * 240)
    
    def param_max_speed(self, value: int | str | bool = None, converted:bool = False) -> str:
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

        return self.mb_server.write_param(dig_inputs_regs.TX_V75, value)

    
    def param_normal_speed(self, value: int | str | bool = None, converted:bool = False) -> str:
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

        return self.mb_server.write_param(dig_inputs_regs.TX_V77, value)

    
    def param_low_speed(self, value: int | str | bool = None, converted:bool = False) -> str:
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

        return self.mb_server.write_param(dig_inputs_regs.TX_V76, value)

    
    def param_max_step(self, value: int | str | bool = None) -> str:
        """deprecated - use param_max_pos instead"""
        if value is None:
            return str(Config.max_step)

        return self.mb_server.write_param(dig_inputs_regs.TX_V79, value)

    def _convert_acceleration(self, acc: int | float) -> int:
        return int(acc * Config.microns_2_rps * 6)

    def param_acceleration(self, value: int | str | bool = None, converted:bool = False) -> str:
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

        value = int( value * Config.microns_2_rps * 6 )
        return self.mb_server.write_param(dig_inputs_regs.TX_V80, value)

    
    def param_deceleration(self, value: int | str | bool = None, converted:bool = False) -> str:
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

        value = int( value * Config.microns_2_rps * 6 )
        return self.mb_server.write_param(dig_inputs_regs.TX_V79, value)

    def _convert_current(self, current: int | float) -> int:
        return int(current * 0.1)

    def param_idle_current(self, value: int | str | bool = None, converted:bool = False) -> str:
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

        value  = int(value * 0.1)
        return self.mb_server.write_param(dig_inputs_regs.TX_V78, value)

    
    def param_run_current(self, value: int | str | bool = None, converted:bool = False) -> str:
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
        return self.mb_server.write_param(dig_inputs_regs.TX_V81, value)

    
    def param_acc_current(self, value: int | str | bool = None, converted:bool = False) -> str:
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

        value = int(value * 0.1)
        return self.mb_server.write_param(dig_inputs_regs.TX_V82, value)

    
    def read_firmware_version(self) -> str:
        """Precisa ser implementada pelo driver"""
        return str(self.mb_server._conv_reg_to_value(coils_regs.RX_V90, self.mb_server.db_shadow))

    
    def read_alarm_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        return self.mb_server.db_shadow.get_coils(coils_regs.RX_ALM.ADDRESS, coils_regs.RX_ALM.SIZE)[0]     

    
    def parse_alarm_info(self) -> str:
        """Precisa ser implementada pelo driver"""
        motor_alarm_int = self.mb_server._conv_reg_to_value(coils_regs.RX_ALC, self.mb_server.db_shadow)
        motor_alarm = MotorAlarmInfo(motor_alarm_int)
        self.read_firmware_status()  # Update the SASTAT value
        sastat_alarm_int = self.motor.SASTAT & motor_program_errors_mask
        sastat_alarm = MotorProgramStatus(sastat_alarm_int)

        print(f"Motor alarm int: {motor_alarm_int} - Motor alarm: {motor_alarm}")
        print(f"SASTAT alarm int: {sastat_alarm_int} - SASTAT alarm: {sastat_alarm}")
        print(f"Motor alarm bits: {self.motor.SASTAT & motor_program_errors_mask:016b}")
        print(f"mascara de erros: {bin(motor_program_errors_mask)}")

        alarm_info = "Alarm details: "
        for error in motor_alarm:
            alarm_info += error.name + " / "

        for error in sastat_alarm:
            alarm_info += error.name + " / "
        
        alarm_info = alarm_info.removesuffix(" / ")

        return alarm_info



    
    def read_firmware_status(self) -> str:
        """Precisa ser implementada pelo driver"""

        self.motor.SASTAT = self.mb_server._conv_reg_to_value(coils_regs.RX_SASTAT, self.mb_server.db_shadow)
        # print(f"SASTAT = {sastat}")
        

        if self.motor.SASTAT & MotorProgramStatus.RUN_FOCUS_OUT:
            self.driver_comm.run_focus_out.emit(True, "statusLed", "WAIT")
        else:
            self.driver_comm.run_focus_out.emit(False, "statusLed", "OFF")

        if self.motor.SASTAT & MotorProgramStatus.RUN_FOCUS_IN:
            self.driver_comm.run_focus_in.emit(True, "statusLed", "WAIT")
        else:
            self.driver_comm.run_focus_in.emit(False, "statusLed", "OFF")

        if self.motor.SASTAT & MotorProgramStatus.RUN_PARK:
            self.driver_comm.run_park.emit(True, "statusLed", "WAIT")
        else:
            self.driver_comm.run_park.emit(False, "statusLed", "OFF")

        if self.motor.SASTAT & MotorProgramStatus.READY:
            return "Idle"

        if self.motor.SASTAT & MotorProgramStatus.ERROR_NEED_HOME:
            return "Must run HOME"

        if self.motor.SASTAT & MotorProgramStatus.ERROR_FOCUS_OUT:
            return "Too close to HOME"

        if self.motor.SASTAT & MotorProgramStatus.MANUAL_MOVE:
            return "Manual Movement"
        
        if self.motor.SASTAT & MotorProgramStatus.ERROR_RS485:
            return "RS485 error"
        
        if self.motor.SASTAT & MotorProgramStatus.ERROR_OUT_OF_RANGE:
            return "Out of range"
        
        return "Running"



        # sastat  = self.mb_server.db_shadow.get_coils(coils_regs.RX_SASTAT.ADDRESS, coils_regs.RX_SASTAT.SIZE)
        # sastat_bits = "".join(reversed([str(int(b)) for b in sastat]))
        # sastat_bits_bin = int(sastat_bits, 2)

        # mst  = self.mb_server.db_shadow.get_coils(coils_regs.RX_MST.ADDRESS, coils_regs.RX_MST.SIZE)
        # mst_bits = "".join(reversed([str(int(b)) for b in mst]))
        # mst_bits_bin = int(mst_bits, 2)



     #   print(f"SASTAT = {sastat}")
        # print(f"MST = {mst_bits}")

        # if  not (sastat_bits_bin & MotorProgramStatus.READY) and not (mst_bits_bin & 16384):
        #     return "Idle"
        # else:
        #     return "Running"
        # if not (mst_bits_bin & 16384):
        #     return "Idle"
        # else:
        #     return "Running"

        # if not (sastat_bits_bin & MotorProgramStatus.READY):
        #     return "Idle"
        # else:
        #     return "Running"


        # if val_bits_bin & MotorProgramStatus.READY:
        #     ...
        # if val_bits_bin & MotorProgramStatus.RUN_HOMING:
        #     print('Motor running Home')
        # if val_bits_bin & MotorProgramStatus.ON_FAULT:
        #     print('Motor on fault')
        # if val_bits_bin & MotorProgramStatus.CHECK_RANGES:
        #     print('checking ranges')
        # if val_bits_bin & MotorProgramStatus.RUN_PARK:
        #     print('Motor running Park')
        # if val_bits_bin & MotorProgramStatus.RUN_FOCUS_OUT:
        #     print('Motor running FOCUS OUT')
        # if val_bits_bin & MotorProgramStatus.RUN_FOCUS_IN:
        #     print('Motor running FOCUS IN')
        # if val_bits_bin & MotorProgramStatus.RUN_GOTO:
        #     print('Motor running GO TO')
        # if val_bits_bin & MotorProgramStatus.MANUAL_MOVE:
        #     print('Motor running MANUAL MOVE')
        # if val_bits_bin & MotorProgramStatus.ERROR_NEED_HOME:
        #     print('ERROR - Need to do HOMING first')
        # if val_bits_bin & MotorProgramStatus.ERROR_NEED_HOME:
        #     print('ERROR - Focus In error - too close to LIM-')
        # if val_bits_bin & MotorProgramStatus.ERROR_OUT_OF_RANGE:
        #     print('ERROR - Velocity or position out of range')
        # if val_bits_bin & MotorProgramStatus.ERROR_RS485:
        #     print('ERROR -  RS485 error or Motor OFF')
        # if val_bits_bin & MotorProgramStatus.ERROR_PADDLE:
        #     print('ERROR - Paddle Short circuit')
        # if val_bits_bin & MotorProgramStatus.ERROR_LIM_SWITCH:
        #     print('ERROR - LIM switch error')
        # if val_bits_bin & MotorProgramStatus.VALID_STATUS:
        #     print('Motor ON & ID OK')
        # else:
        #     print('Motor OFF or ID error')

            
    
    def sendCommand(self, command: str) -> str:
        """Precisa ser implementada pelo driver"""
        ...
    
    def move_to(self, pos: str) -> str:
        """Precisa ser implementada pelo driver"""

        # return self.mb_server.send_command(dig_inputs_regs.TX_GS29)

        if pos < 0:
            pos = 0
        elif pos > Config.max_pos:
            pos = Config.max_pos
        # Sends the position value to the CLP, and then sends the command to start the movement towards the target position
        command_position = 25389.8 - POSITION_COMMAND_CONVERSION * 10*int(pos)   # Conversão necessária devido a montagem mecânica  

        print(f"Moving to position {pos} microns - Command position value: {command_position}")

        if self.mb_server.write_param(dig_inputs_regs.TX_V20, int(self._convert_pos(command_position))) == "OK":
            time.sleep(1)   # Delay to ensure the position value is written to the CLP before sending the command to start the movement
            return self.mb_server.send_command(dig_inputs_regs.TX_GS29)
        else:
            return "NOK"

    def focus_in(self, speed: str = None) -> str:
        """Precisa ser implementada pelo driver""" 
        return self.mb_server.send_command(dig_inputs_regs.TX_GS21)
    
    def focus_out(self, speed: str = None) -> str:
        """Precisa ser implementada pelo driver""" 
        return self.mb_server.send_command(dig_inputs_regs.TX_GS20)
    
    def halt(self) -> str:
        """Precisa ser implementada pelo driver""" 
        return self.mb_server.send_command(dig_inputs_regs.TX_V42)


    def home(self) -> str:
        """Precisa ser implementada pelo driver"""
        return self.mb_server.send_command(dig_inputs_regs.TX_GS30)
    
    def park(self) -> str:
        """Precisa ser implementada pelo driver""" 
        return self.mb_server.send_command(dig_inputs_regs.TX_GS5)
        
    def _reset_communication(self):
        """Resets and tries to re-establish the modbus connection with the CLP.
        Reset process:
            - Signals server that the connection to the motor was lost;
            - Resets modbus server"""
        super()._reset_communication()

        self.driver_comm.timeout.emit(True)

        self.motor.connected = False

        self.mb_server.timeout.running = False  # Stops timeout counter
        self.mb_server.timeout.reset()
        self.mb_server.handshake = False

        
    def _update_all_parameters(self):
        params = tuple()
        values = tuple()

        # self.motor.signals.progress.value.emit(True)
        # self.motor.signals.progress.string.emit(0)

        for param_idx in MotorParamsIdx:
                if param_idx != MotorParamsIdx.MOTOR_IP and param_idx != MotorParamsIdx.MAX_STEP:
                    params += (self.motor.parameters[param_idx].REGISTER,)
                    # values += (int(float(self.motor.parameters[param_idx].VALUE)),)
                    values += (int(self.param_methods[param_idx](converted=True)),)
                    # p += 1
                    # self.motor.signals.progress.string.emit(int((p/(len(MotorParamsIdx) - 2))*100)) # Exclude IP and MAX_STEP, which are not written in the same way as the others

                    print(f'{self.motor.parameters[param_idx].REGISTER} - {int(self.param_methods[param_idx](converted=True))}')
                    
        self.mb_server.write_param(params, values)

        # self.motor.signals.progress.value.emit(False)
        # self.motor.signals.progress.string.emit(0)

                    