from pyModbusTCP.server import DataBank
from src.utils.modbus_regs import coils_regs, dig_inputs_regs

class MB_DataBank(DataBank):
    def __init__(self, coils_size=65536, coils_default_value=False, d_inputs_size=65536, d_inputs_default_value=False, h_regs_size=65536, h_regs_default_value=0, i_regs_size=65536, i_regs_default_value=0, virtual_mode=False):
        super().__init__(coils_size, coils_default_value, d_inputs_size, d_inputs_default_value, h_regs_size, h_regs_default_value, i_regs_size, i_regs_default_value, virtual_mode)

        self.handshake = False

    def on_coils_change(self, address, from_value, to_value, srv_info):
        # print("-------------------")
        # print(f"Coil recebida:\n Endereço: {address}\n Valor antigo: {from_value}\n Valor atual: {to_value}")
        # print("-------------------")
        
        # if address == coils_regs.RX_ALM.ADDRESS:
        #     self.set_discrete_inputs(dig_inputs_regs.TX_ALM.ADDRESS, [to_value])

        # match address:
        #     case coils_regs.RX_ALM.ADDRESS:
        #         self.set_discrete_inputs(dig_inputs_regs.TX_ALM.ADDRESS, [to_value])
        #     case coils_regs.RX_EO:
        #         self.set_discrete_inputs(dig_inputs_regs.TX_EO, [to_value])
        #     case coils_regs.RX_V15:
        #         self.set_discrete_inputs(dig_inputs_regs.TX_V15, [to_value])
        #     case coils_regs.RX_V44:
        #         self.set_discrete_inputs(dig_inputs_regs.TX_V44, [to_value])
        #     case coils_regs.RX_V46:
        #         self.set_discrete_inputs(dig_inputs_regs.TX_V46, [to_value])
            
            
        # self.handshake = coils_regs.HANDSHAKE

        # if coils_regs.RX_V20.ADDRESS <= address < (coils_regs.RX_V20.ADDRESS + coils_regs.RX_V20.SIZE):
        #     self.set_discrete_inputs(address + 723, [to_value])

        return super().on_coils_change(address, from_value, to_value, srv_info)
        