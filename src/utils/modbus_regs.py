from typing import NamedTuple
from enum import Enum

class RegType(Enum):
    COIL=0,
    DISCRETE_INPUT=1,
    INPUT_REGISTER=2,
    HOLDING_REGISTER=3

class RegsInfo(NamedTuple):
    ADDRESS: int
    SIZE: int
    TYPE: RegType

class CoilsRegs(NamedTuple):
    RX_ALM: RegsInfo
    RX_EO: RegsInfo
    RX_V15: RegsInfo
    RX_V44: RegsInfo
    RX_V45: RegsInfo
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
    RX_83: RegsInfo
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

coils_regs = CoilsRegs(
    RX_ALM=RegsInfo(1, 1, RegType.COIL),
    RX_EO=RegsInfo(2, 1, RegType.COIL),
    RX_V15=RegsInfo(3, 1, RegType.COIL),
    RX_V44=RegsInfo(4, 1, RegType.COIL),
    RX_V45=RegsInfo(5, 1, RegType.COIL),
    RX_EX=RegsInfo(6, 32, RegType.COIL),
    RX_MST=RegsInfo(38, 32, RegType.COIL),
    RX_SASTAT=RegsInfo(70, 32, RegType.COIL),
    RX_V20=RegsInfo(102, 32, RegType.COIL),
    RX_V50=RegsInfo(134, 32, RegType.COIL),
    RX_V71=RegsInfo(166, 32, RegType.COIL),
    RX_V74=RegsInfo(198, 32, RegType.COIL),
    RX_V75=RegsInfo(230, 32, RegType.COIL),
    RX_V76=RegsInfo(262, 32, RegType.COIL),
    RX_V77=RegsInfo(294, 32, RegType.COIL),
    RX_V78=RegsInfo(326, 32, RegType.COIL),
    RX_V79=RegsInfo(358, 32, RegType.COIL),
    RX_V80=RegsInfo(390, 32, RegType.COIL),
    RX_V81=RegsInfo(422, 32, RegType.COIL),
    RX_V82=RegsInfo(454, 32, RegType.COIL),
    RX_83=RegsInfo(486, 32, RegType.COIL),
    OK=RegsInfo(518, 1, RegType.COIL),
    NOK=RegsInfo(519, 1, RegType.COIL),
    RX_IP_A=RegsInfo(520, 8, RegType.COIL),
    RX_IP_B=RegsInfo(528, 8, RegType.COIL),
    RX_IP_C=RegsInfo(537, 8, RegType.COIL),
    RX_IP_D=RegsInfo(545, 8, RegType.COIL),
    HANDSHAKE=RegsInfo(554, 1, RegType.COIL),
    RX_CGT_A=RegsInfo(555, 8, RegType.COIL),
    RX_CGT_B=RegsInfo(563, 8, RegType.COIL),
    RX_CGT_C=RegsInfo(571, 8, RegType.COIL),
    RX_CGT_D=RegsInfo(579, 8, RegType.COIL),
    RX_CMK_A=RegsInfo(587, 8, RegType.COIL),
    RX_CMK_B=RegsInfo(595, 8, RegType.COIL),
    RX_CMK_C=RegsInfo(603, 8, RegType.COIL),
    RX_CMK_D=RegsInfo(611, 8, RegType.COIL)
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
    TX_ALC: RegsInfo
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



dig_inputs_regs = DigInputsRegs(
    TX_CGT_A=RegsInfo(761, 8, RegType.DISCRETE_INPUT), 
    TX_CGT_B=RegsInfo(769, 8, RegType.DISCRETE_INPUT),
    TX_CGT_C=RegsInfo(777, 8, RegType.DISCRETE_INPUT), 
    TX_CGT_D=RegsInfo(785, 8, RegType.DISCRETE_INPUT),
    TX_CMK_A=RegsInfo(793, 8, RegType.DISCRETE_INPUT), 
    TX_CMK_B=RegsInfo(801, 8, RegType.DISCRETE_INPUT),
    TX_CMK_C=RegsInfo(809, 8, RegType.DISCRETE_INPUT), 
    TX_CMK_D=RegsInfo(817, 8, RegType.DISCRETE_INPUT),
    TX_V20=RegsInfo(825, 32, RegType.DISCRETE_INPUT),
    TX_V71=RegsInfo(857, 32, RegType.DISCRETE_INPUT),
    TX_V74=RegsInfo(889, 32, RegType.DISCRETE_INPUT),
    TX_V75=RegsInfo(921, 32, RegType.DISCRETE_INPUT),
    TX_V76=RegsInfo(953, 32, RegType.DISCRETE_INPUT),
    TX_V77=RegsInfo(985, 32, RegType.DISCRETE_INPUT),
    TX_V78=RegsInfo(1017, 32, RegType.DISCRETE_INPUT),
    TX_V79=RegsInfo(1049, 32, RegType.DISCRETE_INPUT),
    TX_V80=RegsInfo(1081, 32, RegType.DISCRETE_INPUT),
    TX_V81=RegsInfo(1113, 32, RegType.DISCRETE_INPUT),
    TX_V82=RegsInfo(1145, 32, RegType.DISCRETE_INPUT),
    TX_V83=RegsInfo(1177, 32, RegType.DISCRETE_INPUT),
    TX_IP_A=RegsInfo(1209, 8, RegType.DISCRETE_INPUT),
    TX_IP_B=RegsInfo(1217, 8, RegType.DISCRETE_INPUT),
    TX_IP_C=RegsInfo(1225, 8, RegType.DISCRETE_INPUT),
    TX_IP_D=RegsInfo(1233, 8, RegType.DISCRETE_INPUT),
    TX_ALC=RegsInfo(1241, 1, RegType.DISCRETE_INPUT),
    TX_AX=RegsInfo(1242, 1, RegType.DISCRETE_INPUT),
    TX_GS1=RegsInfo(1243, 1, RegType.DISCRETE_INPUT),
    TX_GS5=RegsInfo(1244, 1, RegType.DISCRETE_INPUT),
    TX_GS20=RegsInfo(1245, 1, RegType.DISCRETE_INPUT),
    TX_GS21=RegsInfo(1246, 1, RegType.DISCRETE_INPUT),
    TX_GS29=RegsInfo(1247, 1, RegType.DISCRETE_INPUT),
    TX_GS30=RegsInfo(1248, 1, RegType.DISCRETE_INPUT),
    TX_IST=RegsInfo(1249, 1, RegType.DISCRETE_INPUT),
    TX_MOF=RegsInfo(1250, 1, RegType.DISCRETE_INPUT),
    TX_MON=RegsInfo(1251, 1, RegType.DISCRETE_INPUT),
    TX_PDB=RegsInfo(1252, 1, RegType.DISCRETE_INPUT),
    TX_RCLP=RegsInfo(1253, 1, RegType.DISCRETE_INPUT),
    TX_V42=RegsInfo(1254, 1, RegType.DISCRETE_INPUT),
    TX_ALM=RegsInfo(1255, 1, RegType.DISCRETE_INPUT),
    TX_EO=RegsInfo(1256, 1, RegType.DISCRETE_INPUT),
    TX_V15=RegsInfo(1257, 1, RegType.DISCRETE_INPUT),
    TX_V44=RegsInfo(1258, 1, RegType.DISCRETE_INPUT),
    TX_V46=RegsInfo(1259, 1, RegType.DISCRETE_INPUT),
    TX_EX=RegsInfo(1260, 32, RegType.DISCRETE_INPUT),
    TX_MST=RegsInfo(1268, 32, RegType.DISCRETE_INPUT),
    TX_SASTAT=RegsInfo(1276, 32, RegType.DISCRETE_INPUT),
    TX_V50=RegsInfo(1284, 32, RegType.DISCRETE_INPUT),
    OK=RegsInfo(1292, 1, RegType.DISCRETE_INPUT),
    NOK=RegsInfo(1293, 1, RegType.DISCRETE_INPUT),
    HANDSHAKE=RegsInfo(1294, 1, RegType.DISCRETE_INPUT)
)