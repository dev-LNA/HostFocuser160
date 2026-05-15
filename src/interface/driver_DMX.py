from src.interface.motor_driver import Driver
from src.core.config import Config

from threading import Lock
import time
import socket

from contextlib import closing
from src.utils.constants import constants, MotorStatusFlags, MotorAlarmInfo


class DriverDMX(Driver):

    def __init__(self, model):  #TODO: Criar classe (IntNum) com os modelos possíveis de motores
        super().__init__(model)
        self.socket = None
        self._lock = Lock()
    
    def connect_motor(self, max_retries = 5, delay = 0.1) -> str:
        """Connects the device and open socket connection

        Args:
            max_retries (int, optional): Number os tries if first one fail. Defaults to 5.
            delay (float, optional): Small delay, in seconds, to wait after a try. Defaults to 0.1.

        Returns:
            str: Result of the operation (OK / NOK)
        """
        retries = 0
        connected_successfully = False

        while retries < max_retries and not connected_successfully:         #TODO: Se o while não checar o "max_retries" isso pode ser checado dentro da exception, finalizando se passar da quantidade de retries
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(.6)
                self.socket.connect((Config.device_ip, Config.device_port)  )      
                time.sleep(delay)
                connected_successfully = True
                self.driver_comm.status.emit(True)
            except Exception as e:
                # self.logger.error(f'Connection attempt {retries + 1} failed: {e}')
                retries += 1                    
                time.sleep(delay)
                print(e)
            
        if not connected_successfully:   
            raise ConnectionError(f'Failed to connecto to the motor: {str(e)}')       
            # return "NOK"
        else:
            return "OK"

    def disconnect_motor(self) -> str:
        try:
            if self.socket:
                while self._lock.locked(): pass     # Waits if a message is being transfered so that the socket is not closed mid-transfer
                self.socket.close()
                self.socket = None
                self.driver_comm.status.emit(False)
            return "OK"
        except Exception as e:
            raise RuntimeError(f'Cannot disconnect -> {e}') 
    #self._lock.release()
    
    def ping_motor(self) -> str:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((Config.device_ip, Config.device_port))

            if result == 0:
                return "OK"
            else:
                return "NOK"
        

    def conv_position(self, encoder_pos: int = None) -> int:
        """Reads motor encoder position and converts to microns

        :raises ValueError: If the reading is not valid
        :return: _description_
        :rtype: int | Exception
        """
        if encoder_pos is None:
            encoder_pos = self.read_encoder()
        pos = int(round(encoder_pos/Config.enc_2_microns))
        return pos
        
    def set_position(self, position: int) -> str:
        """Moves the motor to a specific position in microns

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
        x = self._write("V15")
        if "1" in x:
            return True                     
        else:                                       
            return False
        

    def read_parking(self) -> bool:
        # self._lock.acquire()
        x = self._write("V16")
        if "1" in x:
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
   
    def param_backlash(self, value = None) -> str:
        if value:
            value = str(int(value) * Config.enc_2_microns)    # Converts to encoder value
            resp = self._write(f"V74={value}")
            if resp == "NOK":
                return f'[Device] Failed to configure new BACKLASH'
            else: 
                return "OK"
        else:
            resp = self._write("V74")
            if self.is_convertible_to_int(resp):
                resp = int(resp)
                return f"{round(resp / Config.enc_2_microns, 0):.0f}"  # Converts to microns
            else:
                return f'[Device] Failed to configure new BACKLASH'


    def param_max_pos(self, value = None) -> str:
        if value:
            pos = str(int(value) * Config.enc_2_microns)    # Converts to encoder value
            resp = self._write(f"V71={pos}")
            if resp == "NOK":
                return f'[Device] Failed to configure new MAX_POS'
            else: 
                return "OK"
        else:
            resp = self._write("V71")
            if self.is_convertible_to_int(resp):
                pos = int(resp) / Config.enc_2_microns
                return f"{pos:.0f}"
    
    def param_max_speed(self, value = None) -> str:
        if value:
            resp = self._write(f"V75={value}")             # Flash memory position used to retain the high speed configuration after reboot
            if resp != "NOK":
                resp = self._write(f"HSPD={value}")
                if resp != "NOK":
                    return "OK"
            # If this point is reached an error occured
            return f'[Device] Failed to configure new MAX_SPEED'
        else:
            resp = self._write("HSPD")
            if self.is_convertible_to_int(resp):
                return resp
            else:
                return "NOK"
    
    def param_normal_speed(self, value = None) -> str: # DMX firmware do not implement a 'Normal speed'
        if value:
            return self.param_max_speed(value)
        else:
            return self.param_max_speed()
    
    def param_low_speed(self, value = None):
        if value:
            resp = self._write(f"V76={value}")             # Flash memory position used to retain the low speed configuration after reboot
            if resp != "NOK":
                resp = self._write(f"LSPD={value}")
                if resp != "NOK":
                    return "OK"
            # If this point is reached an error occured
            return f'[Device] Failed to configure new LOW_SPEED'
        else:
            resp = self._write("LSPD")
            if self.is_convertible_to_int(resp):
                return resp
            else:
                return "NOK"
    
    def param_park_pos(self, value = None) -> str:
        if value:
            pos = str(int(value) * Config.enc_2_microns)
            resp = self._write(f"V83={pos}")
            return resp
        else:
            print("Reading park pos value")
            resp = self._write("V83")
            if self.is_convertible_to_int(resp):
                pos = int(resp) / Config.enc_2_microns
                return f"{pos:.0f}"
            else: 
                return "NOK"
            
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
            
    def read_firmware_version(self) -> str:
        V1 = self._write("V90")    # Version number
        V2 = self._write("V91")    # Update number
        V3 = self._write("V92")    # Bug fix number
        if (V1 != "NOK") and (V2 != "NOK") and (V3 != "NOK"):
            return f"{V1}.{V2}.{V3}"
        else: 
            return "NOK"

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
    

    def move_to(self, pos: int) -> str:
        print(f"Sending move to command to position {pos}...")
        pos_conv = int(round((Config.enc_2_microns * pos), 0)) 
        resp = self._write(f"V20={pos_conv}")
        if resp == "OK":            
            resp = self._write(f"GS29")
            if resp == "OK":
                return resp
        raise RuntimeError(f'[Motor] Error moving motor to target position {pos}')
        
             

    def focus_in(self, speed: int) -> str:
        print(f"Sending focus in command with speed {speed}...")
        self._set_speed(speed)
        resp = self._write('GS21')
        if resp == "OK":
            return resp
        raise RuntimeError(f'[Motor] Error running "FOCUS_IN" command')

    def focus_out(self, speed: int) -> str:
        print(f"Sending focus out command with speed {speed}...")
        self._set_speed(speed)
        resp = self._write('GS20')
        if resp == "OK":
            return resp
        raise RuntimeError(f'[Motor] Error running "FOCUS_OUT" command')

    def halt(self) -> str:
        print("Sending halt command...")
        resp = self._write('V42=1')
        if resp == "OK":
            return resp
        raise RuntimeError(f'[Motor] Error running "HALT" command')
             

    def home(self) -> str:
        print("Sending home command...")
        resp = self._write('GS30')
        if resp == "OK":
            return resp
        raise RuntimeError(f'[Motor] Error running "HOME" command')
        
             

    def park(self) -> str:
        print("Sending park command...")
        resp = self._write('GS5')
        if resp == "OK":
            return resp
        raise RuntimeError(f'[Motor] Error running "PARK" command')

    def _set_speed(self, speed: int) -> str:
        print(f"Setting motor movement speed")
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

    def _write(self, cmd, max_retries = 5):
        """Send commands to motor socket.
        Args:  
            cmd (str): Command.
            max_retries (int): Number of retries if first one fails
        Returns: 
            Device response or Error message
        """
        retries = 0
        self._lock.acquire()  
        # time.sleep(0.01)         # time.sleep(0.1)  #TODO: Avaliar o motivo de precisar desse tempo morto
        if self.socket:
            while retries < max_retries: 
                time.sleep(0.01)         # time.sleep(0.1)  #TODO: Avaliar o motivo de precisar desse tempo morto
                try:   
                    self.socket.sendall(bytes(f'{cmd}\x00', 'utf-8'))
                    response = self.socket.recv(1024)
                    self._lock.release()
                    return response.decode('utf-8').replace("\x00", "")                    
                except Exception as e:
                    err = e
                retries += 1                                                               #TODO: Parece que esse retries tem que estar dentro do exception, mas talvez não faça diferença
            
        # If the program reaches this points it means that a problem occurred in sending or receiving the data
            # self.logger.error(f"[Device] Error writing {cmd}: {str(err)}")
        print(f"RETRIES {retries}")
        self._lock.release()
        if self.socket:
            self.disconnect_motor() 
        # raise ConnectionError(f'Could not send command "{cmd}" to motor. Failed to reach motor after {retries} attempts.')
        return 'NOK' #"Error communicating to the motor" 
