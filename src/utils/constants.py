from collections import namedtuple

Constants = namedtuple('Constants',
                        ['ID_FOCUSER_160', 
                         'ID_FOCUSER_IAG',
                         'ARCUS_DMX_ETH',
                         'MOTORZINHO',
                         'INVALID_POSITION'])

constants = Constants(
    ID_FOCUSER_160="64", 
    ID_FOCUSER_IAG="100",
    ARCUS_DMX_ETH="64", 
    MOTORZINHO="100",
    INVALID_POSITION=-9999,     # If a problem occurs in the reading an invalid value is published
    ) 