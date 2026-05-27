from pyModbusTCP.server import ModbusServer as mbServer
from pyModbusTCP.server import DataBank
from src.core.config import Config
from src.utils.modbus_regs import dig_inputs_regs, coils_regs, RegsInfo, RegType, CLP_Owned, TwosComplementReg, param_vars, DB_size
from src.utils.constants import CommandTimeout
from src.interface.modbus_data_bank import MB_DataBank


from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtWidgets import QWidget

import time
from threading import Timer, Lock
from datetime import datetime

class TimeoutCheck(QObject):
    """Handshake Timeout verification"""

    _timeout_signal = pyqtSignal(bool)
    def __init__(self, timeout: int = 5):
        super(QObject, self).__init__()
        self._timeout_limit = timeout                           # Timeout limit
        self.timer: int = 0                                     # Current timer

        self.status = False                                     # Timeout status (True -> timeout occured)

    def reset(self):
        """Resets timeout timer"""
        self.timer = time.time()

    def check_timeout(self) -> bool:
        """Checks if a timeout occured

        Returns:
            bool:   True -> Timeout
                    False -> No timeout
        """ 
        # The timeout occurs when this function is not called in less than '_timeout_limit'
        if (time.time() - self.timer) < self._timeout_limit:
            self.status = False
            self._timeout_signal.emit(False)
        else:
            self.status = True
            self._timeout_signal.emit(True)

        return self.status 
        

class IAGModbusServer(mbServer):
    """A Qwidget that operates as modbus server

    Args:
        QWidget (_type_): Being a QWidget the ModbusServer is capable to emit signals

        host (_str_): hostname or IPv4/IPv6 address server address (default is 'localhost')
        port (_int_): TCP port number (default is 5005)
        no_block (_bool_): no block mode, i.e. start() will return (default is False)
        ipv6 (_bool_): use ipv6 stack (default is False)
        device_id (_DeviceIdentification_): instance of DeviceIdentification class for read device identification request (optional)
        coils_size (_int_): Number of coils
        d_inputs_size (_int_): Number of digital inputs
        h_regs_size (_int_): Number of holding registers
        i_regs_size (_int_): Number of input registers
    """

    _reading = False
    _writting = False
    RW_lock = Lock()
    def __init__(self, host: str='0.0.0.0', port: int=5005, no_block: bool=False, ipv6: bool=False, device_id=None,
                 data_bank: MB_DataBank | None = None,):
        super(IAGModbusServer, self).__init__(host=host, port=port, no_block=no_block, ipv6=ipv6, data_bank=data_bank, device_id=device_id)

            # self.dataBank = DataBank(coils_size=1127, coils_default_value=False, d_inputs_size=0, h_regs_size=0, i_regs_size=0)
        # dataBank = DataBank(coils_size=coils_size, coils_default_value=False,
        #                     d_inputs_size=d_inputs_size, d_inputs_default_value=False,
        #                     h_regs_size=h_regs_size, h_regs_default_value=0,
        #                     i_regs_size=i_regs_size, i_regs_default_value=0)
        
        #self.server = mbServer(host=host, port=port, no_block=no_block, ipv6=ipv6, data_bank=data_bank, device_id=device_id)          # If port <=1024 needs root access on linux

        # self.host = host
        # self.port = port

        self.db_shadow = DataBank(coils_size=data_bank.coils_size, coils_default_value=data_bank.coils_default_value,               #|      
                                d_inputs_size=data_bank.d_inputs_size, d_inputs_default_value=data_bank.d_inputs_default_value,     #|  Config value for the modbus data bank.
                                h_regs_size=data_bank.h_regs_size, h_regs_default_value=data_bank.h_regs_default_value,             #|  
                                i_regs_size=data_bank.i_regs_size, i_regs_default_value=data_bank.i_regs_default_value)  

        self.stop_server = False
        self.handshake = False
        self.running = False

        self.timeout = TimeoutCheck()

        self.handshake_timer = time.time()

        self.command_timeout = CommandTimeout(
            command='',
            timer=Timer(Config.write_timeout, self._handle_command_timeout)
        )
            
        self._changed_coils: set[tuple[RegsInfo, int | bool]] = set()   # A set to keep track of the coils that had their value changed


    @property
    def reading(self) -> bool:
        """Returns if the ModbusServer is currently reading data from the CLP
        Also locks the writting process while the ModbusServer is reading data to avoid writting data that is being read by the CLP"""
        return self._reading
    @reading.setter
    def reading(self, value: bool):


        if value == False:
            self._reading = False
            self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [False])  # Informs the CLP that the Driver is not reading data from the modbus coils
            
            # If the reading process is being set to false it is important to check if the lock
            # was acquired by the reading process or by the writting process, if the lock was acquired by the reading process it must be released to
            # allow the writting process to write data to the CLP
            if self.RW_lock.locked() and not self.writting:
                self.RW_lock.release()

        elif value == True:
            
            # Cannot start reading if the writting process is locked to avoid reading data that is being writted to the CLP
            if self.RW_lock.locked():
                # guarantees that _reading is set to False if the writting process is locked
                self._reading = False
                self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [False])  # Informs the CLP that the Driver is not reading data from the mod
                return            

            else:
                # # If the CLP writting process is not happening the reading mode can be set
                # # waits up to 2 seconds the CLP writting
                # t = time.time()
                # t_over = False
                # while self.CLP_writting:
                #     if time.time() - t > 2:
                #         t_over = True

                # if t_over == False:
                #     # Sets server reading mode
                self._reading = True
                self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [True])   # Informs the CLP that the Driver is reading some data from the modbus coils
                self.RW_lock.acquire()

            
    @property
    def writting(self) -> bool:
        """Returns if the ModbusServer is currently writting data to the CLP
        Also locks the reading process while the ModbusServer is writting data to avoid reading data that is being writted to the CLP"""
        return self._writting
    @writting.setter
    def writting(self, value: bool):


        if value == False:
            self._writting = False
            self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])  # Informs the CLP that the Driver is not writting data to the modbus discrete inputs
            
            # If the writting process is being set to false it is important to check if the lock
            # was acquired by the writting process or by the reading process, if the lock was acquired by the writting process it must be released to
            # allow the reading process to read data from the CLP
            if self.RW_lock.locked() and not self.reading:
                self.RW_lock.release()

        elif value == True:
            
            # Cannot start reading if the writting process is locked to avoid reading data that is being writted to the CLP
            if self.RW_lock.locked():
                # guarantees that _writting is set to False if the writting process is locked
                self._writting = False
                self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])  # Informs the CLP that the Driver is not writting data to the modbus discrete inputs
                return            

            else:
                # If the CLP reading process is not happening the weritting mode can be set
                # waits up to 2 seconds the CLP reading
                # t = time.time()
                # t_over = False
                # while self.CLP_reading:
                #     if time.time() - t > 2:
                #         t_over = True
                # if t_over == False:
                    # sets server writting mode

                self._writting = True
                self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [True])   # Informs the CLP that the Driver is writting some data to the modbus discrete inputs
                self.RW_lock.acquire()

    @property
    def CLP_writting(self) -> bool:
        """Returns if the CLP is writting data to the ModbusServer by checking 
        the status of the 'RX_WRITTING' coil register that is set by the CLP when it is writting data"""
        return self.data_bank.get_coils(coils_regs.RX_WRITTING.ADDRESS, coils_regs.RX_WRITTING.SIZE)[0]
    
    @property
    def CLP_reading(self) -> bool:
        """Returns if the CLP is reading data from the ModbusServer by checking 
        the status of the 'RX_READING' coil register that is set by the CLP when it is reading data"""
        return self.data_bank.get_coils(coils_regs.RX_READING.ADDRESS, coils_regs.RX_READING.SIZE)[0]

    @property
    def CLP_OK(self) -> bool:
        """Returns the status of the CLP OK coil register"""
        return self.data_bank.get_coils(coils_regs.OK.ADDRESS, coils_regs.OK.SIZE)[0]
        # return self.db_shadow.get_coils(coils_regs.OK.ADDRESS, coils_regs.OK.SIZE)[0]

    @property
    def CLP_NOK(self) -> bool:
        """Returns the status of the CLP NOK coil register"""
        return self.data_bank.get_coils(coils_regs.NOK.ADDRESS, coils_regs.NOK.SIZE)[0]
        # return self.db_shadow.get_coils(coils_regs.NOK.ADDRESS, coils_regs.NOK.SIZE)[0]

    def run(self):
        """Loop that operates the modbus server"""
        while not self.stop_server:
            time.sleep(.05) # 0.1
             
            # Checks if a HANDSHAKE was received and if a timeout occured
            self._check_handshake()


            # To be operational the handshake must be valid
            if self.handshake:
                
                # As variáveis que vem do CLP devem ser sempre lidas e rebatidas para o CLP, porém, elas somente
                # serão salvas no data bank principal quando o CLP enviar o sinal de que parou de escrever
                # O data bank "db_shadow" é o que possui as informações que são utilizadas pelo python
                # O data bank "data_bank" e o que possui as informações sendo recebidas pelo CLP

                # If the CLP is not writting, the Driver will check if there is any change in the coil registers and 
                # save the updated value in the shadow register, then it will check if any of the changed coils are 
                # owned by the CLP and if so it will mirror the value to the CLP response register to confirm that the 
                # information was received by the python
                # if not self.data_bank.get_coils(coils_regs.RX_WRITTING.ADDRESS, 1)[0]: 
                # if not self.CLP_writting:
                self._mirror_clp_owned_coils()

                if not self.CLP_writting:
                    if self._start_reading_data():
                        for reg in coils_regs:
                            if not self._compare_regs(reg):
                                current_reg_val = self._conv_reg_to_value(reg, self.data_bank)
                                self.db_shadow.set_coils(reg.ADDRESS, self._conv_num_bits(current_reg_val, reg.SIZE))
                    self._stop_reading_data()
                            
                        

                # if self._start_reading_data():          # Informa o CLP que o python está lendo dos registradores
                #     for reg in coils_regs:
                #         if not self._compare_regs(reg):     # If false means that the register value was changed
                #             self._check_clp_owned_coils(reg)               # Checks if any clp owned coil was changed 

                #     # self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [False])
                #     self._stop_reading_data()          # Informa o CLP que o python finalizou a leitura dos registradores

                #     # If there is any coil that had its value changed
                #     if self._changed_coils:   
                #         self._write(self._changed_coils)   # Writes the changed coils to the CLP
                #         self._changed_coils.clear()         # Clears the set of changed coils




                # # Se o CLP não estiver escrevendo verifica quais coil tiveram seus valores alterados
                # # e salva no registrador shadow
                # if not self.data_bank.get_coils(coils_regs.RX_WRITTING.ADDRESS, 1)[0]:  

                #     # ------------ PYTHON READING REGISTERS -------------
                #     # Informa o CLP que o python está lendo dos registradores
                #     self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [True])

                #     # Compares every coil register from 'DB coil' and 'DB coil shadow'
                #     # If 'DB coil' is different from 'DB coil shadow' some information was received
                #     for reg in coils_regs:
                #         if not self._compare_regs(reg):   # If false means that the register value was changed
                #             if reg.SIZE == 1:
                #                 print(f"Register {reg.TAG} old value {self.db_shadow.get_coils(reg.ADDRESS, reg.SIZE)} -> new value {self.data_bank.get_coils(reg.ADDRESS, reg.SIZE)}")
                #             else:
                #                 print(f"Register {reg.TAG} old value {self._conv_reg_to_value(reg, self.db_shadow)} -> new value {self._conv_reg_to_value(reg, self.data_bank)}")

                #             self._operate(reg)  # Operates according to the changed coil

                #             # Saves in the shadow register the update value
                #             self.db_shadow.set_coils(reg.ADDRESS, self.data_bank.get_coils(reg.ADDRESS, reg.SIZE))  
                    
                #     # Informa o CLP que o python finalizou a leitura dos registradores
                #     self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [False])
                #     # ------------ PYTHON FINISHED READING REGISTERS -------------



        

        print("Stopping server")
        time.sleep(1)


    def _check_handshake(self):
        if not self._compare_regs(coils_regs.HANDSHAKE):   # If false means that the register value was changed
            new = self.data_bank.get_coils(coils_regs.HANDSHAKE.ADDRESS, coils_regs.HANDSHAKE.SIZE)[0]
            # print(f"Register {coils_regs.HANDSHAKE.TAG} old value {old} -> new value {new}")
            # print(new)
            if new == True:                  # if changed from false to true
                self.timeout.check_timeout()                                            # Checks if the time between handshakes has passed the timeout limit
                self.handshake = True                                                   # DEBUG: Colocar a lógica correta -> self.handshake = not self.timeout.check_timeout()
                
                if self.data_bank.d_inputs_size == DB_size.DI_LAST_ADDRESS+1:
                    self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_SVON.ADDRESS, [True])   # Informs the CLP that the Driver is active and ready to operate

                # print(f"Handshake took {time.time() - self.timeout.timer} seconds")
                self.timeout.reset()

                if self.timeout.status:
                    print("TIMEOUT")        #TODO: Implementar lógica de timeout 
                    
                    ...
                else:
                    # print("NO TIMEOUT")
                    ...

                
            # print(f"Handshake value changed to {new}")

            # Saves the new handshake value in the shadow register and mirror it to the CLP
            self.db_shadow.set_coils(coils_regs.HANDSHAKE.ADDRESS, [new]) 
            self.data_bank.set_discrete_inputs(dig_inputs_regs.HANDSHAKE.ADDRESS, [new])

    def _mirror_clp_owned_coils(self):
        for reg in CLP_Owned:
            current_reg_value = self.data_bank.get_coils(reg.ORIGIN.ADDRESS, reg.ORIGIN.SIZE)
            # self.data_bank.set_discrete_inputs(reg.RESPONSE.ADDRESS, current_reg_value)
            match reg.ORIGIN.SIZE:
                case 32:
                    # current_reg_value.reverse()
                    self.data_bank.set_discrete_inputs(reg.RESPONSE.ADDRESS, current_reg_value[16:])     #|  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address   
                    self.data_bank.set_discrete_inputs(reg.RESPONSE.ADDRESS+16, current_reg_value[:16]) 
                case _:            
                    self.data_bank.set_discrete_inputs(reg.RESPONSE.ADDRESS, current_reg_value)



    def _check_clp_owned_coils(self, reg: RegsInfo):

        # If the register is owned by the CLP, the python must mirror the value to the CLP response register
        # so that the CLP can verify that the information was received by the python
        for clp_owned_reg in CLP_Owned:
            if reg.TAG == clp_owned_reg.ORIGIN:

                print("**********************************************************")
                bit_list = self.data_bank.get_coils(reg.ADDRESS, reg.SIZE)
                bit_string = "".join([str(int(b)) for b in bit_list])
                print(f"Register {reg.TAG} received value {bit_string}")
                print("**********************************************************")

                a = self._conv_reg_to_value(reg, self.data_bank)
                b = self._conv_reg_to_value(reg, self.db_shadow)
                print("--------------------------------------------------------------------")
                print(f"Comparing register {reg.TAG} -> DB value: {a} | Shadow value: {b}")

                resp_reg = clp_owned_reg.RESPONSE
                num = self._conv_reg_to_value(reg, self.data_bank)

                # resp = self._write(num, resp_reg)

                
                self._changed_coils.add( (resp_reg, num) )   # Adds the changed register to the set of changed coils

                if not self.CLP_writting:    
                    self.db_shadow.set_coils(reg.ADDRESS, self.data_bank.get_coils(reg.ADDRESS, reg.SIZE))   # Saves the updated value in the shadow register

                # if resp == "OK":
                #     # Must update the shadow coil with the current value
                #     print(f"Mirroring {reg.TAG} value {num} to {resp_reg.TAG}")
                #     self.db_shadow.set_coils(reg.ADDRESS, self.data_bank.get_coils(reg.ADDRESS, reg.SIZE))
                
                #     a = self._conv_reg_to_value(reg, self.data_bank)
                #     b = self._conv_reg_to_value(reg, self.db_shadow)
                #     print(f"After mirror register {reg.TAG} -> DB value: {a} | Shadow value: {b}")
                #     print("--------------------------------------------------------------------")

                # else:
                #     print("--------------------------------------------------------------------")

       
    def wait_confirmation(self, reg: RegsInfo) -> bool:

        for resp_reg in coils_regs:
            if resp_reg.TAG[1:] == reg.TAG[1:]:
                print(f"Enviado comando para DI {reg.TAG} e a resposta será dada pela coil {resp_reg.TAG}")
                break
            else:
                resp_reg = None

        if resp_reg is None:
            print(f"Não foi encontrado registrador de resposta para DI {reg.TAG}")
        
        # while self.data_bank.get_coils(resp_reg.ADDRESS, resp_reg.SIZE) != self.data_bank.get_discrete_inputs(reg.ADDRESS, reg.SIZE):
        #     print(f"Waiting confirmation for register {reg.TAG}")
        #     time.sleep(0.5)


        return True

    def _compare_regs(self, reg: RegsInfo) -> bool:
        """Compares the register value from the Data Bank and 
        the Shadow Data Bank, if the register is equal returns true.

        :param reg: Register to be compared
        :type reg: RegsInfo
        :return: True if registers are equal / False if registers are different
        :rtype: bool
        """

        # For registers with more than 1 bit the comparison is realized based on the converted value
        if reg.SIZE == 1:
            return self.data_bank.get_coils(reg.ADDRESS, reg.SIZE) == self.db_shadow.get_coils(reg.ADDRESS, reg.SIZE)   
        
        return self._conv_reg_to_value(reg, self.data_bank) == self._conv_reg_to_value(reg, self.db_shadow)
        

    def _conv_reg_to_value(self, reg: RegsInfo, db: DataBank) -> int:


        if reg.TYPE is RegType.COIL:



            bits = db.get_coils(reg.ADDRESS, reg.SIZE)
            binary_string = "".join(reversed([str(int(b)) for b in bits]))
            # binary_string = "".join([str(int(b)) for b in bits])
            int_val = int(binary_string, base=2)

            if reg.SIZE == 32:
                if binary_string[0] == '1':
                    int_val = int_val - (1 << reg.SIZE)

            # # Two's complement only applies for some registers
            # if reg.TAG.lower() in TwosComplementReg:

            #     bits = db.get_coils(reg.ADDRESS, reg.SIZE)
            #     # binary_string = "".join(reversed([str(int(b)) for b in bits]))
            #     binary_string = "".join([str(int(b)) for b in bits])
            #     int_val = int(binary_string, base=2)


            #     if binary_string[0] == '1':
            #         int_val = int_val - (1 << reg.SIZE)

            # else:

            #     bits = db.get_coils(reg.ADDRESS, reg.SIZE)
            #     binary_string = "".join(reversed([str(int(b)) for b in bits]))
            #     # binary_string = "".join([str(int(b)) for b in bits])
            #     int_val = int(binary_string, base=2)

        return int_val


    def _conv_num_bits(self, num: int, size:int) -> list:
        """Converts an int to a bitlist to be transmited considering
        two's complement for negativa numbers.

        Args:
            num (int): Number to be converted
            size (int): Number of output bits (8, 16, 32, 64)

        Returns:
            list: List with the 
        """
        # print("---------------")
        # print(f"num = {num} ----> {unsigned_value}")
        num_mod = num                                               # Just to keep the original number

        if num < 0:                                                 # If the number is negative gets the absolute value and subtracts 1
            num_mod = abs(num) 
            num_mod-=1

        bits = [(num_mod >> i) & 1 for i in range(0, size, 1)]      # Generates a list with each bit in the correct endianess (lsb to msb)
        if num < 0:                                                 # If the number is negative
            for idx, b in enumerate(bits):                              # Loop to invert the bits and 
                # bits[idx] = not b
                if b: bits[idx] = 0
                else: bits[idx] = 1
        
        return bits

    # def _conv_bits_num(self, )


    def send_command(self, register: RegsInfo) -> str:
        """Sends a command to the CLP by setting the corresponding coil register, then it starts a timer to wait for the CLP response. 
        If the CLP sets the OK coil to True before the timeout limit, the command is considered successful and the function returns True, otherwise it returns False.

        Args:
            register (RegsInfo): Register that represents the command to be sent, it must be a discrete input register that represents a command (ex: 'TX_GS21')"""

        print(f"[*] Sending command {register.TAG.upper()} to CLP")
        self._start_writting_data()
        resp = self._write({(register, True)})   # Writes the command to the CLP
        self._stop_writting_data()
        if resp == "OK":
            # If the command was successfully sent to the CLP, the Driver will wait for the CLP response
            print(f"Command {register.TAG.upper()} sent, waiting confirmation...")

            # Tries to wait for the CLP response until the timeout limit is reached, if the CLP sets the OK coil to True
            #  before the timeout limit, the command is considered successful and the function returns "OK", otherwise it returns "NOK".
            # If the timeout limit is reached without receiving any response from the CLP, the handling function for command timeout is
            #  called and the function returns "NOK"
            cmd_timer = time.time()
            while (time.time() - cmd_timer) < Config.cmd_timeout:
                            
                if self.CLP_OK:
                    self._handle_command_OK(register)
                    return "OK"
                elif self.CLP_NOK:
                    self._handle_command_NOK(register)
                    return "NOK"
            
            self._handle_command_timeout(register)
            return "NOK"

        else:
            return "NOK"


    def _handle_command_timeout(self, register: RegsInfo):
        print(f"\033[31mTIMEOUT\033[0m: {register.TAG} command was not confirmed by the CLP in less than {Config.cmd_timeout} seconds.")
        # self._start_writting_data()
        self.data_bank.set_discrete_inputs(register.ADDRESS, [False])   # Clears the command discrete input to allow sending new commands to the CLP
        # self._stop_writting_data()
        #TODO: Implementar lógica de timeout, realizar a leitura dos status do CLP e verificar qual foi o erro que ocorreu


    def _handle_command_NOK(self, register: RegsInfo):
        print(f"CLP returned\033[31m NOK\033[0m for command: {register.TAG}")
        # self._start_writting_data()
        self.data_bank.set_discrete_inputs(register.ADDRESS, [False])   # Clears the command discrete input to allow sending new commands to the CLP
        # self._stop_writting_data()
        # self.data_bank.set_discrete_inputs(dig_inputs_regs.NOK.ADDRESS, [True])   # Sets the NOK discrete input to indicate unsuccessful command execution

    def _handle_command_OK(self, register: RegsInfo):
        print(f"CLP returned\033[32m OK\033[0m for command: {register.TAG}")
        # self._start_writting_data()
        self.data_bank.set_discrete_inputs(register.ADDRESS, [False])   # Clears the command discrete input to allow sending new commands to the CLP
        # self._stop_writting_data()
        # self.data_bank.set_discrete_inputs(dig_inputs_regs.OK.ADDRESS, [True])   # Sets the OK discrete input to indicate successful command execution


    def write_param(self, reg: RegsInfo | tuple[RegsInfo], value: int | bool | tuple[int | bool]) -> str:
        
        params = set()
        if (type(reg) is tuple and type(value) is not tuple) or (type(reg) is not tuple and type(value) is tuple):
            raise ValueError(f"[Writting parameter] Both 'reg' and 'value' must be tuples when writting multiple parameters")

        if type(reg) is tuple:
            for r, v in zip(reg, value):
                if r.TYPE != RegType.DISCRETE_INPUT:
                    raise ValueError(f"Cannot write to register {r.TAG} because it is not a discrete input register.")
                params.add( (r, v) )
        else:
            if reg.TYPE != RegType.DISCRETE_INPUT:
                raise ValueError(f"Cannot write to register {reg.TAG} because it is not a discrete input register.")
            params.add( (reg, value) )




        # self._write({(reg, value)})   # Writes the command to the CLP
        self._start_writting_data()
        self._write(params)   # Writes the command to the CLP
        self._stop_writting_data()

        for tries in range(2):
            # self._start_writting_data()
            resp = self.send_command(dig_inputs_regs.TX_PR)   # Sends a parameter request command to the CLP to inform that the Driver will write a parameter to the CLP
            # self._stop_writting_data()
            if resp == "OK":

                try:

                    print(f"Parameter request operation confirmed by CLP")
                    # Must confirm that the CLP mirrored the parameters values correctly

                    if self._start_reading_data():  # Informs CLP that the Driver is reading some data from the modbus coils

                        p_dict = param_vars._asdict()
                        for p in params:
                            # if p[0].TAG in p_dict:
                            if p[0] in p_dict:

                                print(f"Waiting for CLP to mirror the value of parameter {p[0].TAG} to the response register {p_dict[p[0].TAG].RESPONSE.TAG}...")

                                t = time.time()
                                t_over = False
                                mirrored = False
                                while mirrored == False and t_over == False:
                                    print(f"COIL mirrored: {self._conv_reg_to_value(p_dict[p[0].TAG].RESPONSE, self.data_bank)}")
                                    print(f"DI SENT: {self._conv_reg_to_value(p[0], self.data_bank)}")    

                                    mirrored = self.data_bank.get_coils(p_dict[p[0].TAG].RESPONSE.ADDRESS, p_dict[p[0].TAG].RESPONSE.SIZE) == self.data_bank.get_discrete_inputs(p[0].ADDRESS, p[0].SIZE)
                                    if mirrored:
                                        print(f"[+] Parameter {reg.TAG} updated with value {value} by CLP")
                                    else:
                                        self._stop_reading_data()

                                        self.send_command(dig_inputs_regs.TX_PR)

                                        self._start_reading_data()

                                        time.sleep(0.1)
                                        if time.time() - t > 3:
                                            t_over = True
                                        
                                            print(f"[-] Coul not update parameter {reg.TAG}, timeout checking mirror value")
                                            print(f"Sent value {self.data_bank.get_discrete_inputs(p[0].ADDRESS, p[0].SIZE)[0]} ======> Mirror Coil Value  {self.data_bank.get_coils(p_dict[p[0].TAG].RESPONSE.ADDRESS, p_dict[p[0].TAG].RESPONSE.SIZE)[0]}")
                                            raise TimeoutError(f"[§]Timeout while updating paramater {reg.TAG}")
       

                    self._stop_reading_data() # Informs CLP that the Driver finished reading data from the modbus coils
                    return "OK"
                
                except Exception as e:
                    print(e)
                    self._stop_reading_data() # Informs CLP that the Driver finished reading data from the modbus coils
                    return "NOK"
                    

            elif resp == "NOK":
                print(f"CLP responded with NOK for parameter {reg.TAG} request operation. Retrying...")
                time.sleep(0.2)
        
        print(f"Failed to write parameter {reg.TAG} after {tries} tries. CLP did not confirm the operation.")
        return "NOK"
        


    def _write(self, reg_list: set[tuple[RegsInfo, int | bool]]) -> str:
            """ Writes a value to a discrete input 
            The writting process to a digital input must always follow the same process:
            - First it must be checked if the CLP is reading data, the Driver will try 5 times to 
            wait for the CLP to finish its reading.
            - Once the CLP ends its previous reading the Driver will set its WRITTING register to 
            inform the CLP that the Driver is writting some data to the modbus discrete inputs
            - When the Driver ends the writting the WRITTING register must be cleared"""
            try:
                # The application can only write new data if the CLP is not reading
                # A configurable timeout is implemented to avoid infinite loops
                t = time.time()
                write_timeout = False
                # while self.data_bank.get_coils(coils_regs.RX_READING.ADDRESS, coils_regs.RX_READING.SIZE)[0]:
                print("Waiting for CLP to finish reading before writting...")
                while self.CLP_reading:
                    if time.time() - t > Config.write_timeout:
                        # write_timeout = True
                        raise TimeoutError(f"Timeout trying to write parameter(s) to CLP. CLP was reading for more than {Config.write_timeout} seconds")

                # If the CLP is not reading, the writting process can start
                # if not write_timeout:            
                    # self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [True]) # Informs CLP that the Driver is writting some data to the modbus discrete inputs
                # self._start_writting_data()  # Informs CLP that the Driver is writting some data to the modbus discrete inputs

                # Repeats the writting process for every register in the 'reg_list'
                for reg, value in reg_list:
                    # When the register size is 1 the value must be 0, 1 or boolean
                    if (reg.SIZE==1 and not ( ( (value==0) or (value==1) or type(value) is bool ) )):
                        raise ValueError(f"Cannot write {value} to {reg.TYPE.name}:{reg.ADDRESS}. This Register supports only {reg.SIZE} bit(s).")
                    
                    # When a boolean was sent to a register that has more bits
                    if ( type(value) is bool ) and ( reg.SIZE != 1):
                        raise ValueError(f"Cannot write a boolean to {reg.TYPE.name}:{reg.ADDRESS}. This Register has {reg.SIZE} bits")

                    # time.sleep(0.1)
                                    
                    # print(f"Trying to write value {value} to {reg.TAG} -> {time.time() - t} seconds [{write_timeout}]")
                    if reg.TYPE is RegType.DISCRETE_INPUT:

                        # time.sleep(0.2)
                        if (type(value) is bool) or (reg.SIZE==1 and ( (value==0) or (value==1) ) ):                # If the value is a bool or the register has only one bit than no conversion is needed
                            self.data_bank.set_discrete_inputs(reg.ADDRESS, [value])
                        else:                                                                                       #| If the register has multiple bits than the value must be converted
                            num_bits = self._conv_num_bits(value, reg.SIZE)                                         #| The conversion already considers negative values as two's complement
                            if reg.SIZE == 8:                                                                       
                                self.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits)          # If the register is only 8 bits the value is saved directly to the register
                            else:               


                                # self.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits) 


                                self.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits[16:])     #|  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address   
                                self.data_bank.set_discrete_inputs(reg.ADDRESS+16, num_bits[:16])  #| and the lower bits must be saved to next 16 bits
                                # self.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits[:16])     #|  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address   
                                # self.data_bank.set_discrete_inputs(reg.ADDRESS+16, num_bits[16:])  #| and the lower bits must be saved to next 16 bits

                

                
                # self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])  # Informs CLP that the Driver finished writting and there is a valid data ready for reading
                # self._stop_writting_data()  # Informs CLP that the Driver finished writting

                # self.wait_confirmation(reg)
                return "OK"
            except Exception as e:
            # else:
                # print(f'Failed to write registers due to timeout. CLP is reading for more than {Config.write_timeout} seconds.')
                # raise RuntimeError(f'Failed to send {value} to register {reg.TAG} after {tries} tries')
                self._stop_writting_data()  # Just to be sure that it stops writting
                return "NOK"
            

    def _start_reading_data(self) -> bool:
        """Sets the reading status of the ModbusServer and returns if the status was changed or not. 
        If the writting process is locked the reading status cannot be set to True to avoid reading data that is being writted to the CLP,
          in this case the function returns False and the reading status is not changed."""
        self.reading = True
        # if self._reading:
        #     print(f"Started reading data from CLP [{datetime.now().strftime('%H:%M:%S')}]")
        return self._reading
    
    def _stop_reading_data(self) -> bool:
        """Sets the reading status of the ModbusServer to False and returns if the status was changed or not. 
        The reading status can be set to False even if the writting process is locked because setting the reading status to False does not cause any risk of reading data that is being writted by the CLP."""
        self.reading = False
        # if self._reading == False:
        #     print(f"Stopped reading data from CLP [{datetime.now().strftime('%H:%M:%S')}]")
        return self._reading
    
    def _start_writting_data(self) -> bool:
        """Sets the writting status of the ModbusServer and returns if the status was changed or not. 
        If the reading process is locked the writting status cannot be set to True to avoid writting data that is being read by the CLP,
          in this case the function returns False and the writting status is not changed."""
        self.writting = True
        # if self._writting:
        #     print(f"Started writting data to CLP [{datetime.now().strftime('%H:%M:%S')}]")
        return self._writting
    
    def _stop_writting_data(self) -> bool:
        """Sets the writting status of the ModbusServer to False and returns if the status was changed or not. 
        The writting status can be set to False even if the reading process is locked because setting the writting status to False does not cause any risk of writting data that is being read by the CLP."""
        self.writting = False
        # if self._writting == False:
        #     print(f"Stopped writting data to CLP [{datetime.now().strftime('%H:%M:%S')}]")
        return self._writting

