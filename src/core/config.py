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
    enc_2_microns: float = get_toml('Device', 'encoder2microns')
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
    acceleration: int = get_toml('Device', 'acceleration')
    deceleration: int = get_toml('Device', 'deceleration')
    idle_current: int = get_toml('Device', 'idle_current')
    run_current: int = get_toml('Device', 'run_current')
    acc_current: int = get_toml('Device', 'acc_current')
    cmd_timeout: int = get_toml('Device', 'cmd_timeout')
    # ---------------
    # Logging Section
    # ---------------
    log_level: str = get_toml('Logging', 'log_level')
    log_to_stdout: bool = get_toml('Logging', 'log_to_stdout')
    log_max_size_mb: int = get_toml('Logging', 'log_max_size_mb')
    log_num_keep: int = get_toml('Logging', 'log_num_keep')