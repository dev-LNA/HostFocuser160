from src.interface.motor_driver import Driver
from src.core.config import Config

from threading import Lock
import time
import socket

from contextlib import closing
from src.utils.constants import constants, MotorStatusFlags, MotorAlarmInfo, MotorParamsIdx, TimeDelays

import logging

class DriverDMX(Driver):

    def __init__(self, model):  #TODO: Criar classe (IntNum) com os modelos possíveis de motores
        super().__init__(model)
        self.socket = None
        self._lock = Lock()

        self.time_count = time.time()
        self.com_total_time: float = 0.0
        self.sent_commands: int = 0
        self.com_speed: float = 0.0
        self.bits_trasmitted: int = 0

        self.timeout_counter: int = 0

    @property
    def focus_out_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...
    @focus_out_status.setter
    def focus_out_status(self, val:bool):
        """Precisa ser implementada pelo driver"""
        ...

    @property
    def focus_in_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...
    @focus_in_status.setter
    def focus_in_status(self, val:bool):
        """Precisa ser implementada pelo driver"""
        ...

    @property
    def park_status(self) -> bool:
        """Precisa ser implementada pelo driver"""
        ...
    @park_status.setter
    def park_status(self, val:bool):
        """Precisa ser implementada pelo driver"""
    
    def connect_motor(self, max_retries = 5, delay = 0.1) -> str:
        """Connects the device and open socket connection

        Args:
            max_retries (int, optional): Number os tries if first one fail. Defaults to 5.
            delay (float, optional): Small delay, in seconds, to wait after a try. Defaults to 0.1.

        Returns:
            str: Result of the operation (OK / NOK)
        """
        retries = 0

        while retries < max_retries: 
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(3)
                self.socket.connect((Config.device_ip, Config.device_port)  )      
                time.sleep(delay)
                self.driver_comm.status.emit(True)
                return "OK"
            except Exception as e:
                logging.warning(f'Connection attempt {retries + 1} failed: {e}')
                retries += 1                    
                time.sleep(delay)
                print(e)
            
        
        logging.error(f"Failed to connect to the focuser motor after {retries} tries")
        return "NOK"
        

    def disconnect_motor(self) -> str:
        try:
            if self.socket:
                while self._lock.locked(): pass     # Waits if a message is being transfered so that the socket is not closed mid-transfer
                self.socket.close()
                self.socket = None
                self.driver_comm.status.emit(False)
                self.driver_comm.timeout.emit(True)
                self.motor.connected = False
                return "OK"
            else:
                logging.warning(f"Cannot disconnect motor: Socket not open")
                return "NOK"
        except Exception as e:
            logging.error(f"Error disconnectig from motor: {e}")
            raise RuntimeError(f'Cannot disconnect -> {e}') 
    #self._lock.release()
    
    def ping_motor(self) -> str:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            retries = 0
            max_retries = 5
            sock.settimeout(0.5)
            while retries < max_retries:
                result = sock.connect_ex((Config.device_ip, Config.device_port))
                if result == 0:
                    self.motor.signals.moving.status.connect(self._check_normal_speed)
                    return "OK"
                time.sleep(TimeDelays.RETRY_TIMEOUT)

            return "NOK"                
        

    def _check_normal_speed(self, moving:bool):
        """In the DMX motor the normal speed is equal to the high speed.
        When a movement starts the program checks is the speed was
        changed and sets it back to normal.

        :param moving: If the motor is moving
        :type moving: bool
        """
        if moving and self.socket:
            val = self.param_max_speed()
            if val != str(Config.max_speed):
                # print('**********Setting normal speed back to original value**********')
                self.param_max_speed(Config.max_speed)

    
    def conv_position_show(self, encoder_pos: int | None = None, type: str = "int") -> int | float:
        """Reads motor encoder position and converts to microns

        :return: Motor position in microns
        :rtype: int | float
        """
        if encoder_pos is None:
            encoder_pos = self.read_encoder()
        pos = round(encoder_pos/Config.enc_2_microns)
        if type == "int":
            return int(pos)
        else:
            return pos
        
    def set_position(self, position: int) -> str:
        """ #DEPRECATED
        Moves the motor to a specific position in microns

        :param position: Target position in microns
        :type position: int
        :raises RuntimeError: R
        :return: _description_
        :rtype: str | Exception
        """
        # self._lock.acquire()
        pos_conv = int(round((Config.enc_2_microns * position), 0)) 
        resp = self._write(f"V20={pos_conv}")
        if resp == "OK":            
            resp = self._write(f"GS29")
            if resp == "OK":
                return resp
        raise Exception(f'[Device] Error moving motor to target position {position}: Error info -> {str(resp)}')
        
    def read_encoder(self) -> int:
        response = self._write("EX")
        if self.is_convertible_to_int(response):
            enc = int(response)
            return enc
        else:
            return constants.INVALID_RESPONSE

    
    def read_homing(self) -> bool: 
    #   The current version of the motor firmware do not implement
    # a variable that indicates the 'homing' process.
    #   To indicate homing the program counter is read and if it is
    # inside the homing function it is homing.
    #   IMPORTANT: This will only work with this specific mnotor firmware
        x = self._write("SPC0")
        if 507 <= int(x) < 564:
            return True
        else:
            return False
             
        # x = self._write("V15")
        # if x == "1":
        #     return True                     
        # else:                                       
        #     return False
        
        

    def read_parking(self) -> bool:
        # self._lock.acquire()
        x = self._write("V16")
        # if "1" in x:
        if x == "1":
            return True                     
        else:                                       
            return False


    def read_initialized(self) -> bool:
        """Checks if initialization was previously executed"""
        x = self._write("V44")
        if "64" in x:                               #TODO: O valor 64 é o ID desse motor específico, seriam utilizados valores diferentes para cada motor?
            return True
        else:
            return False
    
    def read_status(self) -> int:       #TODO: Adicionar tratamento da mensagem de status para padronizar independente do motor
        """Checks motor status

        To allow the code to work with both motors this method also calls
        'read_alarm_status'
        """
        motor_status: int = 0

        if self.read_alarm_status() | self.check_stall():
            motor_status |= MotorStatusFlags.ALARM
        
        resp = self._write("MST")
        if resp != "NOK":
            resp = format(int(resp), '012b')
            resp = "".join(reversed(resp))

            if(resp[0] == '1' or resp[1] == '1' or resp[2] == '1'): 
                # Bit '0' indicates the 'moving' status | Bit '1' indicates acceleration  | Bit '2' indicates deceleration     
                motor_status |= MotorStatusFlags.MOVING

            if(resp[4] == '1'):                                 # Bit '4' indicates the lim minus microswitch status
                motor_status |= MotorStatusFlags.LIM_MIN

            if(resp[5] == '1'):                                 # Bit '5' indicates the lim max microswitch status
                motor_status |= MotorStatusFlags.LIM_MAX

            return motor_status
        return MotorStatusFlags.INVALID
    
    def read_alarm_status(self) -> bool:
        """Checks if the ALM bit is set
        
        In the DMX motor the ALM bit only indicates the over temperature error

        :return: Bool indicating if an alarm is set
        :rtype: bool
        """
        resp = self._write("ALM")
        if resp != "NOK":
            if resp == '1':
                return True
            else:
                return False
        return False            #TODO: verificar o que fazer nesse caso

    def check_stall(self):
        resp = self._write("V25")
        if resp != "NOK":
            if resp == '1':
                return True
            else:
                return False
        return False            #TODO: verificar o que fazer nesse caso


    def parse_alarm_info(self) -> MotorAlarmInfo:
        """Verifies the motor error responsible for setting the alarm bit"""
        # The DMX motor only sets the alarm bit with an over temperature error (temp > 70º)
        return MotorAlarmInfo.OVER_TEMP

   
    def param_IP(self, value = None) -> str:
        if value:
            resp = self._write(f"IP={value}")
            if resp == "NOK":
                return f'[Device] Failed to configure new IP'
            else: 
                return "OK"
        else:
            return self._write("IP")
   
    def param_backlash(self, value: int | float | None = None, converted:bool = False) -> str | None:
        if value:
            value = int(value * Config.enc_2_microns)    # Converts to encoder value
            val_str = str(value)
            resp = self._write(f"V74={val_str}")
            if resp == "NOK":
                return f'[Device] Failed to configure new BACKLASH'
            else: 
                return "OK"
        else:
            # resp = self._write("V74")
            resp = str(Config.backlash)
            # if self.is_convertible_to_int(resp):
            #     resp = int(resp)
            return resp
            # else:
            #     return f'[Device] Failed to configure new BACKLASH'


    def param_max_pos(self, value: int | float | None = None, converted:bool = False) -> str | None:
        if value:
            pos = int(value * Config.enc_2_microns)    # Converts to encoder value
            pos_str = str(pos)
            resp = self._write(f"V71={pos_str}")
            if resp == "NOK":
                return f'[Device] Failed to configure new MAX_POS'
            else: 
                return "OK"
        else:
            # resp = self._write("V71")
            resp = str(Config.max_pos)
            if self.is_convertible_to_int(resp):
                # pos = int(resp) / Config.enc_2_microns    # When read from motor the value is in encoder position
                pos = int(resp)                             # When read from config file the value is in microns
                return f"{pos:.0f}"
            # return "NOK"
        
    def param_park_pos(self, value: int | float | None = None, converted:bool = False) -> str | None:
        if value:
            pos = int(value * Config.enc_2_microns)
            pos_str = str(pos)
            resp = self._write(f"V83={pos_str}")
            return resp
        else:
            # print("Reading park pos value")
            # resp = self._write("V83")
            resp = str(Config.park_pos)
            if self.is_convertible_to_int(resp):
                # pos = int(resp) / Config.enc_2_microns    # When read from motor the value is in encoder position
                pos = int(resp)                             # When read from config file the value is in microns
                return f"{pos:.0f}"
            # else: 
            #     return "NOK"
            
    def param_max_speed(self, value: int | None = None, converted:bool = False) -> str | None:
        # Speed unit is in pulses/second
        if value:
            if (value * Config.speed_factor) > Config.speed_security:
                logging.warning(f"Tried to set max speed to {value} but maximum allowed value is {Config.speed_security}")
                return f"Tried to set max speed to {value} but maximum allowed value is {Config.max_speed}"
            resp = self._write(f"V75={int(value * Config.speed_factor)}")             # Flash memory position used to retain the high speed configuration after reboot
            if resp != "NOK":
                resp = self._write(f"HSPD={int(value * Config.speed_factor)}")         # Convert to encoder
                if resp != "NOK":
                    return "OK"
            # If this point is reached an error occured
            return f'[Device] Failed to configure new MAX_SPEED'
        else:
            resp = self._write("HSPD")
            # resp = str(Config.max_speed)
            if self.is_convertible_to_int(resp):
                # return resp
                return str(int(int(resp) / Config.speed_factor))
            # else:
            #     return "NOK"
    
    def param_normal_speed(self, value: int | None = None, converted:bool = False) -> str | None:
    # DMX firmware do not implement a 'Normal speed'
        if value:
            return self.param_max_speed(value)
        else:
            return self.param_max_speed()
    
    def param_low_speed(self, value: int | None = None, converted:bool = False) -> str | None:
        if value:
            if value >= Config.max_speed:
                logging.warning(f"Tried to set low speed to {value} but value is greater than max_speed {Config.max_speed}")
                return f"Tried to set low speed to {value} but value is greater than max_speed {Config.max_speed}"

            resp = self._write(f"V76={value * Config.speed_factor}")             # Flash memory position used to retain the low speed configuration after reboot
            if resp != "NOK":
                resp = self._write(f"LSPD={value * Config.speed_factor}")
                if resp != "NOK":
                    return "OK"
            # If this point is reached an error occured
            return f'[Device] Failed to configure new LOW_SPEED'
        else:
            # resp = self._write("LSPD")
            resp = str(Config.low_speed)
            if self.is_convertible_to_int(resp):
                return resp
            # else:
            #     return "NOK"
            
    def param_max_step(self, value = None) -> str:
        #TODO: Implementar
        if value:
            return "OK"
        else:
            return "0"
            
    def param_acceleration(self, value = None) -> str:
        #TODO: Implementar
        if value:
            return "OK"
        else:
            return "0"
                
    def param_deceleration(self, value = None) -> str:
        #TODO: Implementar
        if value:
            return "OK"
        else:
            return "0"
            
    def param_idle_current(self, value = None) -> str:
        #TODO: Implementar
        if value:
            return "OK"
        else:
            return "0"
            
    def param_run_current(self, value = None) -> str:
        #TODO: Implementar
        if value:
            return "OK"
        else:
            return "0"
            
    def param_acc_current(self, value = None) -> str:
        #TODO: Implementar
        if value:
            return "OK"
        else:
            return "0"

    
    def param_tcp_rtmo(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    
    def param_tcp_cycle(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    
    def param_tcp_mbtmo(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    
    def param_tcp_katmo(self, value: int | float | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""

    def param_clp_auto_restart(self, value: bool | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...


    def param_motor_auto_restart(self, value: bool | None = None, converted:bool = False) -> str | None:
        """Precisa ser implementada pelo driver"""
    ...

    def read_firmware_version(self) -> str | None:
        V1 = self._write("V90")    # Version number
        V2 = self._write("V91")    # Update number
        V3 = self._write("V92")    # Bug fix number
        if (V1 != "NOK") and (V2 != "NOK") and (V3 != "NOK"):
            return f"{V1}.{V2}.{V3}"
        # else: 
        #     return "NOK"

    def read_firmware_status(self) -> str:
        resp = self._write("SASTAT")
        if resp != "NOK":
            match resp:
                case '0':
                    return "Idle"
                case '1':
                    return "Running"
                case '2':
                    return "paused"
                case '4':
                    return "ERROR"
                case _:
                    return "invalid" 
        return resp
        
    def sendCommand(self, command: str) -> str:
        return self._write(command)
    

    # def move_to(self, pos: int) -> str:
    def move_to(self, pos_str: str) -> str | None:
        # print(f"Sending move to command to position {pos_str}...")
        pos = int(pos_str)
        pos_conv = int(round((Config.enc_2_microns * pos), 0)) 
        resp = self._write(f"V20={pos_conv}")
        if resp == "OK":            
            resp = self._write(f"GS29")
            if resp == "OK":
                return resp
        # raise RuntimeError(f'[Motor] Error moving motor to target position {pos}')
        return "NOK"
        
             

    # def focus_in(self, speed: int) -> str:
    def focus_in(self, speed: str | int = Config.normal_speed) -> str | None:
        # print(f"Sending focus in command with speed {speed}...")
        self._set_speed(int(speed))
        resp = self._write('GS21')
        if resp == "OK":
            return resp
        return "NOK"
        # raise RuntimeError(f'[Motor] Error running "FOCUS_IN" command')

    # def focus_out(self, speed: int) -> str:
    def focus_out(self, speed: str | int = Config.normal_speed) -> str | None:
        # print(f"Sending focus out command with speed {speed}...")
        self._set_speed(int(speed))
        resp = self._write('GS20')
        if resp == "OK":
            return resp
        return "NOK"
        # raise RuntimeError(f'[Motor] Error running "FOCUS_OUT" command')

    def halt(self) -> str | None:
        # print("Sending halt command...")
        resp = self._write('V42=1')
        if resp == "OK":
            return resp
        return "NOK"
        # raise RuntimeError(f'[Motor] Error running "HALT" command')
             

    def home(self) -> str | None:
        # print("Sending home command...")
        resp = self._write('GS30')
        if resp == "OK":
            return resp
        return "NOK"
        
        # raise RuntimeError(f'[Motor] Error running "HOME" command')
        
             

    def park(self) -> str | None:
        # print("Sending park command...")
        resp = self._write('GS5')
        if resp == "OK":
            return resp
        return "NOK"
        # raise RuntimeError(f'[Motor] Error running "PARK" command')

    def _set_speed(self, speed: int) -> str:
        # print(f"Setting motor movement speed")
        vel_conv = speed*Config.speed_factor
        if vel_conv > Config.speed_security:
            vel_conv = Config.speed_security     
        
        resp = self._write(f'V21={str(vel_conv)}')
        if resp == "OK":
            return resp
        else:
            raise RuntimeError(f'[MOTOR] Error setting motor movement speed')

    def _store_to_flash(self) -> str:
        """Stores the settings to the motor flash
         Some settings will only be changed after a hard reset check table 7.15 of the DMS-ETH manual
         If '_store_to_flash' is not executed the variables saved in V51~V100 will be lost after a hard reset
         #TODO: O firmware do motor reseta os valores de max_pos, backlash, max_speed e low_speed durante o boot."""
        return self._write("STORE")

#region backup version
    # def _write(self, cmd: str, max_retries = 5):
    #     """Send commands to motor socket.
    #     Args:  
    #         cmd (str): Command.
    #         max_retries (int): Number of retries if first one fails
    #     Returns: 
    #         Device response or Error message
    #     """
    #     # The ARCUS DMX motor don't seem to accept retries, if an error
    #     # occurs the connection must be reset
    #     retries = 0
    #     self._lock.acquire()  
    #     # time.sleep(0.01)
    #     if self.socket:
    #         while (time.time() - self.time_count) < 0.020_000: 
    #             time.sleep(0.000_005)

    #         print(time.time() - self.time_count)
    #         while retries < max_retries: 
    #             # time.sleep(0.01)     # time.sleep(0.1)  
    #             try:   
    #                 # self.socket.sendall(bytes(f'{cmd}\x00', 'utf-8'))
    #                 format_cmd = f'{cmd}\x00'.encode('ascii')
    #                 self.socket.sendall(format_cmd)

    #                 time.sleep(0.02)         # time.sleep(0.1) 

    #                 response = self.socket.recv(256) #1024
    #                 self._lock.release()
    #                 # time.sleep(0.05)
    #                 self.time_count = time.time()
    #                 return response.decode('ascii').replace("\x00", "")         
    #                 # return response.decode('utf-8').replace("\x00", "")                    
    #             except Exception as e:
    #                 logging.warning(f"Focuser motor message timed out: {e}")
    #                 time.sleep(0.05)
    #                 retries += 1   
    #                 err = e

    #     # If the program reaches this points it means that a problem occurred in sending or receiving the data
    #         # self.logger.error(f"[Device] Error writing {cmd}: {str(err)}")
    #     print(f"RETRIES {retries}")
    #     if self._lock.locked:
    #         self._lock.release()
    #     if self.socket:
    #         self.disconnect_motor() 
    #     # raise ConnectionError(f'Could not send command "{cmd}" to motor. Failed to reach motor after {retries} attempts.')
    #     return 'NOK' #"Error communicating to the motor" 
#endregion

    def _write(self, cmd: str, max_retries = 5) -> str:
        """Send commands to motor socket.
        Args:  
            cmd (str): Command.
            max_retries (int): Number of retries if first one fails
        Returns: 
            Device response or Error message
        """
        # The ARCUS DMX motor don't seem to accept retries, if an error
        # occurs the connection must be reset
        retries = 0
        
        # time.sleep(0.01)
        if self.socket:
            self._lock.acquire()  
            # Waits at least 20 milisseconds before sending new data
            while (time.time() - self.time_count) < 0.080_000: # 0.025_000: 
                time.sleep(0.000_005)

            # print(time.time() - self.time_count)

            try:
                format_cmd = f'{cmd}\x00'.encode('ascii')
                try:
                    self.socket.sendall(format_cmd)
                except Exception as error:
                    print(f"Exception occured on send")
                    raise error
                
                # time.sleep(0.010)

                response = bytearray()
                chunk = bytes()


                # while chunk != b'\x00':
                #     chunk = self.socket.recv(1)
                #     response.extend(chunk)

                # Receives up to 20 bytes until receive '\x00'
                # Exits if a timeout occurs
                while True:
                    chunk = self.socket.recv(20)
                    response.extend(chunk)
                    if b'\x00' in response:
                        break

                # print(response)
                # self._flush_stale_data()
                self.time_count = time.time()
                self._lock.release()

                return response.decode('ascii').replace("\x00", "")         
            except Exception as error:
                self.timeout_counter += 1
                print(f"Timeout counter: {self.timeout_counter}")
                logging.warning(f"Motor communication timed out during command '{cmd}': {error}")
                # self._flush_stale_data()
                if self._lock.locked():
                    self._lock.release()
                if self.socket:
                    self.disconnect_motor() 
                return 'NOK' #"Error communicating to the motor" 
        return 'NOK'

    def _flush_stale_data(self):
        """Drains leftover bytes if a previous read was interrupted."""
        if self.socket:
            self.socket.setblocking(False)
            try:
                while self.socket.recv(1024):
                    pass
            except (BlockingIOError, socket.error):
                pass
            finally:
                self.socket.setblocking(True)
                self.socket.settimeout(3)

    def _update_all_parameters(self):
        resp: str = ""
        p = 0
        if self.socket:
            for param_idx in MotorParamsIdx:
                p += 1
                self.motor.signals.progress.string.emit(int(p/len(MotorParamsIdx)*100))
                # time.sleep(0.05)            # Just for better visualization of ui update
                resp = self.param_methods[param_idx]()
                try:
                    val = float(resp)
                    # print(f'{self.motor.parameters[param_idx]} - {int(self.param_methods[param_idx](converted=True))}')
                except:
                    val = resp
                # print(f'{param_idx}, {val}')
                if val is not None:
                    self.param_methods[param_idx](value=val)
            self._store_to_flash()
                