from src.interface.motor_driver import Driver
from src.core.config import Config

from threading import Lock
import time
import socket

from contextlib import closing


class DriverDMX(Driver):
    def __init__(self, model, config: Config):  #TODO: Criar classe (IntNum) com os modelos possíveis de motores
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
            except Exception as e:
                # self.logger.error(f'Connection attempt {retries + 1} failed: {e}')
                retries += 1                    
                time.sleep(delay)
                print(e)
            
        if not connected_successfully:          
            return "NOK"
        else:
            return "OK"

    def disconnect_motor(self) -> str:
        try:
            while self._lock.locked(): pass     # Waits if a message is being transfered so that the socket is not closed mid-transfer
            self.socket.close()
            self.socket = None
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
        

    def read_position(self) -> int | Exception:
        """Reads motor encoder position and converts to microns

        :raises ValueError: If the reading is not valid
        :return: _description_
        :rtype: int | Exception
        """
        try:
            encoder = self.read_encoder()
            pos = int(round(encoder/Config.enc_2_microns))
            return pos
        except Exception as e:
            return e
        
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
        resp = self._write(f"V20={pos_conv}", max_retries=5)
        if resp == "OK":            
            resp = self._write(f"GS29", max_retries=5)
            if resp == "OK":
                return resp
        raise Exception(f'[Device] Error moving motor to target position {position}: Error info -> {str(resp)}')
        
    def read_encoder(self):
        response = self._write("EX", max_retries=5)
        if self.is_convertible_to_int(response):
            enc = int(response)
            return enc
        else:
            raise ValueError(f'[Device] Error reading encoder position -> Motor response: {response}')

    
    def read_homing(self) -> bool:  
        x = self._write("V15", max_retries=5)
        if "1" in x:
            return True                     
        else:                                       
            return False
        

    def read_parking(self) -> bool:
        # self._lock.acquire()
        x = self._write("V16", max_retries=5)
        if "1" in x:
            return True                     
        else:                                       
            return False


    def read_initialized(self) -> bool:
        """Checks if initialization was previously executed"""
        x = self._write("V44", max_retries=5)
        if "64" in x:                               #TODO: O valor 64 é o ID desse motor específico, seriam utilizados valores diferentes para cada motor?
            return True
        else:
            return False
    
    def read_status(self) -> str:       #TODO: Adicionar tratamento da mensagem de status para padronizar independente do motor
        return self._write("MST", 5)
    


   
    def param_IP(self, value = None) -> str:
        if value:
            resp = self._write(f"IP={value}", 5)
            if resp == "NOK":
                return f'[Device] Failed to configure new IP'
            else: 
                return "OK"
        else:
            return self._write("IP", 5)
   
    def param_backlash(self, value = None) -> str:
        if value:
            value = str(int(value) * Config.enc_2_microns)    # Converts to encoder value
            resp = self._write(f"V74={value}")
            if resp == "NOK":
                return f'[Device] Failed to configure new BACKLASH'
            else: 
                return "OK"
        else:
            resp = self._write("V74", 5)
            if self.is_convertible_to_int(resp):
                resp = int(resp)
                return f"{round(resp / Config.enc_2_microns, 0):.0f}"  # Converts to microns
            else:
                return f'[Device] Failed to configure new BACKLASH'


    def param_max_pos(self, value = None) -> str:
        if value:
            pos = str(int(value) * Config.enc_2_microns)    # Converts to encoder value
            resp = self._write(f"V71={pos}", 5)
            if resp == "NOK":
                return f'[Device] Failed to configure new MAX_POS'
            else: 
                return "OK"
        else:
            resp = self._write("V71", 5)
            if self.is_convertible_to_int(resp):
                pos = int(resp) / Config.enc_2_microns
                return f"{pos:.0f}"
    
    def param_max_speed(self, value = None) -> str:
        if value:
            self._write(f"V75={value}")             # Flash memory position used to retain the high speed configuration after reboot
            if resp != "NOK":
                resp = self._write(f"HSPD={value}")
                if resp != "NOK":
                    return "OK"
            # If this point is reached an error occured
            return f'[Device] Failed to configure new MAX_SPEED'
        else:
            resp = self._write("HSPD", 5)
            if self.is_convertible_to_int(resp):
                return resp
            else:
                return "NOK"
    
    def param_normal_speed(self, value = None) -> str: # No DMX não está implementada uma "normal speed", então "normal speed == max speed"
        return self.param_max_speed(self, value=value)
    
    def param_low_speed(self, value = None):
        if value:
            self._write(f"V76={value}")             # Flash memory position used to retain the high speed configuration after reboot
            if resp != "NOK":
                resp = self._write(f"HSPD={value}")
                if resp != "NOK":
                    return "OK"
            # If this point is reached an error occured
            return f'[Device] Failed to configure new LOW_SPEED'
        else:
            resp = self._write("LSPD", 5)
            if self.is_convertible_to_int(resp):
                return resp
            else:
                return "NOK"
    
    def param_park_pos(self, value = None) -> str:
        if value:
            pos = str(int(value) * Config.enc_2_microns)
            resp = self._write(f"V83={pos}", 5)
            return resp
        else:
            print("Reading park pos value")
            resp = self._write("V83", 5)
            if self.is_convertible_to_int(resp):
                pos = int(resp) / Config.enc_2_microns
                return f"{pos:.0f}"
            else: 
                return "NOK"
            
    def read_firmware_version(self) -> str:
        V1 = self._write("V90", 5)    # Version number
        V2 = self._write("V91", 5)    # Update number
        V3 = self._write("V92", 5)    # Bug fix number
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
        else:
            return resp
        
    def sendCommand(self, command: str) -> str:
        return self._write(command)

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
        time.sleep(0.05)         # time.sleep(0.1)  #TODO: Avaliar o motivo de precisar desse tempo morto
        while retries < max_retries:  
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
            self._lock.release()
            self.disconnect_motor() 
            return 'NOK' #"Error communicating to the motor" 
        else:
            return 'NOK' #"Not connected"