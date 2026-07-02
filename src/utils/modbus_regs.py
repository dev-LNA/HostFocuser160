from typing import NamedTuple
from enum import Enum, IntEnum, StrEnum, IntFlag, auto

class DB_size(IntEnum):
    COIL_FIRST_ADDRESS=1
    COIL_LAST_ADDRESS=668
    DI_FIRST_ADDRESS=761
    DI_LAST_ADDRESS=1443
    HR_FIRST_ADDRESS=1
    HR_LAST_ADDRESS=69

class RegType(Enum):
    COIL=0
    DISCRETE_INPUT=1
    INPUT_REGISTER=2
    HOLDING_REGISTER=3

class RegsInfo(NamedTuple):
    TAG: str
    ADDRESS: int
    SIZE: int
    TYPE: RegType


class HoldingRegs(NamedTuple):
# == REGISTROS DO CLP == #
    RX_PACKSTATUS: RegsInfo
    RX_EX: RegsInfo
    RX_MST: RegsInfo
    RX_SASTAT: RegsInfo
    RX_V20: RegsInfo
    RX_V50: RegsInfo
    RX_V71: RegsInfo
    RX_V74: RegsInfo
    RX_V75: RegsInfo
    RX_V76: RegsInfo
    RX_V77: RegsInfo
    RX_V78: RegsInfo
    RX_V79: RegsInfo
    RX_V80: RegsInfo
    RX_V81: RegsInfo
    RX_V82: RegsInfo
    RX_V83: RegsInfo
    RX_TCPRTMO: RegsInfo
    RX_TCPCYCLE: RegsInfo
    RX_TCPMBTMO: RegsInfo
    RX_TCPKATMO: RegsInfo
    TX_ALC: RegsInfo
    RX_V90: RegsInfo
    RX_V92: RegsInfo
    RX_PACKOK: RegsInfo
# == REGISTROS DO SERVIDOR == #
    TX_V20: RegsInfo
    TX_V71: RegsInfo
    TX_V74: RegsInfo
    TX_V75: RegsInfo
    TX_V76: RegsInfo
    TX_V77: RegsInfo
    TX_V78: RegsInfo
    TX_V79: RegsInfo
    TX_V80: RegsInfo
    TX_V81: RegsInfo
    TX_V82: RegsInfo
    TX_V83: RegsInfo
    TX_TCPRTMO: RegsInfo
    TX_TCPCYCLE: RegsInfo
    TX_TCPMBTMO: RegsInfo
    TX_TCPKATMO: RegsInfo
    TX_PACKCMDS: RegsInfo

# Holding register size given in words (16 bits)
holding_regs = HoldingRegs(
    RX_PACKSTATUS=RegsInfo(TAG="RX_PACKSTATUS", ADDRESS=1, SIZE=1, TYPE=RegType.HOLDING_REGISTER),
    RX_EX=RegsInfo("RX_EX", 2, 2, RegType.HOLDING_REGISTER),
    RX_MST=RegsInfo("RX_MST", 4, 2, RegType.HOLDING_REGISTER),
    RX_SASTAT=RegsInfo("RX_SASTAT", 6, 2, RegType.HOLDING_REGISTER),
    RX_V20=RegsInfo("RX_V20", 8, 2, RegType.HOLDING_REGISTER),
    RX_V50=RegsInfo("RX_V50", 10, 1, RegType.HOLDING_REGISTER),
    RX_V71=RegsInfo("RX_V71", 11, 2, RegType.HOLDING_REGISTER),
    RX_V74=RegsInfo("RX_V74", 13, 1, RegType.HOLDING_REGISTER),
    RX_V75=RegsInfo("RX_V75", 14, 1, RegType.HOLDING_REGISTER),
    RX_V76=RegsInfo("RX_V76", 15, 1, RegType.HOLDING_REGISTER),
    RX_V77=RegsInfo("RX_V77", 16, 1, RegType.HOLDING_REGISTER),
    RX_V78=RegsInfo("RX_V78", 17, 1, RegType.HOLDING_REGISTER),
    RX_V79=RegsInfo("RX_V79", 18, 1, RegType.HOLDING_REGISTER),
    RX_V80=RegsInfo("RX_V80", 19, 1, RegType.HOLDING_REGISTER),
    RX_V81=RegsInfo("RX_V81", 20, 1, RegType.HOLDING_REGISTER),
    RX_V82=RegsInfo("RX_V82", 21, 1, RegType.HOLDING_REGISTER),
    RX_V83=RegsInfo("RX_V83", 22, 2, RegType.HOLDING_REGISTER),
    RX_TCPRTMO=RegsInfo("RX_TCPRTMO", 24, 1, RegType.HOLDING_REGISTER),
    RX_TCPCYCLE=RegsInfo("RX_TCPCYCLE", 25, 1, RegType.HOLDING_REGISTER),
    RX_TCPMBTMO=RegsInfo("RX_TCPMBTMO", 26, 1, RegType.HOLDING_REGISTER),
    RX_TCPKATMO=RegsInfo("RX_TCPKATMO", 27, 1, RegType.HOLDING_REGISTER),
    TX_ALC=RegsInfo("TX_ALC", 28, 1, RegType.HOLDING_REGISTER),
    RX_V90=RegsInfo("RX_V90", 29, 1, RegType.HOLDING_REGISTER),
    RX_V92=RegsInfo("RX_V92", 30, 1, RegType.HOLDING_REGISTER),
    RX_PACKOK=RegsInfo("RX_PACKOK", 31, 1, RegType.HOLDING_REGISTER),
    TX_V20=RegsInfo("TX_V20", 50, 2, RegType.HOLDING_REGISTER),
    TX_V71=RegsInfo("TX_V71", 52, 1, RegType.HOLDING_REGISTER),
    TX_V74=RegsInfo("TX_V74", 53, 1, RegType.HOLDING_REGISTER),
    TX_V75=RegsInfo("TX_V75", 54, 1, RegType.HOLDING_REGISTER),
    TX_V76=RegsInfo("TX_V76", 55, 1, RegType.HOLDING_REGISTER),
    TX_V77=RegsInfo("TX_V77", 56, 1, RegType.HOLDING_REGISTER),
    TX_V78=RegsInfo("TX_V78", 57, 1, RegType.HOLDING_REGISTER),
    TX_V79=RegsInfo("TX_V79", 58, 1, RegType.HOLDING_REGISTER),
    TX_V80=RegsInfo("TX_V80", 59, 1, RegType.HOLDING_REGISTER),
    TX_V81=RegsInfo("TX_V81", 60, 1, RegType.HOLDING_REGISTER),
    TX_V82=RegsInfo("TX_V82", 61, 1, RegType.HOLDING_REGISTER),
    TX_V83=RegsInfo("TX_V83", 62, 2, RegType.HOLDING_REGISTER),
    TX_TCPRTMO=RegsInfo("TX_TCPRTMO", 64, 1, RegType.HOLDING_REGISTER),
    TX_TCPCYCLE=RegsInfo("TX_TCPCYCLE", 65, 1, RegType.HOLDING_REGISTER),
    TX_TCPMBTMO=RegsInfo("TX_TCPMBTMO", 66, 1, RegType.HOLDING_REGISTER),
    TX_TCPKATMO=RegsInfo("TX_TCPKATMO", 67, 1, RegType.HOLDING_REGISTER),
    TX_PACKCMDS=RegsInfo("TX_PACKCMDS", 68, 1, RegType.HOLDING_REGISTER)
)

class PackStatusFlags(IntFlag):
    RX_ALM = 0x0001
    RX_EO = 0x0002
    RX_V15 = 0x0004
    RX_V44 = 0x0008
    RX_V46 = 0x0010
    HANDSHAKE = 0x0020

class PackCMDFlags(IntFlag):
    TX_AX = 0x0001
    TX_GS1 = 0x0002
    TX_GS20 = 0x0004
    TX_GS21 = 0x0008
    TX_GS29 = 0x0010
    TX_GS30 = 0x0020
    TX_MOF = 0x0040
    TX_MON = 0x0080
    TX_PDB = 0x0100
    TX_V42 = 0x0200
    TX_SET = 0x0400

class CoilsRegs(NamedTuple):
    RX_ALM: RegsInfo
    RX_EO: RegsInfo
    RX_V15: RegsInfo
    RX_V44: RegsInfo
    RX_V46: RegsInfo
    RX_EX: RegsInfo
    RX_MST: RegsInfo
    RX_SASTAT: RegsInfo
    RX_V20: RegsInfo
    RX_V50: RegsInfo
    RX_V71: RegsInfo
    RX_V74: RegsInfo
    RX_V75: RegsInfo
    RX_V76: RegsInfo
    RX_V77: RegsInfo
    RX_V78: RegsInfo
    RX_V79: RegsInfo
    RX_V80: RegsInfo
    RX_V81: RegsInfo
    RX_V82: RegsInfo
    RX_V83: RegsInfo
    OK: RegsInfo
    NOK: RegsInfo
    RX_IP_A: RegsInfo
    RX_IP_B: RegsInfo
    RX_IP_C: RegsInfo
    RX_IP_D: RegsInfo
    HANDSHAKE: RegsInfo
    RX_CGT_A: RegsInfo
    RX_CGT_B: RegsInfo
    RX_CGT_C: RegsInfo
    RX_CGT_D: RegsInfo
    RX_CMK_A: RegsInfo
    RX_CMK_B: RegsInfo
    RX_CMK_C: RegsInfo
    RX_CMK_D: RegsInfo
    RX_WRITTING: RegsInfo
    RX_READING: RegsInfo
    RX_SHDW_WAIT: RegsInfo
    RX_SHDW_BUSY: RegsInfo
    RX_ALC: RegsInfo
    RX_V90: RegsInfo
    RX_V92: RegsInfo

coils_regs = CoilsRegs(
    RX_ALM=RegsInfo(TAG="RX_ALM", ADDRESS=DB_size.COIL_FIRST_ADDRESS, SIZE=1, TYPE=RegType.COIL),
    RX_EO=RegsInfo("RX_EO", 2, 1, RegType.COIL),
    RX_V15=RegsInfo("RX_V15", 3, 1, RegType.COIL),
    RX_V44=RegsInfo("RX_V44", 4, 1, RegType.COIL),
    RX_V46=RegsInfo("RX_V46", 5, 1, RegType.COIL),
    RX_EX=RegsInfo("RX_EX", 6, 32, RegType.COIL),
    RX_MST=RegsInfo("RX_MST", 38, 32, RegType.COIL),
    RX_SASTAT=RegsInfo("RX_SASTAT", 70, 32, RegType.COIL),
    RX_V20=RegsInfo("RX_V20", 102, 32, RegType.COIL),
    RX_V50=RegsInfo("RX_V50", 134, 32, RegType.COIL),
    RX_V71=RegsInfo("RX_V71", 166, 32, RegType.COIL),
    RX_V74=RegsInfo("RX_V74", 198, 32, RegType.COIL),
    RX_V75=RegsInfo("RX_V75", 230, 32, RegType.COIL),
    RX_V76=RegsInfo("RX_V76", 262, 32, RegType.COIL),
    RX_V77=RegsInfo("RX_V77", 294, 32, RegType.COIL),
    RX_V78=RegsInfo("RX_V78", 326, 32, RegType.COIL),
    RX_V79=RegsInfo("RX_V79", 358, 32, RegType.COIL),
    RX_V80=RegsInfo("RX_V80", 390, 32, RegType.COIL),
    RX_V81=RegsInfo("RX_V81", 422, 32, RegType.COIL),
    RX_V82=RegsInfo("RX_V82", 454, 32, RegType.COIL),
    RX_V83=RegsInfo("RX_V83", 486, 32, RegType.COIL),
    OK=RegsInfo("OK", 518, 1, RegType.COIL),
    NOK=RegsInfo("NOK", 519, 1, RegType.COIL),
    RX_IP_A=RegsInfo("RX_IP_A", 520, 8, RegType.COIL),
    RX_IP_B=RegsInfo("RX_IP_B", 528, 8, RegType.COIL),
    RX_IP_C=RegsInfo("RX_IP_C", 536, 8, RegType.COIL),
    RX_IP_D=RegsInfo("RX_IP_D", 544, 8, RegType.COIL),
    HANDSHAKE=RegsInfo("HANDSHAKE", 552, 1, RegType.COIL),
    RX_CGT_A=RegsInfo("RX_CGT_A", 553, 8, RegType.COIL),
    RX_CGT_B=RegsInfo("RX_CGT_B", 561, 8, RegType.COIL),
    RX_CGT_C=RegsInfo("RX_CGT_C", 569, 8, RegType.COIL),
    RX_CGT_D=RegsInfo("RX_CGT_D", 577, 8, RegType.COIL),
    RX_CMK_A=RegsInfo("RX_CMK_A", 585, 8, RegType.COIL),
    RX_CMK_B=RegsInfo("RX_CMK_B", 593, 8, RegType.COIL),
    RX_CMK_C=RegsInfo("RX_CMK_C", 601, 8, RegType.COIL),
    RX_CMK_D=RegsInfo("RX_CMK_D", 609, 8, RegType.COIL),
    RX_WRITTING=RegsInfo("RX_WRITTING", 617, 1, RegType.COIL),      # RX_WAIT
    RX_READING=RegsInfo("RX_READING", 618, 1, RegType.COIL),       # RX_BUSY
    RX_SHDW_WAIT=RegsInfo("RX_SHDW_WAIT", 619, 1, RegType.COIL),
    RX_SHDW_BUSY=RegsInfo("RX_SHDW_BUSY", 620, 1, RegType.COIL),
    RX_ALC=RegsInfo("RX_ALC", 621, 32, RegType.COIL),
    RX_V90=RegsInfo("RX_V90", 653, 8, RegType.COIL),
    RX_V92=RegsInfo("RX_V92", 661, 8, RegType.COIL)
)

class DigInputsRegs(NamedTuple):
    TX_CGT_A: RegsInfo
    TX_CGT_B: RegsInfo
    TX_CGT_C: RegsInfo
    TX_CGT_D: RegsInfo
    TX_CMK_A: RegsInfo 
    TX_CMK_B: RegsInfo
    TX_CMK_C: RegsInfo
    TX_CMK_D: RegsInfo
    TX_V20: RegsInfo
    TX_V71: RegsInfo
    TX_V74: RegsInfo
    TX_V75: RegsInfo
    TX_V76: RegsInfo
    TX_V77: RegsInfo
    TX_V78: RegsInfo
    TX_V79: RegsInfo
    TX_V80: RegsInfo
    TX_V81: RegsInfo
    TX_V82: RegsInfo
    TX_V83: RegsInfo
    TX_IP_A: RegsInfo
    TX_IP_B: RegsInfo
    TX_IP_C: RegsInfo
    TX_IP_D: RegsInfo
    TX_PR: RegsInfo 
    TX_AX: RegsInfo
    TX_GS1: RegsInfo
    TX_GS5: RegsInfo
    TX_GS20: RegsInfo
    TX_GS21: RegsInfo
    TX_GS29: RegsInfo
    TX_GS30: RegsInfo
    TX_IST: RegsInfo
    TX_MOF: RegsInfo
    TX_MON: RegsInfo
    TX_PDB: RegsInfo
    TX_RCLP: RegsInfo
    TX_V42: RegsInfo
    TX_ALM: RegsInfo
    TX_EO: RegsInfo
    TX_V15: RegsInfo
    TX_V44: RegsInfo
    TX_V46: RegsInfo
    TX_EX: RegsInfo
    TX_MST: RegsInfo
    TX_SASTAT: RegsInfo
    TX_V50: RegsInfo
    OK: RegsInfo
    NOK: RegsInfo
    HANDSHAKE: RegsInfo
    TX_WRITTING: RegsInfo
    TX_READING: RegsInfo
    TX_SHDW_WAIT: RegsInfo
    TX_SHDW_BUSY: RegsInfo
    TX_ALC: RegsInfo
    TX_V90: RegsInfo
    TX_V92: RegsInfo
    TX_SVON: RegsInfo
    TX_DUMMY: RegsInfo



dig_inputs_regs = DigInputsRegs(
    TX_CGT_A=RegsInfo(TAG="TX_CGT_A", ADDRESS=DB_size.DI_FIRST_ADDRESS, SIZE=8, TYPE=RegType.DISCRETE_INPUT), 
    TX_CGT_B=RegsInfo("TX_CGT_B", 769, 8, RegType.DISCRETE_INPUT),
    TX_CGT_C=RegsInfo("TX_CGT_C", 777, 8, RegType.DISCRETE_INPUT), 
    TX_CGT_D=RegsInfo("TX_CGT_D", 785, 8, RegType.DISCRETE_INPUT),
    TX_CMK_A=RegsInfo("TX_CMK_A", 793, 8, RegType.DISCRETE_INPUT), 
    TX_CMK_B=RegsInfo("TX_CMK_B", 801, 8, RegType.DISCRETE_INPUT),
    TX_CMK_C=RegsInfo("TX_CMK_C", 809, 8, RegType.DISCRETE_INPUT), 
    TX_CMK_D=RegsInfo("TX_CMK_D", 817, 8, RegType.DISCRETE_INPUT),
    TX_V20=RegsInfo("TX_V20", 825, 32, RegType.DISCRETE_INPUT),
    TX_V71=RegsInfo("TX_V71", 857, 32, RegType.DISCRETE_INPUT),
    TX_V74=RegsInfo("TX_V74", 889, 32, RegType.DISCRETE_INPUT),
    TX_V75=RegsInfo("TX_V75", 921, 32, RegType.DISCRETE_INPUT),
    TX_V76=RegsInfo("TX_V76", 953, 32, RegType.DISCRETE_INPUT),
    TX_V77=RegsInfo("TX_V77", 985, 32, RegType.DISCRETE_INPUT),
    TX_V78=RegsInfo("TX_V78", 1017, 32, RegType.DISCRETE_INPUT),
    TX_V79=RegsInfo("TX_V79", 1049, 32, RegType.DISCRETE_INPUT),
    TX_V80=RegsInfo("TX_V80", 1081, 32, RegType.DISCRETE_INPUT),
    TX_V81=RegsInfo("TX_V81", 1113, 32, RegType.DISCRETE_INPUT),
    TX_V82=RegsInfo("TX_V82", 1145, 32, RegType.DISCRETE_INPUT),
    TX_V83=RegsInfo("TX_V83", 1177, 32, RegType.DISCRETE_INPUT),
    TX_IP_A=RegsInfo("TX_IP_A", 1209, 8, RegType.DISCRETE_INPUT),
    TX_IP_B=RegsInfo("TX_IP_B", 1217, 8, RegType.DISCRETE_INPUT),
    TX_IP_C=RegsInfo("TX_IP_C", 1225, 8, RegType.DISCRETE_INPUT),
    TX_IP_D=RegsInfo("TX_IP_D", 1233, 8, RegType.DISCRETE_INPUT),
    TX_PR=RegsInfo("TX_PR", 1241, 1, RegType.DISCRETE_INPUT),
    TX_AX=RegsInfo("TX_AX", 1242, 1, RegType.DISCRETE_INPUT),
    TX_GS1=RegsInfo("TX_GS1", 1243, 1, RegType.DISCRETE_INPUT),
    TX_GS5=RegsInfo("TX_GS5", 1244, 1, RegType.DISCRETE_INPUT),
    TX_GS20=RegsInfo("TX_GS20", 1245, 1, RegType.DISCRETE_INPUT),
    TX_GS21=RegsInfo("TX_GS21", 1246, 1, RegType.DISCRETE_INPUT),
    TX_GS29=RegsInfo("TX_GS29", 1247, 1, RegType.DISCRETE_INPUT),
    TX_GS30=RegsInfo("TX_GS30", 1248, 1, RegType.DISCRETE_INPUT),
    TX_IST=RegsInfo("TX_IST", 1249, 1, RegType.DISCRETE_INPUT),
    TX_MOF=RegsInfo("TX_MOF", 1250, 1, RegType.DISCRETE_INPUT),
    TX_MON=RegsInfo("TX_MON", 1251, 1, RegType.DISCRETE_INPUT),
    TX_PDB=RegsInfo("TX_PDB", 1252, 1, RegType.DISCRETE_INPUT),
    TX_RCLP=RegsInfo("TX_RCLP", 1253, 1, RegType.DISCRETE_INPUT),
    TX_V42=RegsInfo("TX_V42", 1254, 1, RegType.DISCRETE_INPUT),
    TX_ALM=RegsInfo("TX_ALM", 1255, 1, RegType.DISCRETE_INPUT),
    TX_EO=RegsInfo("TX_EO", 1256, 1, RegType.DISCRETE_INPUT),
    TX_V15=RegsInfo("TX_V15", 1257, 1, RegType.DISCRETE_INPUT),
    TX_V44=RegsInfo("TX_V44", 1258, 1, RegType.DISCRETE_INPUT),
    TX_V46=RegsInfo("TX_V46", 1259, 1, RegType.DISCRETE_INPUT),
    TX_EX=RegsInfo("TX_EX", 1260, 32, RegType.DISCRETE_INPUT),
    TX_MST=RegsInfo("TX_MST", 1292, 32, RegType.DISCRETE_INPUT),
    TX_SASTAT=RegsInfo("TX_SASTAT", 1324, 32, RegType.DISCRETE_INPUT),
    TX_V50=RegsInfo("TX_V50", 1356, 32, RegType.DISCRETE_INPUT),
    OK=RegsInfo("OK", 1388, 1, RegType.DISCRETE_INPUT),
    NOK=RegsInfo("NOK", 1389, 1, RegType.DISCRETE_INPUT),
    HANDSHAKE=RegsInfo("HANDSHAKE", 1390, 1, RegType.DISCRETE_INPUT),
    TX_WRITTING=RegsInfo("TX_WRITTING", 1391, 1, RegType.DISCRETE_INPUT),       #TX_WAIT
    TX_READING=RegsInfo("TX_READING", 1392, 1, RegType.DISCRETE_INPUT),       #TX_BUSY
    TX_SHDW_WAIT=RegsInfo("TX_SHDW_WAIT", 1393, 1, RegType.DISCRETE_INPUT),
    TX_SHDW_BUSY=RegsInfo("TX_SHDW_BUSY", 1394, 1, RegType.DISCRETE_INPUT),
    TX_ALC=RegsInfo("TX_ALC", 1395, 32, RegType.DISCRETE_INPUT),
    TX_V90=RegsInfo("TX_V90", 1427, 8, RegType.DISCRETE_INPUT),
    TX_V92=RegsInfo("TX_V92", 1435, 8, RegType.DISCRETE_INPUT),
    TX_SVON=RegsInfo("TX_SVON", 1443, 1, RegType.DISCRETE_INPUT),
    TX_DUMMY=RegsInfo("TX_DUMMY", 0, 32, RegType.DISCRETE_INPUT),
)

class mirrorMapping(NamedTuple):
    # ORIGIN: str
    ORIGIN: RegsInfo
    RESPONSE: RegsInfo


class CLP_Vars(NamedTuple):
    """Registers that are owned by the CLP and the 
    server must mirror so that the CLP can confirm
    the receive"""

    RX_ALM: mirrorMapping
    RX_EO: mirrorMapping
    RX_V15: mirrorMapping
    RX_V44: mirrorMapping
    RX_V46: mirrorMapping
    RX_EX: mirrorMapping
    RX_MST: mirrorMapping
    RX_SASTAT: mirrorMapping
    RX_V50: mirrorMapping
    OK: mirrorMapping
    NOK: mirrorMapping
    HANDSHAKE: mirrorMapping
    RX_ALC: mirrorMapping
    RX_V90: mirrorMapping
    RX_V92: mirrorMapping

# CLP_Owned = CLP_Vars(
#     RX_ALM = mirrorMapping("RX_ALM", dig_inputs_regs.TX_ALM),
#     RX_EO = mirrorMapping("RX_EO", dig_inputs_regs.TX_EO),
#     RX_V15 = mirrorMapping("RX_V15", dig_inputs_regs.TX_V15),
#     RX_V44 = mirrorMapping("RX_V44", dig_inputs_regs.TX_V44),
#     RX_V46 = mirrorMapping("RX_V46", dig_inputs_regs.TX_V46),
#     RX_EX = mirrorMapping("RX_EX", dig_inputs_regs.TX_EX),
#     RX_MST = mirrorMapping("RX_MST", dig_inputs_regs.TX_MST),
#     RX_SASTAT = mirrorMapping("RX_SASTAT", dig_inputs_regs.TX_SASTAT),
#     RX_V50 = mirrorMapping("RX_V50", dig_inputs_regs.TX_V50),
#     OK = mirrorMapping("OK", dig_inputs_regs.OK),
#     NOK = mirrorMapping("NOK", dig_inputs_regs.NOK),
#     HANDSHAKE = mirrorMapping("HANDSHAKE", dig_inputs_regs.HANDSHAKE),
#     RX_ALC = mirrorMapping("RX_ALC", dig_inputs_regs.TX_ALC),
#     RX_V90 = mirrorMapping("RX_V90", dig_inputs_regs.TX_V90),
#     RX_V92 = mirrorMapping("RX_V92", dig_inputs_regs.TX_V92),
# )
CLP_Owned = CLP_Vars(
    RX_ALM = mirrorMapping(coils_regs.RX_ALM, dig_inputs_regs.TX_ALM),
    RX_EO = mirrorMapping(coils_regs.RX_EO, dig_inputs_regs.TX_EO),
    RX_V15 = mirrorMapping(coils_regs.RX_V15, dig_inputs_regs.TX_V15),
    RX_V44 = mirrorMapping(coils_regs.RX_V44, dig_inputs_regs.TX_V44),
    RX_V46 = mirrorMapping(coils_regs.RX_V46, dig_inputs_regs.TX_V46),
    RX_EX = mirrorMapping(coils_regs.RX_EX, dig_inputs_regs.TX_EX),
    RX_MST = mirrorMapping(coils_regs.RX_MST, dig_inputs_regs.TX_MST),
    RX_SASTAT = mirrorMapping(coils_regs.RX_SASTAT, dig_inputs_regs.TX_SASTAT),
    RX_V50 = mirrorMapping(coils_regs.RX_V50, dig_inputs_regs.TX_V50),
    OK = mirrorMapping(coils_regs.OK, dig_inputs_regs.OK),
    NOK = mirrorMapping(coils_regs.NOK, dig_inputs_regs.NOK),
    HANDSHAKE = mirrorMapping(coils_regs.HANDSHAKE, dig_inputs_regs.HANDSHAKE),
    RX_ALC = mirrorMapping(coils_regs.RX_ALC, dig_inputs_regs.TX_ALC),
    RX_V90 = mirrorMapping(coils_regs.RX_V90, dig_inputs_regs.TX_V90),
    RX_V92 = mirrorMapping(coils_regs.RX_V92, dig_inputs_regs.TX_V92),
)

class Param_Vars(NamedTuple):
    """Registers that represent CLP Parameters
    The CLP will mirror this values and the server must
    verify if the value was correctly received by the CLP"""

    TX_CGT_A: mirrorMapping
    TX_CGT_B: mirrorMapping
    TX_CGT_C: mirrorMapping
    TX_CGT_D: mirrorMapping
    TX_CMK_A: mirrorMapping
    TX_CMK_B: mirrorMapping
    TX_CMK_C: mirrorMapping
    TX_CMK_D: mirrorMapping
    TX_V20: mirrorMapping
    TX_V71: mirrorMapping
    TX_V74: mirrorMapping
    TX_V75: mirrorMapping
    TX_V76: mirrorMapping
    TX_V77: mirrorMapping
    TX_V78: mirrorMapping
    TX_V79: mirrorMapping
    TX_V80: mirrorMapping
    TX_V81: mirrorMapping
    TX_V82: mirrorMapping
    TX_V83: mirrorMapping
    TX_IP_A: mirrorMapping
    TX_IP_B: mirrorMapping
    TX_IP_C: mirrorMapping
    TX_IP_D: mirrorMapping

# param_vars = Param_Vars(
#     TX_CGT_A = mirrorMapping("TX_CGT_A", coils_regs.RX_CGT_A),
#     TX_CGT_B = mirrorMapping("TX_CGT_B", coils_regs.RX_CGT_B),
#     TX_CGT_C = mirrorMapping("TX_CGT_C", coils_regs.RX_CGT_C),
#     TX_CGT_D = mirrorMapping("TX_CGT_D", coils_regs.RX_CGT_D),
#     TX_CMK_A = mirrorMapping("TX_CMK_A", coils_regs.RX_CMK_A),
#     TX_CMK_B = mirrorMapping("TX_CMK_B", coils_regs.RX_CMK_B),
#     TX_CMK_C = mirrorMapping("TX_CMK_C", coils_regs.RX_CMK_C),
#     TX_CMK_D = mirrorMapping("TX_CMK_D", coils_regs.RX_CMK_D),
#     TX_V20 = mirrorMapping("TX_V20", coils_regs.RX_V20),
#     TX_V71 = mirrorMapping("TX_V71", coils_regs.RX_V71),
#     TX_V74 = mirrorMapping("TX_V74", coils_regs.RX_V74),
#     TX_V75 = mirrorMapping("TX_V75", coils_regs.RX_V75),
#     TX_V76 = mirrorMapping("TX_V76", coils_regs.RX_V76),
#     TX_V77 = mirrorMapping("TX_V77", coils_regs.RX_V77),
#     TX_V78 = mirrorMapping("TX_V78", coils_regs.RX_V78),
#     TX_V79 = mirrorMapping("TX_V79", coils_regs.RX_V79),
#     TX_V80 = mirrorMapping("TX_V80", coils_regs.RX_V80),
#     TX_V81 = mirrorMapping("TX_V81", coils_regs.RX_V81),
#     TX_V82 = mirrorMapping("TX_V82", coils_regs.RX_V82),
#     TX_V83 = mirrorMapping("TX_V83", coils_regs.RX_V83),
#     TX_IP_A = mirrorMapping("TX_IP_A", coils_regs.RX_IP_A),
#     TX_IP_B = mirrorMapping("TX_IP_B", coils_regs.RX_IP_B),
#     TX_IP_C = mirrorMapping("TX_IP_C", coils_regs.RX_IP_C),
#     TX_IP_D = mirrorMapping("TX_IP_D", coils_regs.RX_IP_D)
# )

param_vars = Param_Vars(
    TX_CGT_A = mirrorMapping(dig_inputs_regs.TX_CGT_A, coils_regs.RX_CGT_A),
    TX_CGT_B = mirrorMapping(dig_inputs_regs.TX_CGT_B, coils_regs.RX_CGT_B),
    TX_CGT_C = mirrorMapping(dig_inputs_regs.TX_CGT_C, coils_regs.RX_CGT_C),
    TX_CGT_D = mirrorMapping(dig_inputs_regs.TX_CGT_D, coils_regs.RX_CGT_D),
    TX_CMK_A = mirrorMapping(dig_inputs_regs.TX_CMK_A, coils_regs.RX_CMK_A),
    TX_CMK_B = mirrorMapping(dig_inputs_regs.TX_CMK_B, coils_regs.RX_CMK_B),
    TX_CMK_C = mirrorMapping(dig_inputs_regs.TX_CMK_C, coils_regs.RX_CMK_C),
    TX_CMK_D = mirrorMapping(dig_inputs_regs.TX_CMK_D, coils_regs.RX_CMK_D),
    TX_V20 = mirrorMapping(dig_inputs_regs.TX_V20, coils_regs.RX_V20),
    TX_V71 = mirrorMapping(dig_inputs_regs.TX_V71, coils_regs.RX_V71),
    TX_V74 = mirrorMapping(dig_inputs_regs.TX_V74, coils_regs.RX_V74),
    TX_V75 = mirrorMapping(dig_inputs_regs.TX_V75, coils_regs.RX_V75),
    TX_V76 = mirrorMapping(dig_inputs_regs.TX_V76, coils_regs.RX_V76),
    TX_V77 = mirrorMapping(dig_inputs_regs.TX_V77, coils_regs.RX_V77),
    TX_V78 = mirrorMapping(dig_inputs_regs.TX_V78, coils_regs.RX_V78),
    TX_V79 = mirrorMapping(dig_inputs_regs.TX_V79, coils_regs.RX_V79),
    TX_V80 = mirrorMapping(dig_inputs_regs.TX_V80, coils_regs.RX_V80),
    TX_V81 = mirrorMapping(dig_inputs_regs.TX_V81, coils_regs.RX_V81),
    TX_V82 = mirrorMapping(dig_inputs_regs.TX_V82, coils_regs.RX_V82),
    TX_V83 = mirrorMapping(dig_inputs_regs.TX_V83, coils_regs.RX_V83),
    TX_IP_A = mirrorMapping(dig_inputs_regs.TX_IP_A, coils_regs.RX_IP_A),
    TX_IP_B = mirrorMapping(dig_inputs_regs.TX_IP_B, coils_regs.RX_IP_B),
    TX_IP_C = mirrorMapping(dig_inputs_regs.TX_IP_C, coils_regs.RX_IP_C),
    TX_IP_D = mirrorMapping(dig_inputs_regs.TX_IP_D, coils_regs.RX_IP_D)
)

#ALC, MST e SASTAT
class TwosComplementReg(StrEnum):
    """Coils that must be interpreted as values
    in twos complement"""
    RX_EX = auto()
    RX_V20 = auto()
    RX_V50 = auto()
    RX_V71 = auto()
    RX_V74 = auto()
    RX_V75 = auto()
    RX_V76 = auto()
    RX_V77 = auto()
    RX_V78 = auto()
    RX_V79 = auto()
    RX_V80 = auto()
    RX_V81 = auto()
    RX_V82 = auto()
    RX_V83 = auto()

