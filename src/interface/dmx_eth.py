from logging import Logger

from threading import Lock
from threading import Timer

from src.core.config import Config

import socket
import time

class FocuserDriver():
    def __init__(self, logger: Logger):  
        self._lock = Lock()
        self.name: str = 'LNA Focuser'
        self.logger = logger

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
        self._at_home = False
        self._initialized = False
        self._alarm = 0

        self._timeout = 1

        self._timer: Timer = None
        self._interval: float = .15

    @property
    def connected(self):
        self._lock.acquire()
        res = self._connected
        self._lock.release()
        return res
    @connected.setter 
    def connected(self, connected: bool, max_retries=5, delay=.1):
        """Connects the device and open socket connection
        Args:
            connected (bool): Sets the connected state
            max_retries (int): Number os tries if first one fail
            delay (float): Small delay, in seconds, to wait after a try
        """
        self._lock.acquire()
        self._connected = connected     
        if connected:
            self._lock.release()
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
                        self._lock.acquire()
                        self._connected = False
                        self._lock.release()
                
            if not connected_successfully:          #TODO: Isso aqui não pode ficar dentro da checagem de "if retries >= max_retries-1" acima?
                self._lock.acquire()
                self._connected = False
                self._lock.release()
                self.logger.error('Failed to establish a connection after retries')
                raise RuntimeError('Cannot Connect')

        else:
            self._connected = False     #TODO: A modificação de `_connected` para false não deveria ser feita somente na função "disconnect" no caso de ter dado certo a desconexão? Senão na hora que for para a função "disconnect" não vai passar pelo `if` e a função não vai fazer nada. Outra opção é só esse método não aceitar "false" como entrada.
            self._lock.release()
            self.disconnect()

        if self._connected:
            self.logger.info('[Connected]')
        else:
            self.logger.info('[Disconnected]')
    
    def disconnect(self):
        """Disconnects device and close socket"""
        self._lock.acquire()
        if self._connected:
            try:
                self.motor_socket.close()
                self._connected = False
            except:
                raise RuntimeError('Cannot disconnect')     #TODO: Daria para fornecer mais informação do motivo de não ter dado certo?
        self._lock.release()
        
    @property
    def temp(self):
        self._lock.acquire()
        res = self._temp
        self._lock.release()
        return res
    
    @property
    def temp_comp_available(self):
        self._lock.acquire()
        res = self._temp_comp_available
        self._lock.release()
        return res
    
    @property
    def temp_comp(self):
        self._lock.acquire()
        res = self._temp_comp
        self._lock.release()
        return res
    @temp_comp.setter
    def temp_comp(self, temp: bool):
        self._lock.acquire()
        if not self._temp_comp_available and temp:
            self._temp_comp = False
        elif self._temp_comp_available:        
            self._temp_comp = temp
        self._lock.release()

    @property
    def position(self) -> int:                      #TODO: Talvez o setter de position poderia chamar o método `move`
        """Device enconders position"""      
        try:
            self._lock.acquire()
            step = int(self._write("EX", max_retries=5)) 
            
            self._position = int(round(step/Config.enc_2_microns))
            self._last_pos = self._position                             #TODO: Para que exatamente está servindo esse `_last_pos`?
            self._lock.release()
            return self._position
        except ValueError as e:
            self.logger.error(f'[Device] Error reading position: {str(e)}')
            self._lock.release()  
        return self._last_pos                                           #TODO: Colocar esse 'return' dentro do except?
    
    @property
    def is_moving(self) -> bool:                    #TODO: Possibilitar configurar número de retries?
        """Checks if device is moving"""            #TODO: Pelo programa do motor `V46` não indica necessariamente que o motor está em movimento, mas sim que uma subrotina está sendo executada. Em alguns pontos do programa do motor é utilizado `V9` para indicar que o motor está em movimento.
        self._lock.acquire()
        x = self._write("V46", max_retries=5)       #TODO: Adicionar try .. except?
        if x == "1":
            self._is_moving = True
            self._lock.release()
            return self._is_moving                  #TODO: Desnecessário, pode ser feito só no final do método
        elif x == "0":
            self._is_moving = False 
            self._lock.release()
            return self._is_moving                  #TODO: Desnecessário, pode ser feito só no final do método
        self._lock.release()
        return self._is_moving

    @property
    def homing(self) -> bool:
        """Check if INIT routine is being executed"""
        self._lock.acquire()
        x = self._write("V44", max_retries=5)
        if "0" in x:
            self._homing = True                     #TODO: Pelo programa do motor parece que `V44 == 0` so indicaria que o homing não foi feito, mas não necessariamente significa que está sendo executado
        else:                                       
            self._homing = False
        self._lock.release()
        return self._homing
    
    @property
    def initialized(self) -> bool:
        """Checks if initialization was previously executed"""
        self._lock.acquire()
        x = self._write("V44", max_retries=5)
        if "64" in x:                               #TODO: O valor 64 é o ID desse motor específico, seriam utilizados valores diferentes para cada motor?
            self._initialized = True
        else:
            self._initialized = False
        self._lock.release()
        return self._initialized

    @property
    def get_status(self) -> str:
        self._lock.acquire()
        self._status = self._write("GS0")
        self._lock.release()
        return self._status
    
    @property
    def absolute(self) -> bool:  
        self._lock.acquire()      
        res = self._absolute
        self._lock.release()
        return res

    @property
    def max_increment(self) -> bool:
        self._lock.acquire()
        res = self._max_increment
        self._lock.release()
        return res

    @property
    def max_step(self) -> bool:
        self._lock.acquire()
        res = self._max_step
        self._lock.release()
        return res

    @property
    def step_size(self) -> bool:
        self._lock.acquire()
        res = self._step_size
        self._lock.release()
        return res
    
    @property
    def alarm(self) -> int:                                 #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores?    
        res = self._write("ALM", max_retries=5)
        try:                                                #TODO: O que ativaria uma exceção dentro desse try?
            self._alarm = int(res)
            if self._alarm == '1':
                self.logger.info('[Device] Temperature Alarm ON')   #TODO: Só a temperatura que aciona esse alarme?
        except Exception as e: 
            self._alarm = 0
            self.logger.error(f'[Device] Alarm Error {str(e)}')
        
        return self._alarm

    @property
    def get_driver_state(self) -> bool:
        """
        Verifies the state of the motor driver.
        
        :param self:
        :return: True if driver is active / False if driver is not active
        :rtype: bool
        """
        self._lock.acquire()
        resp = self._write("EO", 5)
        self._lock.release()
        if resp == '1':
            self.logger.info('[Device] Motor Driver ON')
            return True
        else:
            self.logger.info('[Device] Motor Driver OFF')
            return False



    def home(self):                             #TODO: Deixar configurar quantidade de retries?
        """Executes the INIT routine        
        Returns: 
            Device response or Error message
        Raises:
            RuntimeError if device is busy
        """      
        if self._is_moving:                     #TODO: O `_is_moving` na verdade está verificando se alguma rotina está sendo executada (motor busy), mas essa checagem faz sentido, uma vez que não se pode iniciar uma rotina enquanto outra já está em execução.            
            raise RuntimeError('Cannot start a move while the focuser is moving')

        res = self._write("GS30", max_retries=5)     #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores? 
        if res == 'OK':
            self.logger.info('[Device] home: Success')      #TODO: Não seria bom também executar o `initialized` para confirmar que deu tudo certo e manter `_initialized` atualizado?
            return res  
        else:
            alarm = self.alarm                              #TODO: Não existe um `self.alarm` só `self._alarm`
            if alarm == 1:
                self.logger.error('[Device] home: Failed and Alarm flag is up') 

        self.logger.error('[Device] home: Failed after retries')        #TODO: Informar quantidade de retries? O motor envia alguma outra mensagem de erro com mais informações do que aconteceu?
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
                return                                                  #TODO: return true ?
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
        if self._is_moving:                                                     #TODO: O `_is_moving` na verdade está verificando se alguma rotina está sendo executada (motor busy), mas essa checagem faz sentido, uma vez que não se pode iniciar uma rotina enquanto outra já está em execução.
            raise RuntimeError('Cannot set speed while the focuser is moving')  #TODO: Corrigir mensagem do erro
        if direction != 1 and direction != 0:
            return                                                              #TODO: Retornar alguma informação de erro?
        else:
            resp = self._write(f"GS2{str(direction)}", max_retries=5)           #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores? 
        if "OK" in resp: 
            if direction == 1:                
                self.logger.info(f'[Device] moving FOCUSIN')
            elif direction == 0:
                self.logger.info(f'[Device] moving FOCUSOUT')
            return True           
        else:
            raise RuntimeError(f'[device] {resp}')         

    def stop(self) -> None:                     #TODO: Acho que poderia ser renomeado para `_stop` já que a ideia é só complementar o HALT
        """Complements the HALT method"""
        self._lock.acquire()
        self._is_moving = False
        self._stopped = True                    #TODO: Só é usado aqui, não seria a mesma coisa que `_is_moving == False` ?
        if self._timer is not None:             #TODO: Esse timer é criado mas não é usado para nada no código
            self._timer.cancel()
        self._timer = None
        self._lock.release()      
    
    def Halt(self) -> bool:   
        """Send command STOP and stops main program with GS0=0 subroutine"""     
        resp_stop = self._write("V42=1", 5)     #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores?
        if resp_stop == 'OK':                 
            self.logger.info('[Device] halt')
            self.stop()
            return True  # Command executed successfully 
        return False 



    
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
            time.sleep(.2)            
            while retries < max_retries:  
                try:   
                    self.motor_socket.sendall(bytes(f'{cmd}\x00', 'utf-8'))
                    response = self.motor_socket.recv(1024)
                    return response.decode('utf-8').replace("\x00", "")                    
                except Exception as e:
                    err = e
                retries += 1                                                               #TODO: Parece que esse retries tem que estar dentro do exception, mas talvez não faça diferença
            self._connected = False
            self.logger.error(f"[Device] Error writing {cmd}: {str(err)}")
            if "WinError" in str(err):                                                     #TODO: Isso aqui não tá fazendo nada de diferente de qualquer outro erro que possa dar
                # If many retries were unsucessful, says the device is not connected
                self._connected = False                                                          
            # print(f"Error writing ETH: {cmd}: {str(err)}")
            return str(err)
        else:
            return "Not Connected"