# config.py - Device configuration file
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import os
import toml

config_file = "src/config/config.toml"

# _dict = {}
# _dict = toml.load(config_file)
def get_toml(sect: str, item: str, cfg_file: str = config_file):
    _dict = toml.load(cfg_file)
    if not _dict is {}:
        return _dict[sect][item]
    else:
        return ''

#TODO: Pensar em uma forma que evite ter que carregar toda a configuração cada vez que for mudar uma única configuração no Config
class Config:
    """Device configuration in ``config.toml``"""
    focuser: str = ""
    # ---------------
    # General Section
    # ---------------
    startup: str = get_toml('General', 'startup')
    name: str = get_toml('General', 'name')
    server_version: str = get_toml('General', 'version')

    # ---------------
    # Network Section
    # ---------------
    # ip_address: str = get_toml('Network', 'ip_address')
    ip_address: str = get_toml('Network', 'server_ip')
    port_pub: int = get_toml('Network', 'port_pub')
    port_rep: int = get_toml('Network', 'port_rep')
    sub_mask: int = get_toml('Network', 'sub_mask')
    gateway_ip: int = get_toml('Network', 'gateway_ip')
    pub_interval: int = get_toml('Network', 'pub_interval')
    write_timeout: int = get_toml('Network', 'write_timeout')
    # --------------
    # Device Section
    # --------------
    device_name: str = get_toml('Device', 'device_name')
    device_ip: str = get_toml('Device', 'device_ip')
    # router_ip: str = get_toml('Device', 'router_ip')
    device_port: int = get_toml('Device', 'device_port')
    absolute: bool = get_toml('Device', 'absolute')
    max_step: int = get_toml('Device', 'max_step')
    temp_comp: bool = get_toml('Device', 'temp_comp')
    stepsize: int = get_toml('Device', 'step_size')
    speed_factor: int = get_toml('Device', 'speedFactor')
    maxincrement: int = get_toml('Device', 'max_increment')
    speed_security: int = get_toml('Device', 'speed_security')
    tempcompavailable: bool = get_toml('Device', 'tempcompavailable')
    backlash: int = get_toml('Device', 'backlash')
    max_pos: int = get_toml('Device', 'max_pos')
    park_pos: int = get_toml('Device', 'park_pos')
    max_speed: int = get_toml('Device', 'max_speed')
    normal_speed: int = get_toml('Device', 'normal_speed')
    low_speed: int = get_toml('Device', 'low_speed')
    acceleration: float = get_toml('Device', 'acceleration')
    deceleration: float = get_toml('Device', 'deceleration')
    idle_current: float = get_toml('Device', 'idle_current')
    run_current: float = get_toml('Device', 'run_current')
    acc_current: float = get_toml('Device', 'acc_current')
    cmd_timeout: int = get_toml('Device', 'cmd_timeout')
    enc_2_microns: float = get_toml('Device', 'encoder2microns')
    steps_2_encoder: int = get_toml('Device', 'steps2encoder')
    microns_2_rps: float = get_toml('Device', 'microns2rps')
    # ---------------
    # Logging Section
    # ---------------
    log_level: str = get_toml('Logging', 'log_level')
    log_to_stdout: bool = get_toml('Logging', 'log_to_stdout')
    log_max_size_mb: int = get_toml('Logging', 'log_max_size_mb')
    log_num_keep: int = get_toml('Logging', 'log_num_keep')


def update_config():
    """Updates the device configuration according to ``config.toml``"""
    Config.focuser = ""
    # ---------------
    # General Section
    # ---------------
    Config.startup = get_toml('General', 'startup')
    Config.name = get_toml('General', 'name')
    Config.server_version = get_toml('General', 'version')

    # ---------------
    # Network Section
    # ---------------
    # ip_address = get_toml('Network', 'ip_address')
    Config.ip_address = get_toml('Network', 'server_ip')
    Config.port_pub = get_toml('Network', 'port_pub')
    Config.port_rep = get_toml('Network', 'port_rep')
    Config.sub_mask = get_toml('Network', 'sub_mask')
    Config.gateway_ip = get_toml('Network', 'gateway_ip')
    Config.pub_interval = get_toml('Network', 'pub_interval')
    Config.write_timeout = get_toml('Network', 'write_timeout')
    # --------------
    # Device Section
    # --------------
    Config.device_name = get_toml('Device', 'device_name')
    Config.device_ip = get_toml('Device', 'device_ip')
    # router_ip = get_toml('Device', 'router_ip')
    Config.device_port = get_toml('Device', 'device_port')
    Config.absolute = get_toml('Device', 'absolute')
    Config.max_step = get_toml('Device', 'max_step')
    Config.temp_comp = get_toml('Device', 'temp_comp')
    Config.stepsize = get_toml('Device', 'step_size')
    Config.speed_factor = get_toml('Device', 'speedFactor')
    Config.maxincrement = get_toml('Device', 'max_increment')
    Config.speed_security = get_toml('Device', 'speed_security')
    Config.tempcompavailable = get_toml('Device', 'tempcompavailable')
    Config.backlash = get_toml('Device', 'backlash')
    Config.max_pos = get_toml('Device', 'max_pos')
    Config.park_pos = get_toml('Device', 'park_pos')
    Config.max_speed = get_toml('Device', 'max_speed')
    Config.normal_speed = get_toml('Device', 'normal_speed')
    Config.low_speed = get_toml('Device', 'low_speed')
    Config.acceleration = get_toml('Device', 'acceleration')
    Config.deceleration = get_toml('Device', 'deceleration')
    Config.idle_current = get_toml('Device', 'idle_current')
    Config.run_current = get_toml('Device', 'run_current')
    Config.acc_current = get_toml('Device', 'acc_current')
    Config.cmd_timeout = get_toml('Device', 'cmd_timeout')
    Config.enc_2_microns = get_toml('Device', 'encoder2microns')
    Config.steps_2_encoder = get_toml('Device', 'steps2encoder')
    Config.microns_2_rps = get_toml('Device', 'microns2rps')
    # ---------------
    # Logging Section
    # ---------------
    Config.log_level = get_toml('Logging', 'log_level')
    Config.log_to_stdout = get_toml('Logging', 'log_to_stdout')
    Config.log_max_size_mb = get_toml('Logging', 'log_max_size_mb')
    Config.log_num_keep = get_toml('Logging', 'log_num_keep')