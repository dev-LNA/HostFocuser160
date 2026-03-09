from logging import Logger

from threading import Lock
from threading import Timer

from src.core.config import Config
from src.core.exceptions import DriverException
from src.utils.constants import constants

import socket
import time


class FocuserDriver():
    def __init__(self, logger: Logger, model: str):  
        self._lock = Lock()
        self.name: str = 'LNA Focuser'
        self.logger = logger

        self._model = model

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

        self.property_handlers = {        
                'DEVICE_IP': 'device_IP',
                'BACKLASH': 'backlash',
                'MAX_POS': 'max_pos',
                'PARK_POS': 'park_pos',
                'MAX_SPEED': 'max_speed',
                'NORMAL_SPEED': 'normal_speed',
                'LOW_SPEED': 'low_speed'
            }
        

    def acionar(self):
        print (self._connected)
        self._write("7643")

    @property
    def connected(self):
         
        res = self._connected
         
        return res
    @connected.setter 
    def connected(self, connect: bool, max_retries=5, delay=.1):
        """Connects the device and open socket connection
        Args:
            connected (bool): Sets the connected state
            max_retries (int): Number os tries if first one fail
            delay (float): Small delay, in seconds, to wait after a try
        """
         
 
        if not self.connected and connect == True:      # If not connected and connect was requested
             
            retries = 0
            while retries < max_retries and not self._connected:
                try:
                    self.motor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.motor_socket.settimeout(.6)
                    self.motor_socket.connect((Config.device_ip, 10000)) #Config.device_port))                    
                    time.sleep(delay)
                    self._connected = True
                except Exception as e:
                    self.logger.error(f'Connection attempt {retries + 1} failed: {e}')
                    retries += 1                    
                    time.sleep(delay)                         
                
            if not self._connected:
                self.logger.error(f'Failed to establish a connection after {retries} retries')
                # raise RuntimeError('Cannot Connect')

        elif connect == False:
            self.disconnect()

        if self._connected:
            self.logger.info('[Connected]')
        else:
            self.logger.info('[Disconnected]')
    
    def disconnect(self):
        """Disconnects device and close socket"""
         
        if self._connected:
            try:
                self.motor_socket.close()
                self._connected = False
            except:                                         
                raise RuntimeError('Cannot disconnect')     #TODO: Daria para fornecer mais informação do motivo de não ter dado certo?
         
        
    @property
    def temp(self):
         
        res = self._temp
         
        return res
    
    @property
    def temp_comp_available(self):
         
        res = self._temp_comp_available
         
        return res
    
    @property
    def temp_comp(self):
         
        res = self._temp_comp
         
        return res
    @temp_comp.setter
    def temp_comp(self, temp: bool):
         
        if not self._temp_comp_available and temp:
            self._temp_comp = False
        elif self._temp_comp_available:        
            self._temp_comp = temp
         

    @property
    def position(self) -> int:                      #TODO: Talvez o setter de position poderia chamar o método `move`
        """Device enconders position"""      
        try:
             
            step = int(self._write("EX", max_retries=5)) 
            
            self._position = int(round(step/Config.enc_2_microns))
            self._last_pos = self._position                             #TODO: Para que exatamente está servindo esse `_last_pos`?
             
            return self._position
        except ValueError as e:
            self.logger.error(f'[Device] Error reading position: {str(e)}')
               
        return self._last_pos                                           #TODO: Colocar esse 'return' dentro do except?
    
    @property
    def is_moving(self) -> bool:                    #TODO: Possibilitar configurar número de retries?
        """Checks if device is moving"""            #TODO: Pelo programa do motor `V46` não indica necessariamente que o motor está em movimento, mas sim que uma subrotina está sendo executada. Em alguns pontos do programa do motor é utilizado `V9` para indicar que o motor está em movimento.
         
        x = self._write("V46", max_retries=5)       #TODO: Adicionar try .. except?
        #  
        if x == "1":
            self._is_moving = True
             
            return self._is_moving                  #TODO: Desnecessário, pode ser feito só no final do método
        elif x == "0":
            self._is_moving = False 
             
            return self._is_moving                  #TODO: Desnecessário, pode ser feito só no final do método
         
        return self._is_moving

    @property
    def homing(self) -> bool:
        """Check if INIT routine is being executed"""
         
        x = self._write("V15", max_retries=5)
        if "1" in x:
            self._homing = True                     
        else:                                       
            self._homing = False
         
        return self._homing
    
    @property
    def initialized(self) -> bool:
        """Checks if initialization was previously executed"""
         
        x = self._write("V44", max_retries=5)
        if "64" in x:                               #TODO: O valor 64 é o ID desse motor específico, seriam utilizados valores diferentes para cada motor?
            self._initialized = True
        else:
            self._initialized = False
         
        return self._initialized

    @property
    def status(self) -> str:
         
        self._status = self._write("GS0")
         
        return self._status
    
    @property
    def absolute(self) -> bool:  
        #    
        res = self._absolute
         
        return res

    @property
    def max_increment(self) -> bool:
         
        res = self._max_increment
         
        return res

    @property
    def max_step(self) -> bool:
         
        res = self._max_step
         
        return res

    @property
    def step_size(self) -> bool:
         
        res = self._step_size
         
        return res
    
    @property
    def alarm(self) -> int:                                 
         
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
    def driver_state(self) -> bool:
        """
        Verifies the state of the motor driver.
        
        :param self:
        :return: True if driver is active / False if driver is not active
        :rtype: bool
        """
         
        resp = self._write("EO", 5)
        if resp == '1':
            self.logger.info('[Device] Motor Driver ON')
             
            return True
        else:
            self.logger.info('[Device] Motor Driver OFF')
             
            return False
        
    @property
    def device_IP(self) -> str:
        """
        Returns the motor IP
        
        :param self:
        :return: String with the motor IP
        :rtype: str
        """
         
        resp = self._write("IP", 5)
         
        return resp
    @device_IP.setter
    def device_IP(self, value: str):
         
        self._write(f"IP={value}", 5)
         
    
    @property
    def device_ID(self) -> str:                     # TODO: Mudar para o ID do motor mesmo, não faz sentido mostra o ID do fornecedor
        """
        Returns the motor supplier ID
        
        :param self:
        :return: String with the motor ID
        :rtype: str
        """
         
        # resp = self._write("ID", 5)
        resp = self._write("V50", 5)                    # Hardware ID stored at memory V50 on DMX-ETH  
         
        return resp
    
    @property
    def device_Firmware_Version(self) -> str:       # TODO: Mudar para o firmware do software mesmo, não faz sentido mostra a versão de firmware do fabricante
        """
        Returns the motor firmware version
        
        :param self:
        :return: String with the motor firmware version
        :rtype: str
        """
         
        V1 = self._write("V90", 5)    # Version number
        V2 = self._write("V91", 5)    # Update number
        V3 = self._write("V92", 5)    # Bug fix number
         

        return f"{V1}.{V2}.{V3}"

    @property
    def motor_status(self) -> str:
        """
        Returns the motor status
        
        :param self:
        :return: 
        :rtype: str
        """
         
        resp = self._write("MST", 5)
         
        return resp
        # try:
        #     sts = format(int(resp), '012b')
        #     return sts
        # except Exception as e:
        #     return("Invalid state")
        
    @property
    def backlash(self) -> str:
         
        resp = int(self._write("V74", 5))
         
        value = f"{round(resp / Config.enc_2_microns, 0):.0f}"  # Converts to microns
        return value
    @backlash.setter
    def backlash(self, value: str) -> str:
        value = str(int(value) * Config.enc_2_microns)    # Converts to encoder value
         
        resp = self._write(f"V74={value}")
         
        
    @property
    def max_pos(self) -> str:
         
        resp = self._write("V71", 5)
         
        pos = int(resp) / Config.enc_2_microns
        return f"{pos:.0f}"
    @max_pos.setter
    def max_pos(self, value: str):
        pos = str(int(value) * Config.enc_2_microns)
         
        resp = self._write(f"V71={pos}", 5)
         
      
    @property
    def park_pos(self) -> str:      # TODO: Implementar posição de 'park' no motor DMX-ETH
        """ Not implemented """
        return "Not implemented"
    @park_pos.setter
    def park_pos(self, value: str) -> str:      # TODO: Park position not implemented in DMX-ETH
        #  
        #  
        pass

    @property
    def max_speed(self) -> str:     # TODO: Necessário alterar algumas coisas no firmware do motor pra essa infomração ficar consistente    
         
        resp = self._write("HSPD", 5)
         
        return resp    
    @max_speed.setter
    def max_speed(self, value: str):
         
        self._write(f"V75={value}")             # Memória usada para manter o valor de HSPD na inicialização    
        resp = self._write(f"HSPD={value}")
         
         
    @property
    def normal_speed(self) -> str: # TODO: No DMX-ETH a velocidade 'normal' é a max speed. Fazer alguma lógica diferente?
         
        resp = self._write("HSPD", 5)
         
        return resp         
    @normal_speed.setter
    def normal_speed(self, value: str): # TODO: No DMX-ETH a velocidade 'normal' é a max speed. Fazer alguma lógica diferente?
         
        self._write(f"V75={value}")
        resp = self._write(f"HSPD={value}")
            
    
    @property
    def low_speed(self) -> str:
         
        resp = self._write("LSPD", 5)           
         
        return resp   
    @low_speed.setter
    def low_speed(self, value: str):
         
        self._write(f"V76={value}")             # Memória usada para manter o valor de LSPD na inicialização
        resp = self._write(f"LSPD={value}")
            





    def get_firmware_status(self) -> str:
         
        resp = self._write("SASTAT")
         
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
         
        resp = self._write("STORE")
         


    def home(self):                             #TODO: Deixar configurar quantidade de retries?
        """Executes the INIT routine        
        Returns: 
            Device response or Error message
        Raises:
            RuntimeError if device is busy
        """    
        #
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
            return False                                                        #TODO: Retornar alguma informação de erro?
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

    def _stop(self) -> None:                     #TODO: Acho que poderia ser renomeado para `_stop` já que a ideia é só complementar o HALT
        """Complements the HALT method"""
        self._is_moving = False
        self._stopped = True                    #TODO: Só é usado aqui, não seria a mesma coisa que `_is_moving == False` ?
        if self._timer is not None:             #TODO: Esse timer é criado mas não é usado para nada no código
            self._timer.cancel()
        self._timer = None   
    
    def Halt(self) -> bool:   
        """Send command STOP and stops main program with GS0=0 subroutine"""  
        resp_stop = self._write("V42=1", 5)     #TODO: Não precisa do `acquire/release` que nem foi utilizado para chamar o `_write` nos métodos anteriores?
        if resp_stop == 'OK':                 
            self.logger.info('[Device] halt')
            self._stop()
            return True  # Command executed successfully 
        return False 

    def sendCommand(self, command: str) -> str:
        resp = self._write(command)
        return resp

    def _write(self, cmd, max_retries = 5):
        """Send commands to device socket.
        Args:  
            cmd (str): Command.
            max_retries (int): Number of retries if first one fails
        Returns: 
            Device response or Error message
        """
        
        #TODO: Para o motor AMP a função de escrita precisa operar de forma diferente do motor DMX-ETH
        #       O CLP ligado ao motor AMP consegue apenas responder imediatamente com o valor salvo em um buffer interno, sendo assim
        #   é necessário que o servidor envie o comando e depois faça uma outra requisição para obter a resposta. 
        #       O fluxo do método _write para o motor AMP fica:
          
        #   1 - Servidor envia o comando
        #   2 - CLP responde com um valor padrão ("@")
        #   3 - O servidor aguarda um pequeno tempo (ms) enquanto o CLP processa o comando solicitado
        #   4 - Quando o CLP finalizar o processamento do comando a resposta é colocada no buffer de resposta do CLP
        #   5 - O servidor envia para o CLP um 'echo' do valor recebido no passo 2. Isso é um comando 'dummy' para que o CLP possa responder com o resultado do comando armazenado no buffer.
        #   6 - O CLP precisa resetar o buffer para o valor padrão para aceitar um novo comando.
        retries = 0
        if self._connected:  
            self._lock.acquire()  
            time.sleep(0.2)         
            while retries < max_retries:  
                try:   
                    self.motor_socket.sendall(bytes(f'{cmd}\x00', 'ascii'))
                    response = self.motor_socket.recv(1024)
                    self._lock.release()
                    print(response)
                    return response.decode('utf-8').replace("\x00", "")                    
                except Exception as e:
                    err = e
                retries += 1                                                               #TODO: Parece que esse retries tem que estar dentro do exception, mas talvez não faça diferença
            self._connected = False
            self.logger.error(f"[Device] Error writing {cmd}: {str(err)}")
            self._lock.release()
            
            if "WinError" in str(err):                                                     #TODO: Isso aqui não tá fazendo nada de diferente de qualquer outro erro que possa dar
                # If many retries were unsucessful, says the device is not connected
                self._connected = False                                                         
            # print(f"Error writing ETH: {cmd}: {str(err)}")
            return str(err)
        else:
            return "Not Connected"
