from PyQt6.QtCore import QObject, pyqtSignal
from src.utils.signals import PropertySignals

from logging import Logger

from threading import Lock
from threading import Timer

from src.core.config import Config
from src.core.exceptions import DriverException
from src.utils.constants import constants

from contextlib import closing
import socket
import time

class FocuserDriver(QObject):
    signal_motor_is_moving = pyqtSignal(bool)
    signal_status_lim_min = pyqtSignal(bool)
    signal_status_lim_max = pyqtSignal(bool)

    def __init__(self, logger: Logger, model: str):  
        super(FocuserDriver, self).__init__()
        self._lock = Lock()
        self.name: str = 'LNA Focuser'
        self.logger = logger

        self.model = model

        self.motor_socket = None
        
        self._step_size: float = 1.0
        
        self._reverse = False
        self._absolute = True
        self._max_step = Config.max_step
        self._max_increment = 100
        self._is_moving = False
        self._connected = False
        self._status = ""
        
        self._temp_comp = False 
        self._temp_comp_available = False
        self._temp = 0.0 
        self._steps_per_sec = 1

        self._position = 0
        self._last_pos = 0
        self._tgt_position = 0
        self._stopped = True
        self._homing = False
        self._parking = False
        self._at_home = False
        self._initialized = False
        self._alarm = 0

        self._timeout = 1

        self._timer: Timer = None
        self._interval: float = .15

        self.property_handlers = {        
                'DEVICE_IP': 'device_IP',
                'BACKLASH': 'backlash',
                'MAX_POS': 'max_pos',
                'PARK': 'park_pos',
                'MAX_SPEED': 'max_speed',
                'NORMAL_SPEED': 'normal_speed',
                'LOW_SPEED': 'low_speed'
            }
        
    def acionar(self):
        self.signal_motor_is_moving.emit(True)
        print(self.initialized)

    @property
    def connected(self):
        # self._lock.acquire()
        res = self._connected
        #self._lock.release()
        return res
    @connected.setter 
    def connected(self, connected: bool, max_retries=5, delay=.1):
        """Connects the device and open socket connection
        Args:
            connected (bool): Sets the connected state
            max_retries (int): Number os tries if first one fail
            delay (float): Small delay, in seconds, to wait after a try
        """
        # self._lock.acquire()
        self._connected = connected     
        if connected:
            #self._lock.release()
            retries = 0
            connected_successfully = False

            while retries < max_retries and not connected_successfully:         #TODO: Se o while não checar o "max_retries" isso pode ser checado dentro da exception, finalizando se passar da quantidade de retries
                try:
                    self.motor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.motor_socket.settimeout(.6)
                    self.motor_socket.connect((Config.device_ip, Config.device_port))                    
                    time.sleep(delay)
                    connected_successfully = True
                except Exception as e:
                    self.logger.error(f'Connection attempt {retries + 1} failed: {e}')
                    retries += 1                    
                    time.sleep(delay)
                    if retries >=4:                 #TODO: O certo seria checar "max_retries - 1" ?
                        # self._lock.acquire()
                        self._connected = False
                        #self._lock.release()
                
            if not connected_successfully:          #TODO: Isso aqui não pode ficar dentro da checagem de "if retries >= max_retries-1" acima?
                # self._lock.acquire()
                self._connected = False
                #self._lock.release()
                self.logger.error('Failed to establish a connection after retries')
                raise RuntimeError('Cannot Connect')

        else:
            self._connected = False     #TODO: A modificação de `_connected` para false não deveria ser feita somente na função "disconnect" no caso de ter dado certo a desconexão? Senão na hora que for para a função "disconnect" não vai passar pelo `if` e a função não vai fazer nada. Outra opção é só esse método não aceitar "false" como entrada.
            #self._lock.release()
            self.disconnect()

        if self._connected:
            self.logger.info('[Connected]')
        else:
            self.logger.info('[Disconnected]')
    
    def disconnect(self):
        """Disconnects device and close socket"""
        # self._lock.acquire()
        if self._connected:
            try:
                while self._lock.locked(): pass     # Waits if a message is being transfered so that the socket is not closed mid-transfer
                self.motor_socket.close()
                self.motor_socket = None
                self._connected = False
            except:
                raise RuntimeError('Cannot disconnect')     #TODO: Daria para fornecer mais informação do motivo de não ter dado certo?
        #self._lock.release()
        
    def ping(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((Config.device_ip, Config.device_port))
                if result == 0:
                    return True
                else:
                    return False
                
    @property
    def temp(self):
        # self._lock.acquire()
        res = self._temp
        #self._lock.release()
        return res
    
    @property
    def temp_comp_available(self):
        # self._lock.acquire()
        res = self._temp_comp_available
        #self._lock.release()
        return res
    
    @property
    def temp_comp(self):
        # self._lock.acquire()
        res = self._temp_comp
        #self._lock.release()
        return res
    @temp_comp.setter
    def temp_comp(self, temp: bool):
        # self._lock.acquire()
        if not self._temp_comp_available and temp:
            self._temp_comp = False
        elif self._temp_comp_available:        
            self._temp_comp = temp
        #self._lock.release()

    @property
    def position(self) -> int:                      #TODO: Talvez o setter de position poderia chamar o método `move`
        """Device enconders position"""      
        try:
            # self._lock.acquire()
            response = self._write("EX", max_retries=5)
            if is_convertible_to_int(response):
                step = int(response) 
            
                self._position = int(round(step/Config.enc_2_microns))
                self._last_pos = self._position                             #TODO: Para que exatamente está servindo esse `_last_pos`?
                #self._lock.release()
                return self._position
        except ValueError as e:
            self.logger.error(f'[Device] Error reading position: {str(e)}')
            #self._lock.release()  
        return self._last_pos                                           #TODO: Colocar esse 'return' dentro do except?
    
    @property
    def is_moving(self) -> bool:                    #TODO: Possibilitar configurar número de retries?
        """Checks if device is moving"""            #TODO: Pelo programa do motor `V46` não indica necessariamente que o motor está em movimento, mas sim que uma subrotina está sendo executada. Em alguns pontos do programa do motor é utilizado `V9` para indicar que o motor está em movimento.
        # self._lock.acquire()
        x = self._write("V46", max_retries=5)       #TODO: Adicionar try .. except?
        # #self._lock.release()
        if x == "1":
            self._is_moving = True
            #self._lock.release()
            return self._is_moving                  #TODO: Desnecessário, pode ser feito só no final do método
        elif x == "0":
            self._is_moving = False 
            #self._lock.release()
            return self._is_moving                  #TODO: Desnecessário, pode ser feito só no final do método
        #self._lock.release()
        return self._is_moving

    @property
    def homing(self) -> bool:
        """Check if INIT routine is being executed"""
        # self._lock.acquire()
        x = self._write("V15", max_retries=5)
        if "1" in x:
            self._homing = True                     
        else:                                       
            self._homing = False
        #self._lock.release()
        return self._homing
    
    @property
    def parking(self) -> bool:
        # self._lock.acquire()
        x = self._write("V16", max_retries=5)
        if "1" in x:
            self._parking = True                     
        else:                                       
            self._parking = False
        #self._lock.release()
        return self._parking


    @property
    def initialized(self) -> bool:
        """Checks if initialization was previously executed"""
        # self._lock.acquire()
        x = self._write("V44", max_retries=5)
        if "64" in x:                               #TODO: O valor 64 é o ID desse motor específico, seriam utilizados valores diferentes para cada motor?
            self._initialized = True
        else:
            self._initialized = False
        #self._lock.release()
        return self._initialized

    @property
    def status(self) -> str:
        # self._lock.acquire()
        self._status = self._write("GS0")
        #self._lock.release()
        return self._status
    
    @property
    def absolute(self) -> bool:  
        # self._lock.acquire()      
        res = self._absolute
        #self._lock.release()
        return res

    @property
    def max_increment(self) -> bool:
        # self._lock.acquire()
        res = self._max_increment
        #self._lock.release()
        return res

    @property
    def max_step(self) -> bool:
        # self._lock.acquire()
        res = self._max_step
        #self._lock.release()
        return res

    @property
    def step_size(self) -> bool:
        # self._lock.acquire()
        res = self._step_size
        #self._lock.release()
        return res
    
    @property
    def alarm(self) -> int:                                 
        # self._lock.acquire()
        res = self._write("ALM", max_retries=5)
        #self._lock.release()
        try:                                                #TODO: O que ativaria uma exceção dentro desse try?
            self._alarm = int(res)
            if self._alarm == '1':
                self.logger.info('[Device] Temperature Alarm ON')   #TODO: Só a temperatura que aciona esse alarme?
        except Exception as e: 
            self._alarm = 0
            self.logger.error(f'[Device] Alarm Error {str(e)}')
        return self._alarm

    @property
    def driver_state(self) -> bool:
        """
        Verifies the state of the motor driver.
        
        :param self:
        :return: True if driver is active / False if driver is not active
        :rtype: bool
        """
        # self._lock.acquire()
        resp = self._write("EO", 5)
        if resp == '1':
            self.logger.info('[Device] Motor Driver ON')
            #self._lock.release()
            return True
        else:
            self.logger.info('[Device] Motor Driver OFF')
            #self._lock.release()
            return False
        
    @property
    def device_IP(self) -> str:
        """
        Returns the motor IP
        
        :param self:
        :return: String with the motor IP
        :rtype: str
        """
        # self._lock.acquire()
        resp = self._write("IP", 5)
        #self._lock.release()
        return resp
    @device_IP.setter
    def device_IP(self, value: str):
        # self._lock.acquire()
        self._write(f"IP={value}", 5)
        #self._lock.release()
    
    @property
    def device_ID(self) -> str:                     # TODO: Mudar para o ID do motor mesmo, não faz sentido mostra o ID do fornecedor
        """
        Returns the motor supplier ID
        
        :param self:
        :return: String with the motor ID
        :rtype: str
        """
        # self._lock.acquire()
        # resp = self._write("ID", 5)
        resp = self._write("V50", 5)                    # Hardware ID stored at memory V50 on DMX-ETH  
        #self._lock.release()
        return resp
    
    @property
    def device_Firmware_Version(self) -> str:       # TODO: Mudar para o firmware do software mesmo, não faz sentido mostra a versão de firmware do fabricante
        """
        Returns the motor firmware version
        
        :param self:
        :return: String with the motor firmware version
        :rtype: str
        """
        # self._lock.acquire()
        V1 = self._write("V90", 5)    # Version number
        V2 = self._write("V91", 5)    # Update number
        V3 = self._write("V92", 5)    # Bug fix number
        #self._lock.release()

        return f"{V1}.{V2}.{V3}"

    @property
    def motor_status(self) -> str:
        """
        Returns the motor status
        
        :param self:
        :return: 
        :rtype: str
        """
        # self._lock.acquire()
        resp = self._write("MST", 5)
        #self._lock.release()
        return resp
        # try:
        #     sts = format(int(resp), '012b')
        #     return sts
        # except Exception as e:
        #     return("Invalid state")
        
    @property
    def backlash(self) -> str:
        # self._lock.acquire()
        resp = self._write("V74", 5)
        if is_convertible_to_int(resp):
            resp = int(resp)
            #self._lock.release()
            value = f"{round(resp / Config.enc_2_microns, 0):.0f}"  # Converts to microns
            return value
    @backlash.setter
    def backlash(self, value: str) -> str:
        value = str(int(value) * Config.enc_2_microns)    # Converts to encoder value
        # self._lock.acquire()
        resp = self._write(f"V74={value}")
        #self._lock.release()
        
    @property
    def max_pos(self) -> str:
        # self._lock.acquire()
        resp = self._write("V71", 5)
        #self._lock.release()
        if is_convertible_to_int(resp):
            pos = int(resp) / Config.enc_2_microns
            return f"{pos:.0f}"
    @max_pos.setter
    def max_pos(self, value: str):
        pos = str(int(value) * Config.enc_2_microns)
        # self._lock.acquire()
        resp = self._write(f"V71={pos}", 5)
        #self._lock.release()
      
    @property
    def park_pos(self) -> str:  
        resp = self._write("V83", 5)
        if is_convertible_to_int(resp):
            pos = int(resp) / Config.enc_2_microns
            return f"{pos:.0f}"
        else:
            return constants.INVALID_RESPONSE
    @park_pos.setter
    def park_pos(self, value: str) -> str:      # TODO: Park position not implemented in DMX-ETH
        pos = str(int(value) * Config.enc_2_microns)
        resp = self._write(f"V83={pos}", 5)

    @property
    def max_speed(self) -> str:     # TODO: Necessário alterar algumas coisas no firmware do motor pra essa infomração ficar consistente    
        # self._lock.acquire()
        resp = self._write("HSPD", 5)
        #self._lock.release()
        return resp    
    @max_speed.setter
    def max_speed(self, value: str):
        # self._lock.acquire()
        self._write(f"V75={value}")             # Memória usada para manter o valor de HSPD na inicialização    
        resp = self._write(f"HSPD={value}")
        #self._lock.release()
         
    @property
    def normal_speed(self) -> str: # TODO: No DMX-ETH a velocidade 'normal' é a max speed. Fazer alguma lógica diferente?
        # self._lock.acquire()
        resp = self._write("HSPD", 5)
        #self._lock.release()
        return resp         
    @normal_speed.setter
    def normal_speed(self, value: str): # TODO: No DMX-ETH a velocidade 'normal' é a max speed. Fazer alguma lógica diferente?
        # self._lock.acquire()
        self._write(f"V75={value}")
        resp = self._write(f"HSPD={value}")
        #self._lock.release()   
    
    @property
    def low_speed(self) -> str:
        # self._lock.acquire()
        resp = self._write("LSPD", 5)           
        #self._lock.release()
        return resp   
    @low_speed.setter
    def low_speed(self, value: str):
        # self._lock.acquire()
        self._write(f"V76={value}")             # Memória usada para manter o valor de LSPD na inicialização
        resp = self._write(f"LSPD={value}")
        #self._lock.release()   





    def get_firmware_status(self) -> str:
        # self._lock.acquire()
        resp = self._write("SASTAT")
        #self._lock.release()
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


    def _store_to_flash(self):
        """Stores the settings to the motor flash
         Some settings will only be changed after a hard reset check table 7.15 of the DMS-ETH manual
         If '_store_to_flash' is not executed the variables saved in V51~V100 will be lost after a hard reset
         #TODO: O firmware do motor reseta os valores de max_pos, backlash, max_speed e low_speed durante o boot."""
        # self._lock.acquire()
        resp = self._write("STORE")
        #self._lock.release()


    def home(self, op: str = "command"):                             #TODO: Deixar configurar quantidade de retries?
        """Executes the INIT routine        
        Returns: 
            Device response or Error message
        Raises:
            RuntimeError if device is busy
        """    
        if op.lower() == "command":
            # self._lock.acquire()  
            if self._is_moving:                     #TODO: O `_is_moving` na verdade está verificando se alguma rotina está sendo executada (motor busy), mas essa checagem faz sentido, uma vez que não se pode iniciar uma rotina enquanto outra já está em execução.            
                raise RuntimeError('Cannot start a move while the focuser is moving')

            res = self._write("GS30", max_retries=5)    
            if res == 'OK':
                self.logger.info('[Device] home: Started homing')      #TODO: Não seria bom também executar o `initialized` para confirmar que deu tudo certo e manter `_initialized` atualizado?
                #self._lock.release()
                return res  
            else:
                alarm = self.alarm                              #TODO: Não existe um `self.alarm` só `self._alarm`
                if alarm == 1:
                    self.logger.error('[Device] home: Failed and Alarm flag is up') 

            self.logger.error('[Device] home: Failed after retries')        #TODO: Informar quantidade de retries? O motor envia alguma outra mensagem de erro com mais informações do que aconteceu?
            #self._lock.release()
        elif op.lower() == "reset": 
            res = self._write("V44=0")      # Reseta a informação de Home
            res = self._write("V15=0")      # Reseta a informação de Homing
            res = self._write("V16=0")      # Reseta a informação de Parking
        return res      
    
    def park(self):
        if self._is_moving:                     #TODO: O `_is_moving` na verdade está verificando se alguma rotina está sendo executada (motor busy), mas essa checagem faz sentido, uma vez que não se pode iniciar uma rotina enquanto outra já está em execução.            
            raise RuntimeError('Cannot start a move while the focuser is moving')
        res = self._write("GS5", max_retries=5)   
        if res == 'OK':
            self.logger.info('[Device] parking: Success')      #TODO: Não seria bom também executar o `initialized` para confirmar que deu tudo certo e manter `_initialized` atualizado?
            return res  
        else:
            alarm = self.alarm                              #TODO: Não existe um `self.alarm` só `self._alarm`
            if alarm == 1:
                self.logger.error('[Device] parking: Failed and Alarm flag is up') 

        self.logger.error('[Device] parking: Failed after retries')        #TODO: Informar quantidade de retries? O motor envia alguma outra mensagem de erro com mais informações do que aconteceu?
        #self._lock.release()
        return res     

    def move(self, position: int):                      #TODO: Deixar configurar quantidade de retries?
        """Moves device position to the given position
        Args:  
            position (int): Value in microns.
        Returns: 
            Device response or Error message
        Raises:
            RuntimeError if Invalid input or if device is busy
        """      
        # self._lock.acquire()
        pos_conv = int(round((Config.enc_2_microns * position), 0))
        if self._is_moving:                                                             #TODO: O `_is_moving` na verdade está verificando se alguma rotina está sendo executada (motor busy), mas essa checagem faz sentido, uma vez que não se pode iniciar uma rotina enquanto outra já está em execução.
            raise RuntimeError('Cannot start a move while the focuser is moving')       #TODO: Mudar para "Motor is busy" ?
        if 0 >= position or position >= self._max_step:
            raise RuntimeError('Invalid Target')
        if self._temp_comp:
            raise RuntimeError('Invalid TempComp')        
        resp = self._write(f"V20={pos_conv}", max_retries=5)                            #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores? 
        if "OK" in resp:            
            resp = self._write(f"GS29", max_retries=5)                                  #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores? 
            if "OK" in resp:
                self.logger.info(f'[Device] move={str(position)}')
                #self._lock.release()
                return True                                                 #TODO: return true ?
            else:
                alarm = self.alarm                      #TODO: Não existe um `self.alarm` só `self._alarm`
                if alarm == 1:
                    self.logger.error('[Device] Move Failed and Alarm flag is up')
                raise RuntimeError(f'[Device] Error: {resp}')
        else:
            raise RuntimeError(f'[Device] Error: {resp}') 

    def speed(self, vel: int):  
        """Sets the speed of the motor
        Args:  
            vel (int): speed value in microns/s.
        Raises:
            RuntimeError if Invalid input or if device is busy
        """      
        # self._lock.acquire()
        vel_conv = vel*Config.speed_factor
        if self._is_moving:
            raise RuntimeError('Cannot set speed while the focuser is moving')  #TODO: O `_is_moving` na verdade está verificando se alguma rotina está sendo executada (motor busy), mas essa checagem faz sentido, uma vez que não se pode iniciar uma rotina enquanto outra já está em execução.
        # if 0 > vel >= self._max_speed:
        #     raise RuntimeError('Invalid Steps') 
        if vel_conv > Config.speed_security:
            vel_conv = Config.speed_security       
        resp = self._write(f"V21={vel_conv}", max_retries=5)                    #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores? 
        if "OK" in resp: 
            self.logger.info(f'[Device] speed={str(vel)}')
            #self._lock.release()
            return True           
        else:
            raise RuntimeError(f'[device] {resp}')  
  

    def focus_in_out(self, direction: int):  
        """Sets the speed of the motor                                          #TODO: Corrigir a descrição 
        Args:  
            direction (int): 1 for IN, 0 for OUT.
        Raises:
            RuntimeError if Invalid input or if device is busy
        """      
        # self._lock.acquire()
        if self._is_moving:                                                     #TODO: O `_is_moving` na verdade está verificando se alguma rotina está sendo executada (motor busy), mas essa checagem faz sentido, uma vez que não se pode iniciar uma rotina enquanto outra já está em execução.
            raise RuntimeError('Cannot set speed while the focuser is moving')  #TODO: Corrigir mensagem do erro
        if direction != 1 and direction != 0:
            #self._lock.release()
            return False                                                        #TODO: Retornar alguma informação de erro?
        else:
            resp = self._write(f"GS2{str(direction)}", max_retries=5)           #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores? 
        if "OK" in resp: 
            if direction == 1:                
                self.logger.info(f'[Device] moving FOCUSIN')
            elif direction == 0:
                self.logger.info(f'[Device] moving FOCUSOUT')
            #self._lock.release()
            return True           
        else:
            raise RuntimeError(f'[device] {resp}')         

    def _stop(self) -> None:                     #TODO: Acho que poderia ser renomeado para `_stop` já que a ideia é só complementar o HALT
        """Complements the HALT method"""
        # # self._lock.acquire()
        self._is_moving = False
        self._stopped = True                    #TODO: Só é usado aqui, não seria a mesma coisa que `_is_moving == False` ?
        if self._timer is not None:             #TODO: Esse timer é criado mas não é usado para nada no código
            self._timer.cancel()
        self._timer = None
        # #self._lock.release()      
    
    def Halt(self) -> bool:   
        """Send command STOP and stops main program with GS0=0 subroutine"""  
        # self._lock.acquire()   
        resp_stop = self._write("V42=1", 5)     #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores?
        if resp_stop == 'OK':                 
            self.logger.info('[Device] halt')
            self._stop()
            #self._lock.release()
            return True  # Command executed successfully 
        #self._lock.release()
        return False 
    

    def read_motor_status(self):   #TODO: mover método para dentro do driver do motor DMX_ETH e fazer outro para o motor AMP
        """Issues command to read the current motor status.
        """
        try:
            resp = format(int(self.motor_status), '012b')        # TODO: Ver um jeito de converter para binário sem ser string
            motor_status = "".join(reversed(resp))                      # This is only done so that the bit order is as shown in table 7 of the manual of the motor (DMX-ETH)
            # print(motor_status)

            if(motor_status[0] == '1' or motor_status[1] == '1' or motor_status[2] == '1'):     #| Bit '0' indicates the 'moving' status
                self.signal_motor_is_moving.emit(True)                                          #| Bit '1' indicates acceleration           
            else:                                                                               #| Bit '2' indicates deceleration
                self.signal_motor_is_moving.emit(False)                                         #|  If any are set the motor is moving

            if(motor_status[4] == '1'):                 #| Bit '4' indicates the lim minus microswitch status
                self.signal_status_lim_min.emit(True)   #|
            else:                                       #|
                self.signal_status_lim_min.emit(False)  #|

            if(motor_status[5] == '1'):                 #| Bit '5' indicates the lim max microswitch status
                self.signal_status_lim_max.emit(True)   #|
            else:                                       #|
                self.signal_status_lim_max.emit(False)  #|

        except Exception as e:                  # TODO: Verificar o que tem que ser feito se não conseguir obter essa informação
            self.logger.error(f"Failed to read motor status [{str(e)}]") 
            print(e)

    def sendCommand(self, command: str) -> str:
        # # self._lock.acquire()
        resp = self._write(command)
        # #self._lock.release()
        return resp

    def _write(self, cmd, max_retries = 5):
        """Send commands to device socket.
        Args:  
            cmd (str): Command.
            max_retries (int): Number of retries if first one fails
        Returns: 
            Device response or Error message
        """
        retries = 0
        if self._connected:  
            self._lock.acquire()  
            time.sleep(0.05)         # time.sleep(0.1)  #TODO: Avaliar o motivo de precisar desse tempo morto
            while retries < max_retries:  
                try:   
                    self.motor_socket.sendall(bytes(f'{cmd}\x00', 'utf-8'))
                    response = self.motor_socket.recv(1024)
                    self._lock.release()
                    return response.decode('utf-8').replace("\x00", "")                    
                except Exception as e:
                    err = e
                retries += 1                                                               #TODO: Parece que esse retries tem que estar dentro do exception, mas talvez não faça diferença
            
        # If the program reaches this points it means that a problem occurred in sending or receiving the data
            self.logger.error(f"[Device] Error writing {cmd}: {str(err)}")
            self._lock.release()
            self.disconnect() 
            # if "WinError" in str(err):                                                     #TODO: Isso aqui não tá fazendo nada de diferente de qualquer outro erro que possa dar
            #     # If many retries were unsucessful, says the device is not connected
            #     self.disconnect()                
            return "Error communicating to the motor"  # "0"  #str(err)
        else:
            return "Not connected" #"1"
        


def is_convertible_to_int(value):
    try:
        int(value)
        return True
    except:
        return False