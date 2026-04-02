from src.interface.modbus_server import ModbusServer
# from pyModbusTCP.server import DataBank
from src.interface.modbus_data_bank import MB_DataBank

from logging import Logger
from threading import Lock, Timer, Thread

from src.core.config import Config
from src.core.exceptions import DriverException
from src.utils.constants import constants
from src.utils.modbus_regs import RegsInfo, RegType, coils_regs, dig_inputs_regs

import time


class FocuserDriver():
    def __init__(self, logger: Logger, model: str):
        self._lock = Lock()
        self.name: str = 'LNA Focuser'
        self.logger = logger

        self._model = model

        self.mb_server: ModbusServer = None

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
        
        # self.dataBank_shadow = MB_DataBank(coils_size=619, coils_default_value=False,       #|      554
        #                                 d_inputs_size=1295, d_inputs_default_value=False,   #|  Shadow value for the modbus data.
        #                                 h_regs_size=0, h_regs_default_value=0,              #|  Also used as initial values for the server.
        #                                 i_regs_size=0, i_regs_default_value=0)              #|
        
    def acionar(self):
        print (self._connected)
        # self._write(192, dig_inputs_regs.TX_IP_A)
        # self._write(168, dig_inputs_regs.TX_IP_B)
        # self._write(60, dig_inputs_regs.TX_IP_C)
        # self._write(39, dig_inputs_regs.TX_IP_D)
        # self._write(192, dig_inputs_regs.TX_CGT_A)
        # self._write(168, dig_inputs_regs.TX_CGT_B)
        # self._write(60, dig_inputs_regs.TX_CGT_C)
        # self._write(1, dig_inputs_regs.TX_CGT_D)
        # self._write(255, dig_inputs_regs.TX_CMK_A)
        # self._write(255, dig_inputs_regs.TX_CMK_B)
        # self._write(255, dig_inputs_regs.TX_CMK_C)
        # self._write(0, dig_inputs_regs.TX_CMK_D)
        # self._write(254863, dig_inputs_regs.TX_V20)
        # self._write(-1548, dig_inputs_regs.TX_V78)
        # self._write(True, dig_inputs_regs.TX_MOF)
        # self._write(True, dig_inputs_regs.TX_MON)
        # self._write(9888754, dig_inputs_regs.TX_SASTAT)
        # self._write(True, dig_inputs_regs.HANDSHAKE)
        # time.sleep(2)
        # self._write(False, dig_inputs_regs.HANDSHAKE)
        for reg in coils_regs:
            print("-------------------------------")
            print(f"Registrador {reg.TAG}:")
            if reg.SIZE > 1:
                print(f"{self.mb_server._conv_reg_to_value(reg, self.mb_server.data_bank)}")
                
                bit_list = self.mb_server.data_bank.get_coils(reg.ADDRESS, reg.SIZE)
                # conv: list = []
                # for cont in range(0,4):
                #     bit_list = self.mb_server.data_bank.get_coils(reg.ADDRESS+8*cont, 8)
                #     bit_list.reverse()
                #     for item in bit_list:      
                #         if item == True:
                #             conv.append(1)
                #         else:
                #             conv.append(0)

                print(bit_list)
            else:
                print(f"{self.mb_server.data_bank.get_coils(reg.ADDRESS, reg.SIZE)}")


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
                dataBank_config = MB_DataBank(coils_size=618, coils_default_value=False,        #|      
                                d_inputs_size=1391, d_inputs_default_value=False,               #|  Config value for the modbus data bank.
                                h_regs_size=0, h_regs_default_value=0,                          #|  
                                i_regs_size=0, i_regs_default_value=0)                          #|
                self.mb_server = ModbusServer(host='0.0.0.0', port=5005 ,no_block=True, data_bank=dataBank_config)
                self.mb_server.start()
                self.mb_server.signal_stop.connect(self._stop_server)
                self.mb_run_thread = Thread(target=self.mb_server.run)
                self.mb_run_thread.start()
                self.mb_server.running = True
                _con = True
                print("Modbus server started")
                self.logger.info("Modbus server started")
            except Exception as e:
                print(f"Error starting modbus server: {e}")
                self.logger.error(f'Failed to start modbus server after {retries} retries.')
                self.logger.error(f'Error code: {e}')


    @property
    def connected(self):
        return self._connected
    
    @connected.setter
    def connected(self, connect: bool, max_retries=5, delay=.1):
        """Starts the modbus server

        Args:
            connect (bool): Sets the connected state
            max_retries (int, optional): Max attempts to start the modbus server. Defaults to 5.
            delay (float, optional): Delay between attempts. Defaults to .1.
        """
        if self.mb_server.running:
            self._connected = connect
        else:
            self._connected = False

    def _stop_server(self):
        if self.mb_server:
            self.mb_server.stop_server = True
            self.mb_run_thread.join()
            self.mb_server.stop()
            self.mb_server = None
            print("Server closed")

    def disconnect(self):
        """Disconnects device and close socket"""
        if self.mb_server:
            if self.mb_server.running:                  # In this the disconnection must check if the modbus server is running
                try:
                    self._stop_server()
                    self._connected = False
                except Exception as e:
                    self.logger.error(f"Error during modbus server disconnection -> {e}")
        
    def ping(self):
        if self.mb_server is None:                  #   If the server was not instantiated
            self.running = True                     #   Instantiates and starts the server (needed to read handshake)
            
        if self.running:                         #   Verifies if the modbus server was correctly connected
            if self.mb_server.handshake:                # If handshake was made
                return True                             # Informs that the motor is reachable
        
        return False                                #   Returns False otherwise
        

    @property
    def temp(self):
        ...
    
    @property
    def temp_comp_available(self):
        ...
    
    @property
    def temp_comp(self):
        ...
    @temp_comp.setter
    def temp_comp(self, temp: bool):
        ...
         

    @property
    def position(self) -> int:                      #TODO: Talvez o setter de position poderia chamar o método `move`
        """Device enconders position"""      
        return 0                                      #TODO: Colocar esse 'return' dentro do except?
    
    @property
    def is_moving(self) -> bool:                    #TODO: Possibilitar configurar número de retries?
        """Checks if device is moving"""            #TODO: Pelo programa do motor `V46` não indica necessariamente que o motor está em movimento, mas sim que uma subrotina está sendo executada. Em alguns pontos do programa do motor é utilizado `V9` para indicar que o motor está em movimento.
        return False

    @property
    def homing(self) -> bool:
        """Check if INIT routine is being executed"""
        return False
    
    @property
    def parking(self) -> bool:
        return False
    @property
    def initialized(self) -> bool:
        """Checks if initialization was previously executed"""
        return False

    @property
    def status(self) -> str:
        return "idle"
    
    @property
    def absolute(self) -> bool:  
        return False

    @property
    def max_increment(self) -> bool:
        return False

    @property
    def max_step(self) -> bool:
        return False

    @property
    def step_size(self) -> bool:
        return False
    
    @property
    def alarm(self) -> int:                                 
        return 0

    @property
    def driver_state(self) -> bool:
        """
        Verifies the state of the motor driver.
        
        :param self:
        :return: True if driver is active / False if driver is not active
        :rtype: bool
        """
        return False
        
    @property
    def device_IP(self) -> str:
        """
        Returns the motor IP
        
        :param self:
        :return: String with the motor IP
        :rtype: str
        """
        return "localhost"
    @device_IP.setter
    def device_IP(self, value: str):
        ...
         
    
    @property
    def device_ID(self) -> str:                     # TODO: Mudar para o ID do motor mesmo, não faz sentido mostra o ID do fornecedor
        """
        Returns the motor supplier ID
        
        :param self:
        :return: String with the motor ID
        :rtype: str
        """
        return "modbus"
    
    @property
    def device_Firmware_Version(self) -> str:       # TODO: Mudar para o firmware do software mesmo, não faz sentido mostra a versão de firmware do fabricante
        """
        Returns the motor firmware version
        
        :param self:
        :return: String with the motor firmware version
        :rtype: str
        """
        return "test"

    @property
    def motor_status(self) -> str:
        """
        Returns the motor status
        
        :param self:
        :return: 
        :rtype: str
        """
        return "0"
        
    @property
    def backlash(self) -> str:
        return "0"
    @backlash.setter
    def backlash(self, value: str) -> str:
        return "0"
         
        
    @property
    def max_pos(self) -> str:
        return "0"
    @max_pos.setter
    def max_pos(self, value: str):
        return "0"
         
      
    @property
    def park_pos(self) -> str:      # TODO: Implementar posição de 'park' no motor DMX-ETH
        return "0"
    @park_pos.setter
    def park_pos(self, value: str) -> str:      # TODO: Park position not implemented in DMX-ETH
        return "0"

    @property
    def max_speed(self) -> str:     # TODO: Necessário alterar algumas coisas no firmware do motor pra essa infomração ficar consistente    
        return "0"
    @max_speed.setter
    def max_speed(self, value: str):
        return "0"
         
         
    @property
    def normal_speed(self) -> str: # TODO: No DMX-ETH a velocidade 'normal' é a max speed. Fazer alguma lógica diferente?
        return "0"      
    @normal_speed.setter
    def normal_speed(self, value: str): # TODO: No DMX-ETH a velocidade 'normal' é a max speed. Fazer alguma lógica diferente?
        return "0"
            
    
    @property
    def low_speed(self) -> str:
        return "0"
    @low_speed.setter
    def low_speed(self, value: str):
        return "0"
            

    # def _conv_num_bits(self, num: int, size:int) -> list:
    #     """Converts an int to a bitlist for transmition considering
    #     two's complement for negativa numbers.

    #     Args:
    #         num (int): Number to be converted
    #         size (int): Number of output bits (8, 16, 32, 64)

    #     Returns:
    #         list: List with the 
    #     """
    #     print("---------------")
    #     # print(f"num = {num} ----> {unsigned_value}")
    #     num_mod = num                                               # Just to keep the original number

    #     if num < 0:                                                 # If the number is negative gets the absolute value and subtracts 1
    #         num_mod = abs(num) 
    #         num_mod-=1

    #     bits = [(num_mod >> i) & 1 for i in range(0, size, 1)]      # Generates a list with each bit in the correct endianess (lsb to msb)
    #     if num < 0:                                                 # If the number is negative
    #         for idx, b in enumerate(bits):                              # Loop to invert the bits and 
    #             # bits[idx] = not b
    #             if b: bits[idx] = 0
    #             else: bits[idx] = 1
        
    #     return bits

    def get_firmware_status(self) -> str:
        return "OK"


    def _store_to_flash(self):
        """Stores the settings to the motor flash
         Some settings will only be changed after a hard reset check table 7.15 of the DMS-ETH manual
         If '_store_to_flash' is not executed the variables saved in V51~V100 will be lost after a hard reset
         #TODO: O firmware do motor reseta os valores de max_pos, backlash, max_speed e low_speed durante o boot."""
         
        ...
         


    def home(self):                             #TODO: Deixar configurar quantidade de retries?
        """Executes the INIT routine        
        Returns: 
            Device response or Error message
        Raises:
            RuntimeError if device is busy
        """    
        ...

    def move(self, position: int):                      #TODO: Deixar configurar quantidade de retries?
        """Moves device position to the given position
        Args:  
            position (int): Value in microns.
        Returns: 
            Device response or Error message
        Raises:
            RuntimeError if Invalid input or if device is busy
        """      
        ...

    def speed(self, vel: int):  
        """Sets the speed of the motor
        Args:  
            vel (int): speed value in microns/s.
        Raises:
            RuntimeError if Invalid input or if device is busy
        """      
        ...
  

    def focus_in_out(self, direction: int):  
        """Sets the speed of the motor                                          #TODO: Corrigir a descrição 
        Args:  
            direction (int): 1 for IN, 0 for OUT.
        Raises:
            RuntimeError if Invalid input or if device is busy
        """      
        ...       

    def _stop(self) -> None:                     #TODO: Acho que poderia ser renomeado para `_stop` já que a ideia é só complementar o HALT
        """Complements the HALT method"""
        ...
    
    def Halt(self) -> bool:   
        """Send command STOP and stops main program with GS0=0 subroutine"""  
        ...

    def sendCommand(self, command: str) -> str:
        return "OK"


    def _write(self, value: int | bool, reg: RegsInfo):
        
        # When the register size is 1 the value must be 0, 1 or boolean
        if (reg.SIZE==1 and not ( ( (value==0) or (value==1) or type(value) is bool ) )):
            raise ValueError(f"Cannot write {value} to {reg.TYPE.name}:{reg.ADDRESS}. This Register supports only {reg.SIZE} bit(s).")
        
        # When a boolean was sent to a register that has more bits
        if ( type(value) is bool ) and ( reg.SIZE != 1):
            raise ValueError(f"Cannot write a boolean to {reg.TYPE.name}:{reg.ADDRESS}. This Register has {reg.SIZE} bits")

        # if reg.TYPE is RegType.COIL:
        #     if (type(value) is bool) or (reg.SIZE==1 and ( (value==0) or (value==1) ) ):                # If the value is a bool or the register has only one bit than no conversion is needed
        #         self.mb_server.data_bank.set_coils(reg.ADDRESS, [value])                 
        #     else:                                                                                       #| If the register has multiple bits than the value must be converted
        #         num_bits = self._conv_num_bits(value, reg.SIZE)                                         #| The conversion already considers negative values as two's complement
        #         self.mb_server.data_bank.set_coils(reg.ADDRESS, num_bits)

        # elif reg.TYPE is RegType.DISCRETE_INPUT:
        #     if (type(value) is bool) or (reg.SIZE==1 and ( (value==0) or (value==1) ) ):                # If the value is a bool or the register has only one bit than no conversion is needed
        #         self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS, [value])
        #     else:                                                                                       #| If the register has multiple bits than the value must be converted
        #         num_bits = self._conv_num_bits(value, reg.SIZE)                                         #| The conversion already considers negative values as two's complement
        #         if reg.SIZE == 8:                                                                       
        #             self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits)          # If the register is only 8 bits the value is saved directly to the register
        #         else:                                                                                   
        #             self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits[16:])     #|  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address   
        #             self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS+16, num_bits[:16])  #| and the lower bits must be saved to next 16 bits

        if reg.TYPE is RegType.DISCRETE_INPUT:
            if (type(value) is bool) or (reg.SIZE==1 and ( (value==0) or (value==1) ) ):                # If the value is a bool or the register has only one bit than no conversion is needed
                self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS, [value])
            else:                                                                                       #| If the register has multiple bits than the value must be converted
                num_bits = self.mb_server._conv_num_bits(value, reg.SIZE)                                         #| The conversion already considers negative values as two's complement
                if reg.SIZE == 8:                                                                       
                    self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits)          # If the register is only 8 bits the value is saved directly to the register
                else:                                                                                   
                    self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits[16:])     #|  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address   
                    self.mb_server.data_bank.set_discrete_inputs(reg.ADDRESS+16, num_bits[:16])  #| and the lower bits must be saved to next 16 bits

            self.mb_server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WAIT.ADDRESS, [False])  # Informs CLP that there is a valid data ready for readi
            self.mb_server.wait_confirmation(reg)


    # def _write(self, cmd, max_retries = 10):
    #     """Send commands to device socket.
    #     Args:  
    #         cmd (str): Command.
    #         max_retries (int): Number of retries if first one fails
    #     Returns: 
    #         Device response or Error message
    #     """
        
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
        ...





def is_convertible_to_int(value):
    try:
        int(value)
        return True
    except:
        return False