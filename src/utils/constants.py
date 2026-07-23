from collections import namedtuple
from enum import StrEnum, Enum, IntFlag, auto
from typing import NamedTuple, TypedDict
from dataclasses import dataclass
from threading import Timer

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.utils.modbus_regs import RegsInfo

#region GUI

class DynamicProperties(StrEnum):
    STATUS_LED = "statusLed"
    STATUS_BAR = "conStatusBar"

#endregion

#region GENERAL
Constants = namedtuple('Constants',
                        ['ID_FOCUSER_160', 
                         'ID_FOCUSER_IAG',
                         'ARCUS_DMX_ETH',
                         'AMP_MOTOR',
                         'INVALID_RESPONSE'])

constants = Constants(
    ID_FOCUSER_160="64", 
    ID_FOCUSER_IAG="100",
    ARCUS_DMX_ETH="64", 
    AMP_MOTOR="100",
    INVALID_RESPONSE=-9999999,     # If a problem occurs in the reading an invalid value is published
    ) 

@dataclass
class CommandTimeout():
    command: str
    timer: Timer

class TimeoutState(Enum):
    NO_TIMEOUT = auto()
    TIMEOUT = auto()
    WAIT_INFO = auto()

# Due to the mechanical mounting the relative positions must be converted to allow
# operators to use previously defined positions in the software
@dataclass
class Conversion():
    POSITION_VISUALIZATION: float = 1 #0.09885853    # Conversion from value to PUB and DISPLAY
    POSITION_COMMAND: float = 1 #1.011546     # Conversion from received command to value to be sent to the motor

class TimeDelays(float, Enum):
    RETRY_TIMEOUT = 0.2         # TODO: Colocar como configuração?
    WAIT_PARAM = 0.4            # Delay to ensure the parameter value is written to the CLP register before sending a related command
    WAIT_CLP_RESPONSE = 0.2 # 0.2     # Time waiting for OK/NOK from CLP
    WAIT_CLP_PROCESS = 0.2  # 0.2      # Time for CLP to process information   
    WAIT_CLP_MIRROR = 0.2   #0.1       # Time for CLP to mirror the value to the response register
    TIMEOUT_PARAM = 3.0                 # Timeout waiting for CLP to mirror parameters
    TIMEOUT_SET = 1.0                   # Timeout waiting for SET OK from CLP after sending a SET
    TIMEOUT_CMD = 3.0                   # Timeout waiting for CLP to respond to commands

class FocuserSignalsNames(StrEnum):
    LIM_SWITCH_MIN = auto()
    LIM_SWITCH_MAX = auto()
    INITIALIZED = "HOMING"
    MANUAL_MOVEMENT = auto()
    RUN_FOCUS_IN = "FOCUS IN"
    RUN_FOCUS_OUT = "FOCUS OUT"
    RUN_PARK = "PARK"
    STOPPED = ""

@dataclass
class FocuserHardwareStatus():
    lim_switch_min: bool = False
    lim_switch_max: bool = False
    initialized: bool = False
    manual_movement: bool = False
    movement_info: str = ""
    
#endregion


#region SERVER
class ServerJsonKeys(StrEnum):
    ABSOLUTE = 'absolute'
    ALARM = 'alarm'
    BROKER = 'broker'
    CMD = 'cmd'
    CMD_CLIENT_ID = 'clientId'
    CMD_CLIENT_TRANSACTION_ID = 'clientTransactionId'
    CMD_CLIENT_NAME = 'clientName'
    CMD_ACTION = 'action'
    CONNECTED = "connected"
    CONTROLLER = "controller"
    DEVICE = "device"
    ERROR = "error"
    HOMING = "homing"                  # Homing solicited
    INITIALIZED = "initialized"        # Homing finalized
    IS_MOVING = "isMoving"             # Executing a function inside the motor
    MAX_SPEED = "maxSpeed"
    MAX_STEP = "maxStep"
    POSITION = "position"
    TEMP_COMP = "tempComp"
    TEMP_COMP_AVAIABLE = "tempCompAvailable"
    TEMPERATURE = "temperature"
    TIMESTAMP = "timestamp"
    VERSION = "version"                                     #TODO: Pegar a versão do arquivo config.toml
    PARKING = "parking"                                     # Executing Parking
    DEVICE_IP = "device_IP"                                 # Motor IP
    DEVICE_ID = "device_ID"                                 # Motor ID
    DEVICE_FIRMWARE_VERSION = "device_Firmware_Version"     # Motor firmware version
    TIMEOUT = "timeout"                                     # Timeout
    PROCESSING = "processing"

class ServerParamsIdx(Enum):
    SERVER_IP=0
    PORT_PUB=auto()
    PORT_REP=auto()
    PUB_INTERVAL=auto()
    SUB_MASK=auto()
    GATEWAY_IP=auto()
    STARTUP=auto()
    STEP_OFFSET=auto()

#endregion

#region MOTOR
class MotorModels(StrEnum):
    ARCUS_DMX_ETH = 'DMX'
    AMP_MOTOR = 'AMP'

# The MotorParamIdx first value must be a continuation from ServerParamsIdx
class MotorParamsIdx(Enum):   
    MOTOR_IP=len(ServerParamsIdx)
    TCP_RETRANSMISSION_TIMEOUT=auto()
    TCP_COM_CYCLE_TIMEOUT=auto()
    TCP_MODBUS_TIMEOUT=auto()
    TCP_KEEP_ALIVE_TIMEOUT=auto()
    BACKLASH=auto()
    MAX_POS=auto()
    PARK_POS=auto()
    MAX_SPEED=auto()
    NORMAL_SPEED=auto()
    LOW_SPEED=auto()
    ACCELERATION=auto()
    DECELERATION=auto()
    IDLE_CURRENT=auto()
    RUN_CURRENT=auto()
    ACC_CURRENT=auto()
    CLP_AUTO_RESTART=auto()
    MOTOR_AUTO_RESTART=auto()


@dataclass
class MotorParameter():
    IDX: MotorParamsIdx
    NAME: str
    # REGISTER: RegsInfo
    VALUE: int | bool | str |float

class ReachStatus(StrEnum):
    CONNECTED = 'connected'
    CONNECTING = 'connecting'
    WAITING = 'waiting'

class ServerCommands(StrEnum):
    STATUS = 'STATUS'
    MOVE = 'MOVE'
    FOCUSIN = 'FOCUSIN'
    FOCUSOUT = 'FOCUSOUT'
    HALT = 'HALT'
    HOME = 'HOME'
    PARK = 'PARK'
    INVALID = 'INVALID'

class ServerMessageValidation(IntFlag):
    VALID = 1
    INVALID = 2
    MOVING = 4

MotorValidCommands = (
    ServerCommands.MOVE,
    ServerCommands.FOCUSIN,
    ServerCommands.FOCUSOUT,
    ServerCommands.HALT,
    ServerCommands.HOME,
    ServerCommands.PARK,
)

class MotorStatusFlags(IntFlag):
    ENABLED = auto()
    INVALID_1 = auto()
    FAULT = auto()
    INVALID_3 = auto()
    MOVING = auto()
    INVALID_5 = auto()
    INVALID_6 = auto()
    WAIT_INPUT = auto()
    INVALID_8 = auto()
    ALARM = auto()
    INVALID_10 = auto()
    WAIT_TIMER = auto()
    INVALID_12 = auto()
    INVALID_13 = auto()
    RUNNING = auto()
    PWR_UP = auto()
    LIM_MIN = auto()
    LIM_MAX = auto()
    INVALID = auto()

class MotorProgramStatus(IntFlag):
    NO_INIT = auto()
    READY = auto()
    RUN_HOMING = auto()
    ON_FAULT = auto()
    CHECK_RANGES = auto()
    RUN_PARK = auto()
    RUN_FOCUS_OUT = auto()
    RUN_FOCUS_IN = auto()
    RUN_GOTO = auto()
    MANUAL_MOVE = auto()
    ERROR_NEED_HOME = auto()
    ERROR_FOCUS_OUT = auto()
    ERROR_OUT_OF_RANGE = auto()
    ERROR_RS485 = auto()
    ERROR_PADDLE = auto()
    ERROR_LIM_SWITCH = auto()
    ERROR_MOTOR_OFF_ID = auto()
    # Added for DMX compatibility
    RUNNING = auto()            
    PAUSED = auto()
    ERROR = auto()
    INVALID = auto()

motor_program_errors_mask = 0x1FC00 # Mask to extract only the error bits from the program status [bits 10~16]
motor_alc_errors_mask = 0xFFF9 # Mask to extract only the error bits from the ALC

# MotorAlarmInfo é referente ao registro ALC do modbus
class MotorAlarmInfo(IntFlag):
    NO_ERROR = 0
    STALL = auto()
    HARDWARE_LIMIT_CCW = auto() 
    HARDWARE_LIMIT_CW = auto()
    OVER_TEMP = auto()
    INTERNAL_VOLTAGE = auto()
    UNDER_VOLTAGE = auto()
    OVER_VOLTAGE = auto()
    OVER_CURRENT = auto() 
    INTERNAL_ERROR_1 = auto()
    INTERNAL_ERROR_2 = auto() 
    COMMUNICATION_ERROR = auto()
    INTERNAL_ERROR_3 = auto()
    CANT_MOVE = auto()
    INTERNAL_ERROR_4 = auto()
    Q_PROGRAM_ERROR = auto()
    INTERNAL_ERROR_5 = auto()

#endregion
