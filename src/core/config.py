# config.py - Device configuration file
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import os
import toml
import sys
import os

#def resource_path(relative_path):
#    """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller """
#    if hasattr(sys, '_MEIPASS'):
#        # No executável, sys._MEIPASS é a raiz da pasta temporária
#        base_path = sys._MEIPASS
#    else:
#        # No desenvolvimento, a base é a pasta raiz do projeto (onde está o main4.py)
#        # Como este arquivo está em src/core, pegamos o avô dele
#        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

#    return os.path.normpath(os.path.join(base_path, relative_path))

# def resource_path(relative_path):
#     """
#     Busca arquivos de configuração prioritariamente fora do executável
#     (na pasta onde o usuário instalou o programa).
#     """
#     # 1. Caminho onde o executável (.exe) está de fato localizado
#     exe_dir = os.path.dirname(sys.executable)
    
#     # 2. Caminho para rodar como script (desenvolvimento)
#     project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    
#     # Define o local externo (na pasta do programa)
#     external_path = os.path.join(exe_dir, relative_path)
    
#     # Define o local de desenvolvimento
#     dev_path = os.path.join(project_root, relative_path)

#     # Lógica de decisão:
#     if os.path.exists(external_path):
#         return external_path
#     elif os.path.exists(dev_path):
#         return dev_path
#     else:
#         # Fallback para o que estiver embutido (se houver)
#         base_path = getattr(sys, '_MEIPASS', project_root)
#         return os.path.join(base_path, relative_path)
    
# def resource_path(relative_path):
#     # Busca ao lado do .exe (pasta dist/src/config)
#     base_path = os.path.dirname(sys.executable)

#     return os.path.normpath(os.path.join(base_path, relative_path))

def resource_path(relative_path, external=False):
    """
    Função universal para localização de arquivos.
    - No VS Code: Segue a estrutura de pastas do projeto.
    - No EXE (Interno): Busca arquivos embutidos (psw.cfg, assets).
    - No EXE (Externo): Busca arquivos na pasta do usuário (config.toml).
    """
    # 1. Checa se o programa está rodando como um executável do PyInstaller
    frozen = getattr(sys, 'frozen', False)
    
    if frozen:  # Se 'False' significa que está rodando do Visual Studio (modo desenvolvimento)
        if external:
            # Caminho ao lado do arquivo .exe
            base_path = os.path.dirname(sys.executable)
        else:
            # Caminho dentro da pasta temporária do .exe
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        # 2. Modo Desenvolvimento (Visual Studio / VS Code)
        # Como este arquivo está em src/core, subimos dois níveis para chegar na raiz
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

    return os.path.normpath(os.path.join(base_path, relative_path))


# Se 'False' significa que está rodando do Visual Studio (modo desenvolvimento)
# Nesse caso a pasta com as configurações está dentro de 'src'
# if getattr(sys, 'frozen', False):
#     config_file =  resource_path('config/config.toml', external=True)
# else:
#     config_file =  resource_path('src/config/config.toml')
    
config_file =  resource_path('src/config/config.toml')

# _dict = {}
# _dict = toml.load(config_file)
def get_toml(sect: str, item: str, cfg_file: str = config_file) -> str | int | float | bool:
    _dict = toml.load(cfg_file)
    if not _dict is {}:
        data = _dict[sect][item]
        if isinstance(data, bool):
            return bool(_dict[sect][item])
        elif isinstance(data, str):
            return str(_dict[sect][item])
        elif isinstance(data, int):
            return int(_dict[sect][item])
        elif isinstance(data, float):
            return float(_dict[sect][item])
        else:
            return str(_dict[sect][item])
        # return _dict[sect][item]
    else:
        return ''

#TODO: Pensar em uma forma que evite ter que carregar toda a configuração cada vez que for mudar uma única configuração no Config
class Config:
    """Device configuration in ``config.toml``"""
    focuser: str = ""
    # ---------------
    # General Section
    # ---------------
    startup: bool = bool(get_toml('General', 'startup'))
    name: str = str(get_toml('General', 'name'))
    server_version: str = str(get_toml('General', 'version'))
    version_date: str = str(get_toml('General', 'date'))

    # ---------------
    # Network Section
    # ---------------
    # ip_address: str = get_toml('Network', 'ip_address')
    ip_address: str = str(get_toml('Network', 'server_ip'))
    port_pub: int = int(get_toml('Network', 'port_pub'))
    port_rep: int = int(get_toml('Network', 'port_rep'))
    sub_mask: str = str(get_toml('Network', 'sub_mask'))
    gateway_ip: str = str(get_toml('Network', 'gateway_ip'))
    pub_interval: float = float(get_toml('Network', 'pub_interval'))
    write_timeout: int = int(get_toml('Network', 'write_timeout'))
    # --------------
    # Device Section
    # --------------
    device_name: str = str(get_toml('Device', 'device_name'))
    device_ip: str = str(get_toml('Device', 'device_ip'))
    # router_ip: str = get_toml('Device', 'router_ip')
    device_port: int = int(get_toml('Device', 'device_port'))
    absolute: bool = bool(get_toml('Device', 'absolute'))
    max_step: int = int(get_toml('Device', 'max_step'))
    temp_comp: bool = bool(get_toml('Device', 'temp_comp'))
    stepsize: int = int(get_toml('Device', 'step_size'))
    speed_factor: int = int(get_toml('Device', 'speedFactor'))
    maxincrement: int = int(get_toml('Device', 'max_increment'))
    speed_security: int = int(get_toml('Device', 'speed_security'))
    tempcompavailable: bool = bool(get_toml('Device', 'tempcompavailable'))
    backlash: int = int(get_toml('Device', 'backlash'))
    max_pos: int = int(get_toml('Device', 'max_pos'))
    park_pos: int = int(get_toml('Device', 'park_pos'))
    max_speed: int = int(get_toml('Device', 'max_speed'))
    normal_speed: int = int(get_toml('Device', 'normal_speed'))
    low_speed: int = int(get_toml('Device', 'low_speed'))
    acceleration: float = float(get_toml('Device', 'acceleration'))
    deceleration: float = float(get_toml('Device', 'deceleration'))
    idle_current: float = float(get_toml('Device', 'idle_current'))
    run_current: float = float(get_toml('Device', 'run_current'))
    acc_current: float = float(get_toml('Device', 'acc_current'))
    cmd_timeout: int = int(get_toml('Device', 'cmd_timeout'))
    enc_2_microns: float = float(get_toml('Device', 'encoder2microns'))
    steps_2_encoder: float = float(get_toml('Device', 'steps2encoder'))
    microns_2_rps: float = float(get_toml('Device', 'microns2rps'))
    # ---------------
    # Logging Section
    # ---------------
    log_level: str = str(get_toml('Logging', 'log_level'))
    log_to_stdout: bool = bool(get_toml('Logging', 'log_to_stdout'))
    log_max_size_mb: int = int(get_toml('Logging', 'log_max_size_mb'))
    log_num_keep: int = int(get_toml('Logging', 'log_num_keep'))


def update_config():
    """Updates the device configuration according to ``config.toml``"""
    Config.focuser = ""
    # ---------------
    # General Section
    # ---------------
    Config.startup = bool(get_toml('General', 'startup'))
    Config.name = str(get_toml('General', 'name'))
    Config.server_version = str(get_toml('General', 'version'))

    # ---------------
    # Network Section
    # ---------------
    # ip_address = get_toml('Network', 'ip_address')
    Config.ip_address = str(get_toml('Network', 'server_ip'))
    Config.port_pub = int(get_toml('Network', 'port_pub'))
    Config.port_rep = int(get_toml('Network', 'port_rep'))
    Config.sub_mask = str(get_toml('Network', 'sub_mask'))
    Config.gateway_ip = str(get_toml('Network', 'gateway_ip'))
    Config.pub_interval = float(get_toml('Network', 'pub_interval'))
    Config.write_timeout = int(get_toml('Network', 'write_timeout'))
    # --------------
    # Device Section
    # --------------
    Config.device_name = str(get_toml('Device', 'device_name'))
    Config.device_ip = str(get_toml('Device', 'device_ip'))
    # router_ip = get_toml('Device', 'router_ip')
    Config.device_port = int(get_toml('Device', 'device_port'))
    Config.absolute = bool(get_toml('Device', 'absolute'))
    Config.max_step = int(get_toml('Device', 'max_step'))
    Config.temp_comp = bool(get_toml('Device', 'temp_comp'))
    Config.stepsize = int(get_toml('Device', 'step_size'))
    Config.speed_factor = int(get_toml('Device', 'speedFactor'))
    Config.maxincrement = int(get_toml('Device', 'max_increment'))
    Config.speed_security = int(get_toml('Device', 'speed_security'))
    Config.tempcompavailable = bool(get_toml('Device', 'tempcompavailable'))
    Config.backlash = int(get_toml('Device', 'backlash'))
    Config.max_pos = int(get_toml('Device', 'max_pos'))
    Config.park_pos = int(get_toml('Device', 'park_pos'))
    Config.max_speed = int(get_toml('Device', 'max_speed'))
    Config.normal_speed = int(get_toml('Device', 'normal_speed'))
    Config.low_speed = int(get_toml('Device', 'low_speed'))
    Config.acceleration = float(get_toml('Device', 'acceleration'))
    Config.deceleration = float(get_toml('Device', 'deceleration'))
    Config.idle_current = float(get_toml('Device', 'idle_current'))
    Config.run_current = float(get_toml('Device', 'run_current'))
    Config.acc_current = float(get_toml('Device', 'acc_current'))
    Config.cmd_timeout = int(get_toml('Device', 'cmd_timeout'))
    Config.enc_2_microns = float(get_toml('Device', 'encoder2microns'))
    Config.steps_2_encoder = float(get_toml('Device', 'steps2encoder'))
    Config.microns_2_rps = float(get_toml('Device', 'microns2rps'))
    # ---------------
    # Logging Section
    # ---------------
    Config.log_level = str(get_toml('Logging', 'log_level'))
    Config.log_to_stdout = bool(get_toml('Logging', 'log_to_stdout'))
    Config.log_max_size_mb = int(get_toml('Logging', 'log_max_size_mb'))
    Config.log_num_keep = int(get_toml('Logging', 'log_num_keep'))