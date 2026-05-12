from collections import namedtuple
from enum import StrEnum, Enum, IntFlag, auto
from typing import NamedTuple, TypedDict
from dataclasses import dataclass

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

class ServerParamsIdx(Enum):
    SERVER_IP=0
    PUB_PORT=1
    REP_PORT=2

#endregion

#region MOTOR
class MotorModels(StrEnum):
    ARCUS_DMX_ETH = 'DMX'
    AMP_MOTOR = 'AMP'

class MotorParamsIdx(Enum):     
    MOTOR_IP=0
    BACKLASH=1
    MAX_POS=2
    PARK_POS=3
    MAX_SPEED=4
    NORMAL_SPEED=5
    LOW_SPEED=6
    MAX_STEP=7

@dataclass
class MotorParameter():
    IDX: MotorParamsIdx
    NAME: str
    VALUE: int | bool | str

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
    ENABLED = 0
    FAULT = auto()
    MOVING = auto()
    WAIT_INPUT = auto()
    ALARM = auto()
    WAIT_TIMER = auto()
    RUNNING = auto()
    PWR_UP = auto()
    LIM_MIN = auto()
    LIM_MAX = auto()
    INVALID = auto()

class MotorProgramStatus(IntFlag):
    NO_INIT = 0
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
    ERROR_FOCUS_IN = auto()
    ERROR_OUT_OF_RANGE = auto()
    ERROR_RS485 = auto()
    ERROR_PADDLE = auto()
    ERROR_LIM_SWITCH = auto()
    VALID_STATUS = auto()
    # Added for DMX compatibility
    RUNNING = auto()            
    PAUSED = auto()
    ERROR = auto()
    INVALID = auto()

class MotorAlarmInfo(IntFlag):
    NO_ERROR = 0
    STALL = auto()
    INVALID_1 = auto() 
    INVALID_2 = auto()
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
