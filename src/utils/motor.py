

class MotorData():

    ID: str
    IP: str
    firmware_version: str

    backlash: int
    max_pos: int
    park_pos: int
    max_speed: int
    normal_speed: int
    low_speed: int

    # motor_data = {"DEVICE_ID":'',
    #             "DEVICE_IP":'',
    #             "BACKLASH":'',
    #             "MAX_POS":'',
    #             "PARK_POS":'',
    #             "MAX_SPEED":'',
    #             "NORMAL_SPEED":'',
    #             "LOW_SPEED":''}