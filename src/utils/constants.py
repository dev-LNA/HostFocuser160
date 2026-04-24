from collections import namedtuple
from enum import StrEnum, Enum, IntFlag
from typing import NamedTuple

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
    INVALID=-1


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


