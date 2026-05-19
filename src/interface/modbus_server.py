from pyModbusTCP.server import ModbusServer as mbServer
from pyModbusTCP.server import DataBank
from src.utils.modbus_regs import dig_inputs_regs, coils_regs, RegsInfo, RegType, CLP_Owned, TwosComplementReg
from src.utils.constants import CommandTimeout
from src.interface.modbus_data_bank import MB_DataBank


from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtWidgets import QWidget

import time
from threading import Timer

class TimeoutCheck(QObject):
    """Handshake Timeout verification"""

    _timeout_signal = pyqtSignal(bool)
    def __init__(self, timeout: int = 5):
        super(QObject, self).__init__()
        self._timeout_limit = timeout                           # Timeout limit
        self.timer: int = 0                                     # Current timer

        self.status = False                                     # Timeout status (True -> timeout occured)
        self.blockSignals(False)

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
            timer=Timer(3.0, self._handle_command_timeout)
        )
            

    def run(self):
        """A loop that fills the server data bank according to the commands sent/received"""
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
                for reg in coils_regs:
                    if not self._compare_regs(reg):     # If false means that the register value was changed
                        a = self._conv_reg_to_value(reg, self.data_bank)
                        b = self._conv_reg_to_value(reg, self.db_shadow)

                        print(f"Comparing register {reg.TAG} -> DB value: {a} | Shadow value: {b}")
                        self._mirror(reg)               # Mirrors the CLP owned coils

                        a = self._conv_reg_to_value(reg, self.data_bank)
                        b = self._conv_reg_to_value(reg, self.db_shadow)
                        print(f"After mirror register {reg.TAG} -> DB value: {a} | Shadow value: {b}")



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


    def _check_handshake(self):
        if not self._compare_regs(coils_regs.HANDSHAKE):   # If false means that the register value was changed
            new = self.data_bank.get_coils(coils_regs.HANDSHAKE.ADDRESS, coils_regs.HANDSHAKE.SIZE)
            # print(f"Register {coils_regs.HANDSHAKE.TAG} old value {old} -> new value {new}")
            # print(new)
            if new[0] == True:                  # if changed from false to true
                self.timeout.check_timeout()                                            # Checks if the time between handshakes has passed the timeout limit
                self.handshake = True                                                   # DEBUG: Colocar a lógica correta -> self.handshake = not self.timeout.check_timeout()
                # print(f"Handshake took {time.time() - self.timeout.timer} seconds")
                self.timeout.reset()

                if self.timeout.status:
                    print("TIMEOUT")        #TODO: Implementar lógica de timeout 
                else:
                    print("NO TIMEOUT")

            # Saves the new handshake value in the shadow register and mirror it to the CLP
            self.db_shadow.set_coils(coils_regs.HANDSHAKE.ADDRESS, new) 
            self.data_bank.set_discrete_inputs(dig_inputs_regs.HANDSHAKE.ADDRESS, new)

    def _operate(self, reg: RegsInfo):


        if reg.SIZE == 1:
            reg_value = self.data_bank.get_coils(reg.ADDRESS, reg.SIZE)[0]
        else:
            reg_value = self._conv_reg_to_value(reg, self.data_bank)

        if reg.TAG == coils_regs.OK.TAG:
            if reg_value == True:
                # self.signals.signal_OK.emit(True)
                self._handle_OK(reg_value)



    def _mirror(self, reg: RegsInfo):

        # If the register is owned by the CLP, the python must mirror the value to the CLP response register
        # so that the CLP can verify that the information was received by the python
        for clp_owned_reg in CLP_Owned:
            if reg.TAG == clp_owned_reg.ORIGIN_COIL:
                resp_reg = clp_owned_reg.RESPONSE_DI
                num = self._conv_reg_to_value(reg, self.data_bank)

                resp = self._write(num, resp_reg)

                if resp == "OK":
                    # Must update the shadow coil with the current value
                    print(f"Mirroring {reg.TAG} value {num} to {resp_reg.TAG}")
                    self.db_shadow.set_coils(reg.ADDRESS, self.data_bank.get_coils(reg.ADDRESS, reg.SIZE))


                # ------------ PYTHON WRITTING REGISTER -------------
                # self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [True])

                # #  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address
                # # and the lower bits must be saved to next 16 bits
                # if reg.SIZE == 32:
                #     self.data_bank.set_discrete_inputs(resp_reg.ADDRESS, num_bits[16:])     
                #     self.data_bank.set_discrete_inputs(resp_reg.ADDRESS+16, num_bits[:16])
                # else:
                #     self.data_bank.set_discrete_inputs(resp_reg.ADDRESS, num_bits)

                # self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])
                # ------------ PYTHON FINISHED WRITTING REGISTER -------------

       
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

            # Two's complement only applies for some registers
            if reg.TAG.lower() in TwosComplementReg:

                bits = db.get_coils(reg.ADDRESS, reg.SIZE)
                # binary_string = "".join(reversed([str(int(b)) for b in bits]))
                binary_string = "".join([str(int(b)) for b in bits])
                int_val = int(binary_string, base=2)


                if binary_string[0] == '1':
                    int_val = int_val - (1 << reg.SIZE)

            else:

                bits = db.get_coils(reg.ADDRESS, reg.SIZE)
                binary_string = "".join(reversed([str(int(b)) for b in bits]))
                # binary_string = "".join([str(int(b)) for b in bits])
                int_val = int(binary_string, base=2)

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



        
    def _handle_OK(self, ok_value: bool):

        # If a command was sent and the OK coil is set it means that the
        # command was successful and 'command_timeout' must be reset.
        if self.command_timeout.command and ok_value == True:
            self.command_timeout.timer.cancel() 

            com_reg = getattr(dig_inputs_regs, self.command_timeout.command)

            print(f"*******************OK RECEBIDO **************************")
            print(f"*******************{com_reg.TAG} **************************")


            self._write(False, com_reg)


            self.command_timeout.command = ""


    def _handle_command_timeout(self):
        print(f"TIMEOUT: {self.command_timeout.command}")

        com_reg = getattr(dig_inputs_regs, self.command_timeout.command)

        self._write(False, com_reg)

        self.command_timeout.timer.cancel() 
        self.command_timeout.command = ""






    # def _write(self, value: int | bool, reg: RegsInfo) -> str:
        # """ Writes a value to a discrete input 
        # The writting process to a digital input must always follow the same process:
        # - First it must be checked if the CLP is reading data, the Driver will try 5 times to 
        #    wait for the CLP to finish its reading.
        # - Once the CLP ends its previous reading the Driver will set its WRITTING register to 
        #    inform the CLP that the Driver is writting some data to the modbus discrete inputs
        # - When the Driver ends the writting the WRITTING register must be cleared"""
        
        # # When the register size is 1 the value must be 0, 1 or boolean
        # if (reg.SIZE==1 and not ( ( (value==0) or (value==1) or type(value) is bool ) )):
        #     raise ValueError(f"Cannot write {value} to {reg.TYPE.name}:{reg.ADDRESS}. This Register supports only {reg.SIZE} bit(s).")
        
        # # When a boolean was sent to a register that has more bits
        # if ( type(value) is bool ) and ( reg.SIZE != 1):
        #     raise ValueError(f"Cannot write a boolean to {reg.TYPE.name}:{reg.ADDRESS}. This Register has {reg.SIZE} bits")

        # tries = 0
        # max_tries = 20
        # # Tries 'max_tries' times to send the data
        # while tries < max_tries:
        #     time.sleep(0.1)
        #     # The application can only write new data if the CLP is not reading
        #     if not self.data_bank.get_coils(coils_regs.RX_READING.ADDRESS, coils_regs.RX_READING.SIZE)[0]:
        #         if reg.TYPE is RegType.DISCRETE_INPUT:

        #             self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [True])
        #             time.sleep(0.05)
        #             if (type(value) is bool) or (reg.SIZE==1 and ( (value==0) or (value==1) ) ):                # If the value is a bool or the register has only one bit than no conversion is needed
        #                 self.data_bank.set_discrete_inputs(reg.ADDRESS, [value])
        #             else:                                                                                       #| If the register has multiple bits than the value must be converted
        #                 num_bits = self._conv_num_bits(value, reg.SIZE)                                         #| The conversion already considers negative values as two's complement
        #                 if reg.SIZE == 8:                                                                       
        #                     self.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits)          # If the register is only 8 bits the value is saved directly to the register
        #                 else:                                                                                   
        #                     self.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits[16:])     #|  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address   
        #                     self.data_bank.set_discrete_inputs(reg.ADDRESS+16, num_bits[:16])  #| and the lower bits must be saved to next 16 bits

        #             self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])  # Informs CLP that there is a valid data ready for readi
        #             # self.wait_confirmation(reg)
        #         break
        #     else:
        #         tries += 1
        # if tries == max_tries:
        #     print(f'Failed to send {value} to register {reg.TAG} after {tries} tries')
        #     # raise RuntimeError(f'Failed to send {value} to register {reg.TAG} after {tries} tries')
        #     return "NOK"
        # else:
        #     return "OK"


    def _write(self, value: int | bool, reg: RegsInfo) -> str:
        """ Writes a value to a discrete input 
        The writting process to a digital input must always follow the same process:
        - First it must be checked if the CLP is reading data, the Driver will try 5 times to 
           wait for the CLP to finish its reading.
        - Once the CLP ends its previous reading the Driver will set its WRITTING register to 
           inform the CLP that the Driver is writting some data to the modbus discrete inputs
        - When the Driver ends the writting the WRITTING register must be cleared"""
        
        # When the register size is 1 the value must be 0, 1 or boolean
        if (reg.SIZE==1 and not ( ( (value==0) or (value==1) or type(value) is bool ) )):
            raise ValueError(f"Cannot write {value} to {reg.TYPE.name}:{reg.ADDRESS}. This Register supports only {reg.SIZE} bit(s).")
        
        # When a boolean was sent to a register that has more bits
        if ( type(value) is bool ) and ( reg.SIZE != 1):
            raise ValueError(f"Cannot write a boolean to {reg.TYPE.name}:{reg.ADDRESS}. This Register has {reg.SIZE} bits")

        tries = 0
        max_tries = 20
        # Tries 'max_tries' times to send the data
        # while tries < max_tries:
        time.sleep(0.1)
        # The application can only write new data if the CLP is not reading
        # if not self.data_bank.get_coils(coils_regs.RX_READING.ADDRESS, coils_regs.RX_READING.SIZE)[0]:

        t = time.time()
        write_timeout = False
        while self.data_bank.get_coils(coils_regs.RX_READING.ADDRESS, coils_regs.RX_READING.SIZE)[0]:
            if time.time() - t > 3:
                write_timeout = True
                break
        
        print(f"Trying to write value {value} to {reg.TAG} -> {time.time() - t} seconds [{write_timeout}]")
        if not write_timeout:
            if reg.TYPE is RegType.DISCRETE_INPUT:

                self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [True])
                time.sleep(0.05)
                if (type(value) is bool) or (reg.SIZE==1 and ( (value==0) or (value==1) ) ):                # If the value is a bool or the register has only one bit than no conversion is needed
                    self.data_bank.set_discrete_inputs(reg.ADDRESS, [value])
                else:                                                                                       #| If the register has multiple bits than the value must be converted
                    num_bits = self._conv_num_bits(value, reg.SIZE)                                         #| The conversion already considers negative values as two's complement
                    if reg.SIZE == 8:                                                                       
                        self.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits)          # If the register is only 8 bits the value is saved directly to the register
                    else:                                                                                   
                        self.data_bank.set_discrete_inputs(reg.ADDRESS, num_bits[16:])     #|  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address   
                        self.data_bank.set_discrete_inputs(reg.ADDRESS+16, num_bits[:16])  #| and the lower bits must be saved to next 16 bits

                self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])  # Informs CLP that there is a valid data ready for readi
                # self.wait_confirmation(reg)
                return "OK"
        else:
            print(f'Failed to send {value} to register {reg.TAG} after {tries} tries')
            # raise RuntimeError(f'Failed to send {value} to register {reg.TAG} after {tries} tries')
            return "NOK"

