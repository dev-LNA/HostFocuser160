from pyModbusTCP.server import ModbusServer as mbServer
from pyModbusTCP.server import DataBank
from src.utils.modbus_regs import dig_inputs_regs, coils_regs

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

import time

class ModbusServer(QWidget):
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
                 data_bank: DataBank | None = None,):
        super().__init__()

            # self.dataBank = DataBank(coils_size=1127, coils_default_value=False, d_inputs_size=0, h_regs_size=0, i_regs_size=0)
        # dataBank = DataBank(coils_size=coils_size, coils_default_value=False,
        #                     d_inputs_size=d_inputs_size, d_inputs_default_value=False,
        #                     h_regs_size=h_regs_size, h_regs_default_value=0,
        #                     i_regs_size=i_regs_size, i_regs_default_value=0)
        self.server = mbServer(host=host, port=port, no_block=no_block, ipv6=ipv6, data_bank=data_bank, device_id=device_id)          # If port <=1024 needs root access on linux

        self.stop_server = False
        self.handshake = False
        self.running = False



    def run(self):
        """A loop that fills the server data bank according to the commands sent/received"""
        while not self.stop_server:
            time.sleep(1)
            if self.server.data_bank.get_coils(0,1)[0]:
                self.signal_stop.emit(True)    
                print("Sent stop server signal")
                break


            if self.server.data_bank.get_coils(coils_regs.HANDSHAKE.ADDRESS,coils_regs.HANDSHAKE.SIZE)[0]:
                self.handshake = True

            

            # print(f"coils -> {self.server.data_bank.get_coils(0,10)}")
                                                                     # bit order  8     7      6     5       4    3      2     1 
            # self.server.data_bank.set_discrete_inputs(dig_inputs_regs.TX_CGT_A, [True, True, False, False, True, False, True, True])
            # print(f"Primeiro byte do IP: {self.server.data_bank.get_discrete_inputs(dig_inputs_regs.TX_CGT_A,1)[0]}")

        print("Stoping server")

        # self.server.start()

        # print(self.server.data_bank.get_coils(0,10))