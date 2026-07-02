from pyModbusTCP.server import ModbusServer as mbServer
from pyModbusTCP.server import DataBank
from src.core.config import Config
from src.utils.constants import CommandTimeout, TimeoutState, TimeDelays
from src.interface.modbus_data_bank import MB_DataBank
from src.utils.modbus_regs import (dig_inputs_regs, 
                                    coils_regs, RegsInfo, 
                                    RegType, CLP_Mirror, 
                                    TwosComplementReg,
                                    param_vars,
                                    DB_size, 
                                    holding_regs,
                                    PackCMDFlags,
                                    PackStatusFlags,
                                    mirrorMapping)


from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtWidgets import QWidget

import time
from threading import Timer, Lock
from datetime import datetime

class TimeoutCheck(QObject):
    """Handshake Timeout verification"""

    signal_timeout = pyqtSignal(bool)
    def __init__(self, driver_timeout_method, timeout: int = 8):
        super(QObject, self).__init__()
        self._timeout_limit = timeout                           # Timeout limit
        self.timer: float = 0                                     # Current timer

        self.status: TimeoutState = TimeoutState.NO_TIMEOUT     # Timeout status (True -> timeout occured)
        self.old_val = False
        self._running:bool = False
        self.elapsed_time = 0

        self.callback_on_timeout = driver_timeout_method

        self.reset()

    @property
    def running(self) -> bool:
        return self._running
    @running.setter
    def running(self, value:bool):
        self._running = value

    def reset(self):
        """Resets timeout timer"""
        self.timer = time.time()


    def check_timeout(self, new_val: bool) -> TimeoutState:
        """Checks if a timeout occured
        The timeout occurs whent this function is not called in less than '_timeout_limit' seconds

        Returns:
            bool:   True -> Timeout
                    False -> No timeout
        """ 
        if self.running:    
            self.elapsed_time = time.time() - self.timer    
        else:
            self.elapsed_time = 0
    
        # print(f"checking timeout: {self.elapsed_time}")

        # return self.status 
        if (self.old_val != new_val):
            if (self.elapsed_time) < self._timeout_limit:     
                    self.status = TimeoutState.NO_TIMEOUT  
                    self.reset()
            else:
                self.status = TimeoutState.TIMEOUT                                  
                self.callback_on_timeout()                          # Calls driver function to deal with the timeout
        else:
            if (self.elapsed_time) > self._timeout_limit:
                self.status = TimeoutState.TIMEOUT
                self.callback_on_timeout() 
            else:
                self.status = TimeoutState.WAIT_INFO      # Não deu timeout mas não pode resetar o timer
        
        self.old_val = new_val
        return self.status 
    
    
        
class MB_Server_Communicator(QObject):
    task_progress = pyqtSignal(int)


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
    _params_initialized: bool = False
    _handshake: bool = False
    def __init__(self, data_bank: MB_DataBank, host: str='0.0.0.0', port: int=5005, no_block: bool=False, ipv6: bool=False, device_id=None,
                 timeout_callback_function = None):
        super().__init__(host=host, port=port, no_block=no_block, ipv6=ipv6, data_bank=data_bank, device_id=device_id)

            # self.dataBank = DataBank(coils_size=1127, coils_default_value=False, d_inputs_size=0, h_regs_size=0, i_regs_size=0)
        # dataBank = DataBank(coils_size=coils_size, coils_default_value=False,
        #                     d_inputs_size=d_inputs_size, d_inputs_default_value=False,
        #                     h_regs_size=h_regs_size, h_regs_default_value=0,
        #                     i_regs_size=i_regs_size, i_regs_default_value=0)
        
        #self.server = mbServer(host=host, port=port, no_block=no_block, ipv6=ipv6, data_bank=data_bank, device_id=device_id)          # If port <=1024 needs root access on linux

        # self.host = host
        # self.port = port
        

        self.stop_server = False
        
        self.running = False

        self.timeout = TimeoutCheck(timeout_callback_function)
        self.mb_comm = MB_Server_Communicator()

        self.command_timeout = CommandTimeout(
            command='',
            timer=Timer(Config.write_timeout, self._handle_command_timeout)
        )
            
        self._changed_coils: set[tuple[RegsInfo, int | bool]] = set()   # A set to keep track of the coils that had their value changed


    @property
    def handshake(self) -> bool:
        """Returns if the ModbusServer received a handshake from the CLP"""
        return self._handshake
    @handshake.setter
    def handshake(self, value: bool):
        if value != self._handshake:
            self._handshake = value
            

    def run(self):
        """Loop that operates the modbus server"""
        while not self.stop_server:
            time.sleep(.05) # 0.1
             
            # Checks if a HANDSHAKE was received and if a timeout occured
            self._check_handshake()

            # self._mirror_clp_owned_coils()

            # To be operational the handshake must be valid
            if self.handshake: #and self._params_initialized:
                
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
                # self._mirror_clp_owned_coils()

                # for reg in coils_regs:
                #     if not self._compare_regs(reg):
                #         current_reg_val = self._conv_reg_to_value(reg, self.data_bank)
                pass
                                    

        print("Stopping server")
        # self.timeout = None
        time.sleep(1)


    def _check_handshake(self):
        """Checks if a handshake was received from the CLP and if a timeout occured"""
        packstatus = self.data_bank.get_holding_registers(holding_regs.RX_PACKSTATUS.ADDRESS, holding_regs.RX_PACKSTATUS.SIZE)
        if packstatus:
            handshake_val = bool(packstatus[0] & PackStatusFlags.HANDSHAKE)
            
            if self.timeout.check_timeout(handshake_val) == TimeoutState.NO_TIMEOUT:
                self.handshake = True
                self.data_bank.set_discrete_inputs(dig_inputs_regs.TX_SVON.ADDRESS, [True])

            self.data_bank.set_coils(coils_regs.HANDSHAKE.ADDRESS, [handshake_val])   
            self.data_bank.set_discrete_inputs(dig_inputs_regs.HANDSHAKE.ADDRESS, [handshake_val])


    def _mirror_clp_owned_coils(self):
        pass
        # for reg in CLP_Mirror:
        #     current_reg_value = self.data_bank.get_coils(reg.ORIGIN.ADDRESS, reg.ORIGIN.SIZE)
        #     # self.data_bank.set_discrete_inputs(reg.RESPONSE.ADDRESS, current_reg_value)
        #     if current_reg_value:
        #         match reg.ORIGIN.SIZE:
        #             case 32:
        #                 # current_reg_value.reverse()
        #                 self.data_bank.set_discrete_inputs(reg.RESPONSE.ADDRESS, current_reg_value[16:])     #|  If the register is 32 bits the higher bits must be saved to the first 16 bits of the address   
        #                 self.data_bank.set_discrete_inputs(reg.RESPONSE.ADDRESS+16, current_reg_value[:16]) 
        #             case _:            
        #                 self.data_bank.set_discrete_inputs(reg.RESPONSE.ADDRESS, current_reg_value)


    def _conv_reg_to_value(self, reg: RegsInfo, db: DataBank) -> int:


        if reg.TYPE is RegType.COIL:

            bits = db.get_coils(reg.ADDRESS, reg.SIZE)
            if bits:
                binary_string = "".join(reversed([str(int(b)) for b in bits]))
                # binary_string = "".join([str(int(b)) for b in bits])
                int_val = int(binary_string, base=2)

                if reg.SIZE == 32:
                    if binary_string[0] == '1':
                        int_val = int_val - (1 << reg.SIZE)

        elif reg.TYPE is RegType.DISCRETE_INPUT:
            bits = db.get_discrete_inputs(reg.ADDRESS, reg.SIZE)
            if bits:
                binary_string = "".join(reversed([str(int(b)) for b in bits]))
                # binary_string = "".join([str(int(b)) for b in bits])
                int_val = int(binary_string, base=2)

                if reg.SIZE == 32:
                    if binary_string[0] == '1':
                        int_val = int_val - (1 << reg.SIZE)

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


    def send_command(self, command: PackCMDFlags) -> str:
        """
        Sends a command to the CLP by setting the corresponding bit in PACKCMDS register, then it starts a timer to wait for the CLP response.
        If the CLP sets the OK bit in PACKOK register before the timeout limit, the command is considered successful and the function returns "OK", otherwise it returns "NOK".

        Args:
            command (PackCMDFlags): Command to be sent, it must be a flag from the PackCMDFlags enum (ex: PackCMDFlags.TX_GS21)"""

        print(f"[*] Sending command {str(command.name).upper()} to CLP")

        self.data_bank.set_holding_registers(holding_regs.TX_PACKCMDS.ADDRESS, [command.value])   # Writes the command to the CLP


        # resp = self._write({(register, True)})   # Writes the command to the CLP
        # if resp == "OK":
        #     # If the command was successfully sent to the CLP, the Driver will wait for the CLP response
        #     print(f"Command {register.TAG.upper()} sent, waiting confirmation...")

        #     # Tries to wait for the CLP response until the timeout limit is reached, if the CLP sets the OK coil to True
        #     #  before the timeout limit, the command is considered successful and the function returns "OK", otherwise it returns "NOK".
        #     # If the timeout limit is reached without receiving any response from the CLP, the handling function for command timeout is
        #     #  called and the function returns "NOK"
        #     cmd_timer = time.time()
        #     while (time.time() - cmd_timer) < Config.cmd_timeout:
        #         time.sleep(TimeDelays.WAIT_CLP_RESPONSE)                 # When no time is applied the program has a peak of cpu usage when waiting 
        #         if self.CLP_OK:
        #             self._handle_command_OK(register)
        #             return "OK"
        #         elif self.CLP_NOK:
        #             self._handle_command_NOK(register)
        #             return "NOK"
            
        #     self._handle_command_timeout(register)
        #     return "NOK"

        # else:
        #     return "NOK"


    def _handle_command_timeout(self, register: RegsInfo):
        print(f"\033[31mTIMEOUT\033[0m: {register.TAG} command was not confirmed by the CLP in less than {Config.cmd_timeout} seconds.")
        # # self._start_writting_data()
        self.data_bank.set_discrete_inputs(register.ADDRESS, [False])   # Clears the command discrete input to allow sending new commands to the CLP
        # self._stop_writting_data()
        #TODO: Implementar lógica de timeout, realizar a leitura dos status do CLP e verificar qual foi o erro que ocorreu


    def _handle_command_NOK(self, register: RegsInfo):
        print(f"CLP returned\033[31m NOK\033[0m for command: {register.TAG}")
        # # self._start_writting_data()
        self.data_bank.set_discrete_inputs(register.ADDRESS, [False])   # Clears the command discrete input to allow sending new commands to the CLP
        # self._stop_writting_data()
        # self.data_bank.set_discrete_inputs(dig_inputs_regs.NOK.ADDRESS, [True])   # Sets the NOK discrete input to indicate unsuccessful command execution

    def _handle_command_OK(self, register: RegsInfo):
        print(f"CLP returned\033[32m OK\033[0m for command: {register.TAG}")
        # # self._start_writting_data()
        self.data_bank.set_discrete_inputs(register.ADDRESS, [False])   # Clears the command discrete input to allow sending new commands to the CLP
        # self._stop_writting_data()
        # self.data_bank.set_discrete_inputs(dig_inputs_regs.OK.ADDRESS, [True])   # Sets the OK discrete input to indicate successful command execution


    def write_param(self, reg: RegsInfo | tuple[RegsInfo, ...], value: int | bool | tuple[int, ...] | tuple[bool, ...] | tuple[str, ...]) -> str | None:
        """
        Writes a parameter to the CLP by setting the corresponding value to the parameter holding register.
        Writting sequence:
            - Server writes parameter(s) value(s) to the corresponding holding register(s);
            - Server waits for the CLP to mirror the parameter(s) to its mirror holding register to guarantee that the 
                value was correctly received by the CLP;
            - If the value is mirrored correctly the function sends the command flag 'TX_SET' to 
                the CLP to inform that the parameter was successfully sent and mirrored;
            - Server waits for the CLP to respond with 'RX_SET_OK', if the CLP responds with 'RX_SET_OK' the 
                server must clear 'TX_SET' and the function returns "OK", otherwise it returns "NOK".
        """

        params = set()
        if (type(reg) is tuple and type(value) is not tuple) or (type(reg) is not tuple and type(value) is tuple):
            raise ValueError(f"[Writting parameter] Both 'reg' and 'value' must be tuples when writting multiple parameters")

        if type(reg) is tuple and type(value) is tuple:
            for r, v in zip(reg, value):
                if r.TYPE != RegType.HOLDING_REGISTER:
                    raise ValueError(f"Cannot write to register {r.TAG} because it is not a discrete input register.")
                params.add( (r, v) )
        elif type(reg) is RegsInfo:
            if reg.TYPE != RegType.HOLDING_REGISTER:
                raise ValueError(f"Cannot write to register {reg.TAG} because it is not a discrete input register.")
            params.add( (reg, value) )


        # self._write({(reg, value)})   # Writes the command to the CLP
        # self._start_writting_data()
        self._write(params)   # Writes the command to the CLP

        time.sleep(TimeDelays.WAIT_CLP_PROCESS)  #0.2   # Time for CLP to process information

        mirror_check:bool = False
        t_start = time.time()
        while not mirror_check:
            count = 0
            msg = 'Failed to confirm parameters: '
            print('-' * 50)
            for param in params:
                r:RegsInfo = param[0]
                v = param[1]
                mirror_reg:mirrorMapping = CLP_Mirror[r.TAG]
                resp = self.data_bank.get_holding_registers(mirror_reg.RESPONSE.ADDRESS, mirror_reg.RESPONSE.SIZE)
                if resp:
                    if (r.SIZE==1):                # If register has only one word than no conversion is needed
                        resp = resp[0]
                        print(f"Param: {r.DESCRIPTION} | Sent: {v} | Received: {resp}")
                    else:
                    # If the register has more than one word, the value must sent as [LSW, MSW]
                    # considering LSW the first register in the mapping address and MSW the last register in the mapping address
                        lsw = resp[0]
                        msw = resp[1]
                        resp = 0
                        resp += lsw
                        resp += (msw << 16) & 0xFFF000 
                        print(f"Param: {r.DESCRIPTION} | Sent: {v} | Received: {resp}")

                    if v == resp:
                        count +=1
                    else:
                        msg += r.DESCRIPTION + ' | '

                    
            if count == len(params):
                mirror_check = True
            else:
                if time.time() - t_start > 3:
                    if msg != 'Failed to confirm parameters: ':
                        msg = msg[:-3]
                    raise TimeoutError(msg)
        
        print('-' * 50)

        # Setting SET
        val = self.data_bank.get_holding_registers(holding_regs.TX_PACKCMDS.ADDRESS, 1)
        if val:
            val = val[0] | PackCMDFlags.TX_SET
            self.data_bank.set_holding_registers(holding_regs.TX_PACKCMDS.ADDRESS, [val])
        
        # Checking for SET OK
        ok: bool = False
        t_start = time.time()
        while time.time() - t_start < 1 and not ok:
            val = self.data_bank.get_holding_registers(holding_regs.RX_PACKOK.ADDRESS, 1)
            if val:
                ok = bool(val[0] & PackCMDFlags.TX_SET)
        
        # Must clear SET 
        val = self.data_bank.get_holding_registers(holding_regs.TX_PACKCMDS.ADDRESS, 1)
        if val:
            val = val[0] & (not PackCMDFlags.TX_SET)
            self.data_bank.set_holding_registers(holding_regs.TX_PACKCMDS.ADDRESS, [val])

        if ok:
            print("*** OK")
            return "OK"
        else:
            print("--- NOK")
            return "NOK"




    
        # self.mb_comm.task_progress.emit(0)  # Just to update the progress bar in the GUI, it does not represent the actual writting progress
        # progress = 0
        # time.sleep(TimeDelays.WAIT_CLP_PROCESS)  #0.2   # Time for CLP to process information

        # for tries in range(2):
        #     # # self._start_writting_data()
        #     # Sends a parameter request command to the CLP to inform that the Driver will write a parameter to the CLP
        #     # resp = self.send_command(dig_inputs_regs.TX_PR)   
        #     # self._stop_writting_data()

        #     resp = "OK"  # For now the command is not being sent to the CLP, so it is assumed that the command was successful
        #     if resp == "OK":

        #         try:

        #             print(f"Parameter request operation confirmed by CLP")
        #             # Must confirm that the CLP mirrored the parameters values correctly


        #             p_dict = param_vars._asdict()
        #             for p in params:
        #                 # if p[0].TAG in p_dict:
        #                 time.sleep(TimeDelays.WAIT_CLP_MIRROR)     # Time for CLP to mirror the value to the response register
        #                 progress += 1    
        #                 self.mb_comm.task_progress.emit(int((progress / len(params)) * 100))  # Just to update the progress bar in the GUI, it does not represent the actual writting progress   

        #                 if p[0] in p_dict:
                            
        #                     print(f"Waiting for CLP to mirror the value of parameter {p[0].TAG} to the response register {p_dict[p[0].TAG].RESPONSE.TAG}...")

        #                     t = time.time()
        #                     t_over = False
        #                     mirrored = False
        #                     while mirrored == False and t_over == False:
        #                         print(f"COIL mirrored: {self._conv_reg_to_value(p_dict[p[0].TAG].RESPONSE, self.data_bank)}")
        #                         print(f"DI SENT: {self._conv_reg_to_value(p[0], self.data_bank)}")    

        #                         mirrored = self.data_bank.get_coils(p_dict[p[0].TAG].RESPONSE.ADDRESS, p_dict[p[0].TAG].RESPONSE.SIZE) == self.data_bank.get_discrete_inputs(p[0].ADDRESS, p[0].SIZE)
        #                         if mirrored:
        #                             print(f"[+] Parameter {p[0].TAG} updated with value {value} by CLP")
        #                         else:
        #                             # self._stop_reading_data()

        #                             # self.send_command(dig_inputs_regs.TX_PR)

        #                             # self._start_reading_data()

        #                             time.sleep(TimeDelays.WAIT_CLP_MIRROR)
        #                             if time.time() - t > 3:
        #                                 t_over = True
                                    
        #                                 print(f"[-] Could not update parameter {p[0].TAG}, timeout checking mirror value")
        #                                 # print(f"Sent value {self.data_bank.get_discrete_inputs(p[0].ADDRESS, p[0].SIZE)[0]} ======> Mirror Coil Value  {self.data_bank.get_coils(p_dict[p[0].TAG].RESPONSE.ADDRESS, p_dict[p[0].TAG].RESPONSE.SIZE)[0]}")
        #                                 raise TimeoutError(f"[§]Timeout while updating paramater {p[0].TAG}")
       

        #             return "OK"
                
        #         except Exception as e:
        #             print(e)
        #             return "NOK"
                    

        #     elif resp == "NOK":
        #         print(f"CLP responded with NOK for parameter request operation. Retrying...")
        #         time.sleep(0.2)
        
        # print(f"Failed to write parameter after {tries} tries. CLP did not confirm the operation.")
        # return "NOK"
        


    def _write(self, reg_list: set[tuple[RegsInfo, int | bool]]) -> str:
            """ Writes a value to a holding register"""

            try:
                # A configurable timeout is implemented to avoid infinite loops
                t = time.time()

                self.mb_comm.task_progress.emit(0)  # Just to update the progress bar in the GUI, it does not represent the actual writting progress
                progress = 0
                len_reg_list = len(reg_list)

                # Repeats the writting process for every register in the 'reg_list'
                for reg, value in reg_list:
                    # time.sleep(0.1)
                    progress += 1
                    self.mb_comm.task_progress.emit(int((progress / len_reg_list) * 100))  # Update the progress bar in the GUI

                    # print(f"Trying to write value {value} to {reg.TAG} -> {time.time() - t} seconds [{write_timeout}]")
                    if reg.TYPE is RegType.HOLDING_REGISTER:

                        # time.sleep(0.2)
                        if (reg.SIZE==1):                # If register has only one word than no conversion is needed
                            self.data_bank.set_holding_registers(reg.ADDRESS, [value])
                        else:
                        # If the register has more than one word, the value must sent as [LSW, MSW]
                        # considering LSW the first register in the mapping address and MSW the last register in the mapping address
                            lsw = value & 0x0000FFFF
                            msw = (value & 0xFFFF0000) >> 16
                            self.data_bank.set_holding_registers(reg.ADDRESS, [lsw, msw])

                self.mb_comm.task_progress.emit(0)  # Just to update the progress bar in the GUI, it does not represent the actual writting progress
                # self.wait_confirmation(reg)
                return "OK"
            except Exception as e:
            # else:
                # print(f'Failed to write registers due to timeout. CLP is reading for more than {Config.write_timeout} seconds.')
                # raise RuntimeError(f'Failed to send {value} to register {reg.TAG} after {tries} tries')
                self.mb_comm.task_progress.emit(0)  # Just to update the progress bar in the GUI, it does not represent the actual writting progress
                return "NOK"
            

    

