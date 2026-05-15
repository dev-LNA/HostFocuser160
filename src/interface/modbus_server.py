from pyModbusTCP.server import ModbusServer as mbServer
from pyModbusTCP.server import DataBank
from src.utils.modbus_regs import dig_inputs_regs, coils_regs, RegsInfo, RegType, DB_size, CLP_Owned, TwosComplementReg
from src.interface.modbus_data_bank import MB_DataBank

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

import time

class TimeoutCheck(QWidget):
    """Timeout verification"""

    _timeout_signal = pyqtSignal(bool)
    def __init__(self, timeout: int = 5):
        super(TimeoutCheck, self).__init__()
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
        


class ModbusServer(QWidget, mbServer):
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

    signal_stop = pyqtSignal(bool)

    def __init__(self, host: str='0.0.0.0', port: int=5005, no_block: bool=False, ipv6: bool=False, device_id=None,
                 data_bank: MB_DataBank | None = None,):
        super(ModbusServer, self).__init__(host=host, port=port, no_block=no_block, ipv6=ipv6, data_bank=data_bank, device_id=device_id)

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

        


    def run(self):
        """A loop that fills the server data bank according to the commands sent/received"""
        while not self.stop_server:
            time.sleep(.05) # 0.1
            # if self.data_bank.get_coils(0,1)[0]:        #DEBUG: usado para pausar o servidor pela comunicação
            #     self.signal_stop.emit(True)
            #     print("Sent stop server signal")
            #     break

            # coils_shadow = self.db_shadow.get_coils(DB_size.COIL_FIRST_ADDRESS, DB_size.COIL_LAST_ADDRES)         # Coils internas do programa
            # coils_real = self.data_bank.get_coils(DB_size.COIL_FIRST_ADDRESS, DB_size.COIL_LAST_ADDRES)           # Coils recebidas do CLP
            # if coils_shadow != coils_real:                          # Verifica se ocorreu alguma mudança nas coil
            #     print("Mudança nas coils detectada")
            #     reg_cont = DB_size.COIL_FIRST_ADDRESS                   # Endereço da primeira coil
            #     for (cs, cr) in zip(coils_shadow, coils_real):      # Obtém a coil na mesma posição no shadow e no real
            #         if cs != cr:                                    # Se essa coil tiver mudado atua da forma que for necessária
            # #             print("-------------------")
            # #             print(f"Reg: {reg_cont}")
            # #             print(f"Coil shadow --> {cs}")
            # #             print(f"Coil real --> {cr}")
            # #             print("-------------------")

            #             self.db_shadow.set_coils(reg_cont, 1)           # Updates shadow coil


            #DEBUG: Necessário fazer temporização para checagem de handshake
            # if self.data_bank.get_coils(coils_regs.HANDSHAKE.ADDRESS,coils_regs.HANDSHAKE.SIZE)[0]:
            #     self.handshake = True
            #     self.timeout.check_timeout()
            #     self.timeout.reset()               
             
            # Checks if a HANDSHAKE was received
            if not self._compare_regs(coils_regs.HANDSHAKE):   # If false means that the register value was changed
                old = self.db_shadow.get_coils(coils_regs.HANDSHAKE.ADDRESS, coils_regs.HANDSHAKE.SIZE)
                new = self.data_bank.get_coils(coils_regs.HANDSHAKE.ADDRESS, coils_regs.HANDSHAKE.SIZE)
                print(f"Register {coils_regs.HANDSHAKE.TAG} old value {old} -> new value {new}")
                print(new)
                if new[0] == True:                  # if changed from false to true
                    self.timeout.check_timeout()                                            # Checks if the time between handshakes has passed the timeout limit
                    self.handshake = True                                                   # DEBUG: Colocar a lógica correta -> self.handshake = not self.timeout.check_timeout()
                    print(f"Handshake took {time.time() - self.timeout.timer} seconds")
                    self.timeout.reset()

                    if self.timeout.status:
                        print("TIMEOUT")
                    else:
                        print("NO TIMEOUT")

                    # self.db_shadow.set_coils(coils_regs.HANDSHAKE.ADDRESS, self.data_bank.get_coils(coils_regs.HANDSHAKE.ADDRESS, coils_regs.HANDSHAKE.SIZE)) 
                self.db_shadow.set_coils(coils_regs.HANDSHAKE.ADDRESS, new) 
                self.data_bank.set_discrete_inputs(dig_inputs_regs.HANDSHAKE.ADDRESS, new)  # Mirror handshake value

                print(F"HANDSHAKE ATUAL: {self.data_bank.get_discrete_inputs(dig_inputs_regs.HANDSHAKE.ADDRESS, 1)}")



            # To be operational the handshake must be valid  and 'RX_WAIT' must be False
            # if self.handshake and not self.data_bank.get_coils(coils_regs.RX_WAIT.ADDRESS, 1)[0]:
            if self.handshake:
                
                # self.data_bank.set_coils(coils_regs.RX_WAIT.ADDRESS, [True])        # Puts coil RX_WAIT back to True to avoid entering again this statement

                # for reg in coils_regs:
                #     if reg.SIZE > 1:
                #         self._conv_reg_to_value(reg)

                #Timed handshake for testing
                # if time.time() - self.handshake_timer > 1:
                #     self.handshake_timer = time.time()
                #     if self.data_bank.get_discrete_inputs(dig_inputs_regs.HANDSHAKE.ADDRESS, 1)[0] == True:
                #         self.data_bank.set_discrete_inputs(dig_inputs_regs.HANDSHAKE.ADDRESS, [False])
                #     else:
                #         self.data_bank.set_discrete_inputs(dig_inputs_regs.HANDSHAKE.ADDRESS, [True])


                # 'RX_WRITTING == 0' indicates that the CLP is not writting, so the coils information is valid.
                # This guarantees that the server will not read while the CLP is writting a new value.


                # time.sleep(0.3)  # temporização para dar tempo do CLP ler infomrações


                # As variáveis que vem do CLP devem ser sempre lidas e rebatidas para o CLP, porém, elas somente
                # serão salvas no data bank principal quando o CLP enviar o sinal de que parou de escrever
                # O data bank "db_shadow" é o que possui as informações que são utilizadas pelo python
                # O data bank "data_bank" e o que possui as informações sendo recebidas pelo CLP
                for reg in coils_regs:
                    if not self._compare_regs(reg):   # If false means that the register value was changed
                        self._operate(reg)  # Operates according to the changed coil


                # Se o CLP não estiver escrevendo verifica quais coil tiveram seus valores alterados
                # e salva no registrador shadow
                if not self.data_bank.get_coils(coils_regs.RX_WRITTING.ADDRESS, 1)[0]:  
                    # Informa o CLP que o python está lendo dos registradores
                    # self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [True])

                    # Compares every coil register from 'DB coil' and 'DB coil shadow'
                    # If 'DB coil' is different from 'DB coil shadow' some information was received
                    for reg in coils_regs:
                        if not self._compare_regs(reg):   # If false means that the register value was changed
                            if reg.SIZE == 1:
                                print(f"Register {reg.TAG} old value {self.db_shadow.get_coils(reg.ADDRESS, reg.SIZE)} -> new value {self.data_bank.get_coils(reg.ADDRESS, reg.SIZE)}")
                            else:
                                print(f"Register {reg.TAG} old value {self._conv_reg_to_value(reg, self.db_shadow)} -> new value {self._conv_reg_to_value(reg, self.data_bank)}")

                            # self._operate(reg)  # Operates according to the changed coil

                            # Saves in the shadow register the update value
                            self.db_shadow.set_coils(reg.ADDRESS, self.data_bank.get_coils(reg.ADDRESS, reg.SIZE))  
                    
                    # Informa o CLP que o python finalizou a leitura dos registradores
                    # self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_READING.ADDRESS, [False])






            # print(f"coils -> {self.server.data_bank.get_coils(0,10)}")
                                                                     # bit order  8     7      6     5       4    3      2     1 
            # self.server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_CGT_A, [True, True, False, False, True, False, True, True])
            # print(f"Primeiro byte do IP: {self.server.data_bank.get_discrete_inputs(dig_inputs_regs.TX_CGT_A,1)[0]}")

        print("Stopping server")

        # self.server.start()

        # print(self.server.data_bank.get_coils(0,10))

    def _operate(self, reg: RegsInfo):



            #AÇÕES COM AS INFORMAÇÕES



        for clp_owned_reg in CLP_Owned:
            if reg.TAG == clp_owned_reg.ORIGIN_COIL:
                resp_reg = clp_owned_reg.RESPONSE_DI
                num = self._conv_reg_to_value(reg, self.data_bank)
                num_bits = self._conv_num_bits(num, reg.SIZE)

                self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [True])

                #  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address
                # and the lower bits must be saved to next 16 bits
                if reg.SIZE == 32:
                    self.data_bank.set_discrete_inputs(resp_reg.ADDRESS, num_bits[16:])     
                    self.data_bank.set_discrete_inputs(resp_reg.ADDRESS+16, num_bits[:16])
                else:
                    self.data_bank.set_discrete_inputs(resp_reg.ADDRESS, num_bits)

                self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_WRITTING.ADDRESS, [False])

                binary_string = "".join([str(int(b)) for b in self.data_bank.get_coils(reg.ADDRESS, reg.SIZE)])
                # print(f"Coil recebida {reg.TAG} = {binary_string}")
                binary_string = "".join([str(int(b)) for b in self.data_bank.get_discrete_inputs(resp_reg.ADDRESS, resp_reg.SIZE)])
                # print(f"DI {resp_reg.TAG} = {binary_string}")

       
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