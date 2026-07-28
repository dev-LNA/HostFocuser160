from pyModbusTCP.server import DataBank, ModbusServer
from src.utils.modbus_regs import coils_regs, dig_inputs_regs
import time

class MB_DataBank(DataBank):
    # client_info: ModbusServer.ClientInfo | None = None

    def __init__(self, coils_size=65536, coils_default_value=False, d_inputs_size=65536, d_inputs_default_value=False, h_regs_size=65536,
                  h_regs_default_value=0, i_regs_size=65536, i_regs_default_value=0, virtual_mode=False, allowed_ip: str = '127.0.0.1'):
        super().__init__(coils_size, coils_default_value, d_inputs_size, d_inputs_default_value, h_regs_size, h_regs_default_value, i_regs_size, i_regs_default_value, virtual_mode)

        self._allowed_ip = allowed_ip
        self.handshake = False

        self.ping_allowed = True
        self.client_info :ModbusServer.ClientInfo = ModbusServer.ClientInfo()

        self.t1 = 0
        self.t2 = 0

    def on_coils_change(self, address, from_value, to_value, srv_info):
        return super().on_coils_change(address, from_value, to_value, srv_info)
    

    def on_holding_registers_change(self, address, from_value, to_value, srv_info:ModbusServer.ServerInfo):
        return super().on_holding_registers_change(address, from_value, to_value, srv_info)

    def get_holding_registers(self, address, number=1, srv_info:ModbusServer.ServerInfo | None=None):
        if srv_info and srv_info.client.address != self._allowed_ip:
            # print(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            raise ConnectionRefusedError(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            return None
        return super().get_holding_registers(address, number, srv_info)

    def get_coils(self, address, number=1, srv_info:ModbusServer.ServerInfo | None=None):
        if srv_info and srv_info.client.address != self._allowed_ip:
            # print(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            raise ConnectionRefusedError(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            return None
        return super().get_coils(address, number, srv_info)

    def get_discrete_inputs(self, address, number=1, srv_info:ModbusServer.ServerInfo | None=None):
        if srv_info and srv_info.client.address != self._allowed_ip:
            # print(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            raise ConnectionRefusedError(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            return None
        return super().get_discrete_inputs(address, number, srv_info)

    def get_input_registers(self, address, number=1, srv_info:ModbusServer.ServerInfo | None=None):
        if srv_info and srv_info.client.address != self._allowed_ip:
            # print(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            raise ConnectionRefusedError(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            return None
        return super().get_input_registers(address, number, srv_info)

    def set_coils(self, address, bit_list, srv_info:ModbusServer.ServerInfo | None=None):
        if srv_info and srv_info.client.address != self._allowed_ip:
            # print(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            raise ConnectionRefusedError(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            return None
        return super().set_coils(address, bit_list, srv_info)

    def set_holding_registers(self, address, word_list, srv_info:ModbusServer.ServerInfo | None=None):

        # if srv_info:
        #     self.client_info = srv_info.client
        #     if self.client_info != self._allowed_ip:
        #         self.ping_allowed = False
        #         return
        #     else:
        #         self.ping_allowed = True

        if srv_info and srv_info.client.address != self._allowed_ip:
            self.client_info = srv_info.client
            # print(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            self.ping_allowed = False
            raise ConnectionRefusedError(f"Modbus server connection to ip '{srv_info.client.address}' is not allowed")
            return None
        
        self.ping_allowed = True
        return super().set_holding_registers(address, word_list, srv_info)
