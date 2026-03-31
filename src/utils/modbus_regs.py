from typing import NamedTuple
from enum import Enum, IntEnum

class DB_size(IntEnum):
    COIL_FIRST_ADDRESS=1,
    COIL_LAST_ADDRES=617,
    DI_FIRST_ADDRESS=761
    DI_LAST_ADDRESS=1391

class RegType(Enum):
    COIL=0,
    DISCRETE_INPUT=1,
    INPUT_REGISTER=2,
    HOLDING_REGISTER=3

class RegsInfo(NamedTuple):
    TAG: str
    ADDRESS: int
    SIZE: int
    TYPE: RegType

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
    RX_WAIT: RegsInfo

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
    RX_WAIT=RegsInfo("RX_WAIT", DB_size.COIL_LAST_ADDRES, 1, RegType.COIL)
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
    TX_WAIT: RegsInfo



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
    TX_ALC=RegsInfo("TX_ALC", 1241, 1, RegType.DISCRETE_INPUT),
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
    TX_WAIT=RegsInfo("TX_WAIT", DB_size.DI_LAST_ADDRESS, 1, RegType.DISCRETE_INPUT)
)

class CLP_own(NamedTuple):
    RX_ALM: str
    RX_EO: str
    RX_V15: str
    RX_V44: str
    RX_V46: str
    RX_EX: str
    RX_MST: str
    RX_SASTAT: str
    RX_V50: str
    RX_OK: str
    RX_NOK: str
    HANDSHAKE: str
    RX_WAIT: str


CLP_managed_var_mirror = CLP_own(
    RX_ALM= "TX_ALM",
    RX_EO= "TX_EO",
    RX_V15= "TX_V15", 
    RX_V44= "TX_V44",
    RX_V46= "TX_V46",
    RX_EX= "TX_EX",
    RX_MST= "TX_MST",
    RX_SASTAT= "TX_SASTAT",
    RX_V50= "TX_V50",
    RX_OK= "TX_OK",
    RX_NOK= "TX_NOK",
    HANDSHAKE= "HANDSHAKE",
    RX_WAIT= "TX_WAIT",
)
