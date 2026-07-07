from pyModbusTCP.server import DataBank, ModbusServer
from src.utils.modbus_regs import coils_regs, dig_inputs_regs
import time

class MB_DataBank(DataBank):
    client_info: ModbusServer.ClientInfo | None = None

    def __init__(self, coils_size=65536, coils_default_value=False, d_inputs_size=65536, d_inputs_default_value=False, h_regs_size=65536, h_regs_default_value=0, i_regs_size=65536, i_regs_default_value=0, virtual_mode=False):
        super().__init__(coils_size, coils_default_value, d_inputs_size, d_inputs_default_value, h_regs_size, h_regs_default_value, i_regs_size, i_regs_default_value, virtual_mode)

        self.handshake = False

        self.t1 = 0
        self.t2 = 0

    def on_coils_change(self, address, from_value, to_value, srv_info):
        return super().on_coils_change(address, from_value, to_value, srv_info)
    

    def on_holding_registers_change(self, address, from_value, to_value, srv_info:ModbusServer.ServerInfo):
        self.client_info = srv_info.client
        return super().on_holding_registers_change(address, from_value, to_value, srv_info)
        