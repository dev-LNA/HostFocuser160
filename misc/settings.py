from ast import Attribute

from PyQt6 import uic, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QLineEdit, QProgressBar, QDialog, QMessageBox, QSpinBox, QDoubleSpinBox, QCheckBox,QWidget
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QFontMetrics, QKeyEvent
# from src.core.exceptions import NotImplementedException
from misc.load_bar import LoadBar
from misc.ui_intellisense import UiWidgets
from misc.login_form import LoginForm
from misc.default_settings import LoadConfigForm
from misc.verification import VerificationDialog

# from src.interface.dmx_eth import FocuserDriver
# from src.interface.focuser_driver import FocuserDriver
from src.core.config import Config, get_toml, update_config
from src.core.log import FocusLogger

from src.utils.constants import constants, MotorModels, MotorParamsIdx, ServerParamsIdx, Conversion
from src.interface.motor_driver import Driver
from src.utils.motor import Motor

from datetime import datetime
from typing import NamedTuple, Generic, TypeVar
from dataclasses import dataclass

import sys
import os
import toml
import shutil

import time




# def resource_path(relative_path):
#     """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller """
#     if hasattr(sys, '_MEIPASS'):
#         # No executável, sys._MEIPASS é a raiz da pasta temporária
#         base_path = sys._MEIPASS
#     else:
#         # No desenvolvimento, a base é a pasta raiz do projeto (onde está o main4.py)
#         # Como este arquivo está em misc, pegamos o pai dele
#         base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

#     return os.path.normpath(os.path.join(base_path, relative_path))

# def resource_path(relative_path, external=False):
#     if external:
#         # Busca ao lado do .exe (pasta dist/src/config)
#         base_path = os.path.dirname(sys.executable)
#     else:
#         if hasattr(sys, '_MEIPASS'):
#         # No executável, sys._MEIPASS é a raiz da pasta temporária
#             base_path = sys._MEIPASS
#         else:
#             # No desenvolvimento, a base é a pasta raiz do projeto (onde está o main4.py)
#             # Como este arquivo está em misc, pegamos o pai dele
#             base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    
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
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    return os.path.normpath(os.path.join(base_path, relative_path))

# path_to_ui = resource_path('assets/ui/engineering.ui')              # Path to settings window UI
# config_dir = resource_path('src/config', external=True)  #"src/config/"
# config_file = config_dir + "/config.toml" #"src/config/config.toml"
# config_file_backup = config_dir + "/config_backup.toml" #"src/config/config_backup.toml"                #TODO: Possibilitar definir o nome do arquivo? Talvez nomear de acordo com a data que foi criado
# config_file_default = config_dir + "/config_default.toml" #"src/config/config_default.toml"
# config_file_160 = config_dir + "/config_PE160.toml" 
# config_file_iag = config_dir + "/config_IAG.toml" 

# Se 'False' significa que está rodando do Visual Studio (modo desenvolvimento)
# Nesse caso a pasta com as configurações está dentro de 'src'
if getattr(sys, 'frozen', False):
    # Rodando do executável
    path_to_ui = resource_path('assets/ui/engineering.ui')              # Path to settings window UI
    config_dir = resource_path('config', external=True)  #"src/config/"
    config_file_backup = resource_path('src/config/config_backup.toml', external=False)               #TODO: Possibilitar definir o nome do arquivo? Talvez nomear de acordo com a data que foi criado
    config_file_default = resource_path('src/config/config_default.toml', external=False)
    config_file = resource_path('src/config/config.toml', external=False)
    config_file_160 =  config_dir + "/config_PE160.toml" 
    config_file_iag = config_dir + "/config_IAG.toml" 

    # config_file = config_dir + "/config.toml" #"src/config/config.toml"
    # config_file_backup = config_dir + "/config_backup.toml" #"src/config/config_backup.toml"                #TODO: Possibilitar definir o nome do arquivo? Talvez nomear de acordo com a data que foi criado
    # config_file_default = config_dir + "/config_default.toml" #"src/config/config_default.toml"
    # config_file_160 = config_dir + "/config_PE160.toml" 
    # config_file_iag = config_dir + "/config_IAG.toml" 
else:
    # Rodando em modo desenvolvimento (Visual Studio)
    path_to_ui = resource_path('assets/ui/engineering.ui')              # Path to settings window UI
    config_dir = resource_path('src/config')  #"src/config/"
    config_file = config_dir + "/config.toml" #"src/config/config.toml"
    config_file_backup = config_dir + "/config_backup.toml" #"src/config/config_backup.toml"                #TODO: Possibilitar definir o nome do arquivo? Talvez nomear de acordo com a data que foi criado
    config_file_default = config_dir + "/config_default.toml" #"src/config/config_default.toml"
    config_file_160 = config_dir + "/config_PE160.toml" 
    config_file_iag = config_dir + "/config_IAG.toml" 


# Using a generic type for the widgets guarantees typing is resolved
T_Widget = TypeVar('T_Widget', QLineEdit, QSpinBox, QCheckBox, QDoubleSpinBox)

@dataclass
class SettingsAttributes(Generic[T_Widget]):
    NAME: MotorParamsIdx | ServerParamsIdx
    TAG: str
    OBJ: T_Widget
    VALUE: str | int | bool | float
    TYPE: object


class ConfigurableSettings(NamedTuple):
    SERVER_IP : SettingsAttributes[QLineEdit]
    PORT_PUB: SettingsAttributes[QSpinBox]
    PORT_REP: SettingsAttributes[QSpinBox]
    SUB_MASK: SettingsAttributes[QLineEdit]
    GATEWAY_IP: SettingsAttributes[QLineEdit]
    STARTUP : SettingsAttributes[QCheckBox]
    MOTOR_IP: SettingsAttributes[QLineEdit]
    BACKLASH: SettingsAttributes[QSpinBox]
    MAX_POS: SettingsAttributes[QSpinBox]
    PARK_POS: SettingsAttributes[QSpinBox]
    MAX_SPEED: SettingsAttributes[QSpinBox]
    NORMAL_SPEED: SettingsAttributes[QSpinBox]
    LOW_SPEED: SettingsAttributes[QSpinBox]
    MAX_STEP: SettingsAttributes[QSpinBox]
    ACCELERATION: SettingsAttributes[QDoubleSpinBox]
    DECELERATION: SettingsAttributes[QDoubleSpinBox]
    IDLE_CURRENT: SettingsAttributes[QDoubleSpinBox]
    RUN_CURRENT: SettingsAttributes[QDoubleSpinBox]
    ACC_CURRENT: SettingsAttributes[QDoubleSpinBox]


class SettingsWindowSignals(QObject):
    window_closed = pyqtSignal(bool)
    engineering_mode = pyqtSignal(bool)
    command_response = pyqtSignal(str)
    progress = pyqtSignal(int)
    changed_settings = pyqtSignal(dict)

class SettingsWindow(QMainWindow):

    signals = SettingsWindowSignals()

    _engineering_mode = False                                       # Engineering mode state
    _logged_user = "<b>USER</b>"                                           # Current logged user

    _motor_settings = dict()                                        # Motor current settings
    _settings_changed = False                                       # Informs if a setting was changed
    _changed_settings = dict[MotorParamsIdx | ServerParamsIdx, str | int | float | bool]()                                      # Dict of settings that were changed, keeping the old values for reference

    def __init__(self, motor: Motor, logger: FocusLogger):
        super().__init__()

        if type(motor.driver).__base__ is not Driver:
            raise RuntimeError("Driver must be of Driver class")
        
        self.motor = motor
        self.logger = logger
        
        uic.loadUi(path_to_ui, self)                                # Loads the window UI  # type: ignore 
        # self.setFixedSize(QSize(937, 508))

        self.ui_elements = UiWidgets(self, "settings")              # Generates UI elements intellisense

    # The QLineEdits must be initialized as 'disabled'. This is changed in engineering mode.
        # lineEdits = self.findChildren(QLineEdit)                                        # Makes a list of all QLineEdit widgets
        # for _ in lineEdits:                                                             # Connects the engineering mode signal to each QLineEdit setEnabled
        #     self.signals.engineering_mode.connect(_.setEnabled)                         #  this way when engineering mode is activated the line edits automatically become enabled   

        self.ui_elements.gbMotorParameters.setEnabled(False)
        self.signals.engineering_mode.connect(self.ui_elements.gbMotorParameters.setEnabled)

        # self.ui_elements.gbNetwork.setEnabled(False)
        self.signals.engineering_mode.connect(self.ui_elements.gbNetwork.setEnabled)

        # self.ui_elements.gbZMQ.setEnabled(False)
        self.signals.engineering_mode.connect(self.ui_elements.gbZMQ.setEnabled)

        self.ui_elements.gbServerParams.setEnabled(False)
        self.signals.engineering_mode.connect(self.ui_elements.gbServerParams.setEnabled)

        self.ui_elements.btnSave.setVisible(False)
        self.signals.engineering_mode.connect(self.ui_elements.btnSave.setVisible)      # Save button is only enabled in engineering mode

        # self.engineering_mode = False                                                   # Initializes engineering mode to false

        self.ui_elements.btnEngineering.clicked.connect(self._login_engineering_mode)   # Connects engineering login button
        self.ui_elements.btnSave.clicked.connect(self._save_settings)                   # Connects save settings button
        self.ui_elements.btnDefault.clicked.connect(self._load_config_values)           # Connects default settings button
        self.ui_elements.btnBackup.clicked.connect(self._load_config_values)            # Connects default settings button
        self.ui_elements.btnReadMotor.clicked.connect(self._update_settings)            # Connects read motor settings button
        
        
        self.ui_elements.frameCommand.setVisible(False)                                 # Send commands frame begins not visible
        self.signals.engineering_mode.connect(self.ui_elements.frameCommand.setVisible) # The commands frame is only visible when in engineering mode

        self.ui_elements.gbRetrieveParameters.setVisible(False)
        self.signals.engineering_mode.connect(self.ui_elements.gbRetrieveParameters.setVisible)

        # self.ui_elements.btnDefault.setVisible(False)                                   # Defaul configurations button begins not visible
        # self.signals.engineering_mode.connect(self.ui_elements.btnDefault.setVisible)   # The default configurations button is only visible in engineering mode

        # self.ui_elements.btnBackup.setVisible(False)                                    # Defaul configurations button begins not visible
        # self.signals.engineering_mode.connect(self.ui_elements.btnBackup.setVisible)    # The default configurations button is only visible in engineering mode

        # self.ui_elements.btnReadMotor.setVisible(False)                                    # Defaul configurations button begins not visible
        # self.signals.engineering_mode.connect(self.ui_elements.btnReadMotor.setVisible)    # The default configurations button is only visible in engineering mode

        self.ui_elements.btnSendCommand.clicked.connect(self._send_test_command)
        self.ui_elements.txtCommand.returnPressed.connect(self._send_test_command)
        self.ui_elements.txtCommand.textChanged.connect(self._command_changed)

        self.ui_elements.lblServerVer_val.setText(Config.server_version)
        self.ui_elements.lblAccessLvl.setText("Access level: " + self._logged_user)
        

        self.signals.command_response.connect(self.ui_elements.lblResponse_Val.setText)

        self._config_settings = ConfigurableSettings(
                # Server parameters
                    SERVER_IP = SettingsAttributes(ServerParamsIdx.SERVER_IP, 'Server IP Address', self.ui_elements.txtSocketIP, '0', str),
                    PORT_PUB = SettingsAttributes(ServerParamsIdx.PORT_PUB, 'ZMQ PUB Port', self.ui_elements.spinPortPub, 0, int),
                    PORT_REP = SettingsAttributes(ServerParamsIdx.PORT_REP, 'ZMQ REP Port', self.ui_elements.spinPortRep, 0, int),
                    SUB_MASK = SettingsAttributes(ServerParamsIdx.SUB_MASK, 'Subnet Mask', self.ui_elements.txtSubMask, '0', str),
                    GATEWAY_IP = SettingsAttributes(ServerParamsIdx.GATEWAY_IP, 'Gateway IP Address', self.ui_elements.txtGatewayIP, '0', str),
                    STARTUP= SettingsAttributes(ServerParamsIdx.STARTUP, 'Auto Startup', self.ui_elements.cbAutoStartup, False, bool ),
                # Motor parameters
                    MOTOR_IP = SettingsAttributes(MotorParamsIdx.MOTOR_IP, 'Motor IP Address' , self.ui_elements.txtMotorIP, '0', str),
                    BACKLASH = SettingsAttributes(MotorParamsIdx.BACKLASH, 'Backlash', self.ui_elements.spinBacklash, 0, int),
                    MAX_POS = SettingsAttributes(MotorParamsIdx.MAX_POS, 'Maximum Mirror Position', self.ui_elements.spinMaxPos, 0, int),
                    PARK_POS = SettingsAttributes(MotorParamsIdx.PARK_POS, 'Park Mirror Position', self.ui_elements.spinParkPos, 0, int),
                    MAX_SPEED = SettingsAttributes(MotorParamsIdx.MAX_SPEED, 'Maximum Motor Speed', self.ui_elements.spinMaxSpeed, 0, int),
                    NORMAL_SPEED = SettingsAttributes(MotorParamsIdx.NORMAL_SPEED, 'Normal Motor Speed', self.ui_elements.spinNormalSpeed, 0, int),
                    LOW_SPEED = SettingsAttributes(MotorParamsIdx.LOW_SPEED, 'Low Motor Speed', self.ui_elements.spinLowSpeed, 0, int),
                    MAX_STEP = SettingsAttributes(MotorParamsIdx.MAX_STEP, 'Max Step (Deprecated)', self.ui_elements.spinMaxStep, 0, int),
                    ACCELERATION = SettingsAttributes(MotorParamsIdx.ACCELERATION, 'Acceleration Rate', self.ui_elements.spinAcceleration, 0, float),
                    DECELERATION = SettingsAttributes(MotorParamsIdx.DECELERATION, 'Deceleration Rate', self.ui_elements.spinDeceleration, 0, float),
                    IDLE_CURRENT = SettingsAttributes(MotorParamsIdx.IDLE_CURRENT, 'Motor Idle Current', self.ui_elements.spinIdleCurrent, 0, float),
                    RUN_CURRENT = SettingsAttributes(MotorParamsIdx.RUN_CURRENT, 'Motor Running Current', self.ui_elements.spinRunCurrent, 0, float),
                    ACC_CURRENT = SettingsAttributes(MotorParamsIdx.ACC_CURRENT, 'Motor Acceleration Current', self.ui_elements.spinAccCurrent, 0, float),
                )


        self._progress_bar = LoadBar()                                                  # Creates load bar
        
        if self.ui_elements.statusBar:
            self.ui_elements.statusBar.addPermanentWidget(self._progress_bar)                         # Add load bar to status bar, it is not visible by default and is made visible when needed

        # The updater runs on a different thread and retrieves the motor current configured parameters
        self._updater = RetrieveSettings(self.motor)

        self._updater.signal_running.connect(self._progress_bar.setVisible)                   # The progress bar visibility is connected to the updater method running signal
        self._updater.signal_progress.connect(self._progress_bar.progress.setValue)    # The progress bar value is connected to the updater method progress
    
        # The motor data is kept in a dictionary and the parse function is responsible to parse the information
        self._updater.signal_motor_data.connect(self._parse_motor_data)

        # When the updater finishes reading the motor the dictionary with the current values must be updated
        self._updater.signal_running.connect(self._initialize_motor_settings)                 

        self._changed_settings.clear()          # Resets changes dictionary   

        # if Config.focuser == "160":
        self._update_settings()                                                         # Runs the _updater to retrieve the current motor parameters
        # else:
            # raise RuntimeError("The IAG settings are not implemented yet")                  #TODO: Implementar configurações do IAG


#region  ========== PROPERTIES ========== # 

    @property
    def engineering_mode(self) -> bool:     # Property to read the engineering mode state
        return self._engineering_mode
    @engineering_mode.setter                # Engineering mode setter
    def engineering_mode(self, value: bool):
        self._engineering_mode = value  
        self.signals.engineering_mode.emit(value)       # When the engineering mode changes signals all slots connected

    @property
    def logged_user(self) -> str:           # Property to read the current logged user
        return self._logged_user
    @logged_user.setter
    def logged_user(self, user:str):
        self._logged_user = user
        self.ui_elements.lblAccessLvl.setText("Access level: " + self._logged_user)
        
    #TODO: Verificar outra forma de fazer isso. E se é necessário, acho que essa infomração nem existe atualmente.
    # def _logged_user_setter(self, name: str):   # Logged user setter (A method was used in order to be able to connect this method to the signal from the login form)
    #     self._logged_user = name 

    @property
    def motor_settings(self):
        return self._motor_settings

#endregion

#region  ========== METHODS ========== # 

    def _update_settings(self):
        """Updates current settings by reading the values from the motor
        The thread will run one time only"""
        self._updater.start()               # Starts the thread


    def _parse_motor_data(self, data: Motor):
        """Parses the motor data and updates the GUI with the information
        retrieved from the motor
        This method is called automatically when the _updater thread
        finishes its execution"""

        self.ui_elements.lblFocuser.setText(data.ID)
        self.ui_elements.lblFirmVer_value.setText(data._firmware_version)

        for param in self._config_settings:
            # if param.NAME in MotorParamsIdx:
            if isinstance(param.NAME, MotorParamsIdx):
                if isinstance(param.OBJ, QLineEdit):
                    param.OBJ.setText(str(data.parameters[param.NAME].VALUE))
                elif isinstance(param.OBJ, QDoubleSpinBox):
                    param.OBJ.setValue(float(data.parameters[param.NAME].VALUE))
                elif isinstance(param.OBJ, QCheckBox):
                    param.OBJ.setChecked(bool(data.parameters[param.NAME].VALUE))
                else:
                    param.OBJ.setValue(int(float(data.parameters[param.NAME].VALUE))) # Must first convert to float to avoid problems with the float parameters

        self._config_settings.SERVER_IP.OBJ.setText(Config.ip_address)
        self._config_settings.PORT_PUB.OBJ.setValue(Config.port_pub)
        self._config_settings.PORT_REP.OBJ.setValue(Config.port_rep)
        self._config_settings.SUB_MASK.OBJ.setText(Config.sub_mask)
        self._config_settings.GATEWAY_IP.OBJ.setText(Config.gateway_ip)
        self._config_settings.STARTUP.OBJ.setChecked(Config.startup)

    def _initialize_motor_settings(self, value):
        """Updates the dictionary with the values retrieved from the motor
        This method is called automatically when the _updater thread
        finishes its execution"""
        if value is False:                                                                  # The motor reading finishes when the _running signal goes to False

            for param in self._config_settings:
                if isinstance(param.OBJ, QLineEdit):
                    param.VALUE = param.OBJ.text()
                    param.OBJ.textChanged.connect(self._validate_parameters)
                elif isinstance(param.OBJ, QSpinBox) or isinstance(param.OBJ, QDoubleSpinBox):
                    param.VALUE = param.OBJ.value()
                    param.OBJ.valueChanged.connect(self._validate_parameters)
                elif isinstance(param.OBJ, QCheckBox):
                    param.VALUE = param.OBJ.isChecked()
                    param.OBJ.checkStateChanged.connect(self._validate_parameters)

            for param in self._config_settings:
                print(f"{param.NAME} -> {param.VALUE}")
                    
    def _set_settings(self, param:SettingsAttributes):

        if isinstance(param.OBJ, QLineEdit):
            value = param.OBJ.text()
        elif isinstance(param.OBJ, QSpinBox) or isinstance(param.OBJ, QDoubleSpinBox):
            value = param.OBJ.value()
        elif isinstance(param.OBJ, QCheckBox):
            value = param.OBJ.isChecked()

        # If the value being set is equal to the current value the parameter
        # is removed from the "_changed_settings" dict
        if value == param.VALUE:
            if param.NAME in self._changed_settings:
                del self._changed_settings[param.NAME]

        # To be considered that the value was changed the value must be different from the current value OR
        # if that parameter is already in "_changed_settings" then this new value must be different from the one in 
        # '_changed_settings'
        if (param.VALUE != value) or \
            ( (param.NAME in self._changed_settings) and self._changed_settings[param.NAME] != value):
            
            self._changed_settings[param.NAME] = value             # Indicates that this value has changed and saves the new value
            print(f"{param.NAME} value changed to {value}")

            print(self._changed_settings[param.NAME])

        else:
            # self._settings_changed = False
            print(f"{param.NAME} value NOT changed")
        
        

    def _set_motor_settings(self, key:MotorParamsIdx | ServerParamsIdx, value:str):
            """Sets a new value for a specific parameter setting.
            In this method the '_changed_settings' dictionary is altered
            according to the new setting. This dictionary can later be
            compared to the current motor settings to evaluate which 
            settings were changed and need to be sent to the motor.

            _motor_settings [dict]: Current motor parameters
            _changed_settings [dict]: New values to be set 

            :param key: Motor parameter that will be changed
            :type key: MotorParamsIdx
            :param value: New parameter value
            :type value: str
            """
            # If the value being set is equal to the current value the parameter
            # is removed from the "_changed_settings" dict
            if value == self._motor_settings[key]:
                if key in self._changed_settings:
                    print(f"{self._changed_settings}")
                    print("deleting key")
                    del self._changed_settings[key]
                    print(f"{self._changed_settings}")

            # To be considered that the value was changed the value must be different from the current value OR
            # if that parameter is already in "_changed_settings" than this new value must be different from the one in 
            # '_changed_settings'
            if (self._motor_settings[key] != value) or \
                ( (key in self._changed_settings) and self._changed_settings[key] != value):
                self._changed_settings[key] = value             # Indicates that this value has changed and saves the new value
                # self._settings_changed = True
                print(f"{key} value changed to {value}")
            else:
                # self._settings_changed = False
                print(f"{key} value NOT changed")

    def _command_changed(self):
        """Guarantees that the text in the command QLineEdit
          will allways be uppercase""" # TODO: Deve ter outro jeito de fazer isso
        self.ui_elements.txtCommand.setText(self.ui_elements.txtCommand.text().upper())
   
    def _send_test_command(self):
        """Sends the command written in text box and 
        emits the motor response"""
        if self.engineering_mode and self.ui_elements.txtCommand.text():   # The button is not supposed to be visible when not in engineering mode, this is just a safeguard
            try:
                self.signals.command_response.emit(self.motor.driver.sendCommand(self.ui_elements.txtCommand.text()))
            except Exception as e:
                print(e)
            
    def _create_backup_config(self, backup_file_path: str = config_file_backup):
        """Creates a backup file of the current motor configurations

        :param backup_file_path: Defines the path and name of the backup file, defaults to 
        the path and name define in 'config_file_backup'
        :type backup_file_path: str, optional
        """
        try:
            # The backup config files are emebedded in the executable
            if Config.name == "PE 160 Focuser":
                # backup_file_path = config_dir + "/config_backup_160.toml"
                backup_file_path = resource_path('src/config/config_backup_160.toml', external=False)
            elif Config.name == "IAG Focuser":
                # backup_file_path = config_dir + "/config_backup_IAG.toml"
                backup_file_path = resource_path('src/config/config_backup_IAG.toml', external=False)
            

            shutil.copy(config_file, backup_file_path)            #TODO: 'copy' do not retain the metadata, if metadata is needed change to '.copy2'
            self.logger.info(f"Created backup configuration file: {backup_file_path}")

        except FileNotFoundError:
            print("The source file was not found.")
            self.logger.error(f"Could not create configuration backup file. The source file was not found.")
        except PermissionError:
            print("Permission denied to access files or destination.")
            self.logger.error(f"Could not create configuration backup file. Permission denied to access files or destination.")
        except shutil.SameFileError:
            print("Source and destination are the same file.")
            self.logger.error(f"Could not create configuration backup file. Source and destination are the same file.")

    def _update_config_file(self, cfg_file: str, keys: tuple[MotorParamsIdx | ServerParamsIdx]):
        #TODO: Atualizar esse método para não apagar comentários no arquivo de configuração
        with open(cfg_file, 'r') as f:
            config = toml.load(f)
            for k in keys:
                if isinstance(k, ServerParamsIdx):
                    if isinstance(self._changed_settings[k], bool):
                        config['General'][k.name.lower()] = self._changed_settings[k]
                    if isinstance(self._changed_settings[k], int):
                        config['Network'][k.name.lower()] = int(self._changed_settings[k])
                    else:
                        config['Network'][k.name.lower()] = self._changed_settings[k]

                elif k == MotorParamsIdx.MOTOR_IP:
                    Config.device_ip = config['Device']['device_ip']

                else:
                    if isinstance(self._changed_settings[k], int):
                        config['Device'][k.name.lower()] = int(self._changed_settings[k])
                    else:
                        config['Device'][k.name.lower()] = self._changed_settings[k]

        with open(cfg_file, 'w') as f:
            toml.dump(config, f)

    def _load_config_values(self):
        """Opens the dialog window to confirm loading of default or
        backup configurations"""
        if self.sender() is self.ui_elements.btnDefault:
            # The default config files will be embedded in the executable
            if Config.name == "PE 160 Focuser":
                # cfg_file = config_dir + "/config_default_160.toml"
                cfg_file = resource_path('src/config/config_default_160.toml', external=False)
            elif Config.name == "IAG Focuser":
                # cfg_file = config_dir + "/config_default_IAG.toml"
                cfg_file = resource_path('src/config/config_default_IAG.toml', external=False)
            msg = "DEFAULT"
            self.logger.info("Loading default motor configuration")
        elif self.sender() is self.ui_elements.btnBackup:
            # The backup config files are emebedded in the executable
            if Config.name == "PE 160 Focuser":
                # cfg_file = config_dir + "/config_backup_160.toml"
                cfg_file = resource_path('src/config/config_backup_160.toml', external=False)
            elif Config.name == "IAG Focuser":
                # cfg_file = config_dir + "/config_backup_IAG.toml"
                cfg_file = resource_path('src/config/config_backup_IAG.toml', external=False)
            msg = "BACKUP"
            self.logger.info("Loading backup motor configuration")

        self._default_widget = LoadConfigForm(msg)
        if self._default_widget.exec() == QDialog.DialogCode.Accepted:
            for param in self._config_settings:
                if param.NAME.name in self._default_widget.selected_items:
                    if param.NAME.name == "MOTOR_IP":
                        config = get_toml('Device', 'device_ip', cfg_file)
                        # if Config.name == "Focuser160":
                        #     config = get_toml('Device', 'ip_160', cfg_file)
                        # elif Config.name == "FocuserIAG":
                        #     config = get_toml('Device', 'ip_iag', cfg_file)
                    elif isinstance(param.NAME, ServerParamsIdx):
                        # The server parameters are saved in Network section
                        if param.NAME == ServerParamsIdx.STARTUP:
                            config = get_toml('General', param.NAME.name.lower(), cfg_file)
                        else:
                            config = get_toml('Network', param.NAME.name.lower(), cfg_file)
                    else:
                        # The rest of the parameters are saved in Device section
                        config = str(get_toml('Device', param.NAME.name.lower(), cfg_file))
                

                    if isinstance(param.OBJ, QLineEdit) and isinstance(config, str):
                        # QLineEdits will use the string directly
                        param.OBJ.setText(config)
                    elif isinstance(param.OBJ, QCheckBox) and isinstance(config, bool):
                        param.OBJ.setChecked(config)
                    elif isinstance(param.OBJ, QSpinBox):
                            param.OBJ.setValue(int(float(config))) 
                    elif isinstance(param.OBJ, QDoubleSpinBox):
                            param.OBJ.setValue(float(config)) 
                    
                    # else:
                    #     # The value must be properly converted according to the parameter type
                    #     if param.TYPE is int and isinstance(param.OBJ, QSpinBox):
                    #         param.OBJ.setValue(int(float(config))) 
                    #     elif isinstance(param.OBJ, QDoubleSpinBox):
                    #         param.OBJ.setValue(float(config)) 

                    self._validate_parameters()    



        else:
            print("DO NOT RETURN TO DEFAULT VALUES")
        self._default_widget.destroy()

    def _check_values_conflicts(self):
        """Verifies conflicts between configured values
           If a conflict is found raises an error with more information"""
        error_msg = ""
        if (self._config_settings.PORT_PUB.NAME in self._changed_settings) or (self._config_settings.PORT_REP.NAME in self._changed_settings):
            if self._config_settings.PORT_PUB.OBJ.value() == self._config_settings.PORT_REP.OBJ.value():
                error_msg += "The ZMQ configuration PORT PUB and PORT REP must have different values"    
                # raise ValueError("The ZMQ configuration PORT PUB and PORT REP must have different values")
        
        if error_msg != "":
            raise ValueError(error_msg)


    def _save_settings(self):
        """Save to the motor the values configured in the text boxes
        Checks if the value in the text box changed in relation to the one read from the motor
        during the initialization, and if the value has changed sends the command to the motor to 
        change the setting value."""

        try:
            ValError = False
            # for key, value in self._changed_settings.items():
            #     if value == "":
            #         raise ValueError(f"Cannot save empty value to motor parameters")
            # The QLineEdits may be empty at this point, but the QSpinBoxes have a protection against being empty
            for param in self._config_settings:
                
                if isinstance(param.OBJ, QLineEdit) and param.NAME in self._changed_settings:
                    val = self._changed_settings[param.NAME]
                    if isinstance(val, str):
                        text = val.replace(".", "")                  # Remove dots from IP masked values
                        if not text:
                            raise ValueError(f"Cannot save empty value to parameters")

            self._check_values_conflicts()

        except Exception as e:
            dialog = QMessageBox(self)
            dialog.setText(str(e))
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.exec()
            ValError = True

        # If the "_changed_settings" dictionary has any elements then a setting was changed and the command store must be executed
        if self._changed_settings and not ValError:                       
            verify = VerificationDialog()
            text = ""
            keys, values = zip(*self._changed_settings.items())
            
            for i in range(0, len(keys)):
                key_str = keys[i].name.replace("'", "")
                # text += f"<font color=red> {self.motor.parameters[keys[i]].NAME}</font>: {self._motor_settings[keys[i]]} -> {values[i]} <br>"
                text += f"<font color=red> {key_str}</font>: {self._config_settings[keys[i].value].VALUE} -> {values[i]} <br>"
            
            text += f"<br>"
            text += f"<font color=red> * The server or the motor/CLP must be restarted for some changes to take effect </font>"
            verify.txtChanges.setText(text)

            font_size = QFontMetrics(verify.txtChanges.font())
            text_height = ( (len(keys) + 2) * font_size.height()) + 20

            verify.txtChanges.setMinimumHeight(100)
            verify.txtChanges.setFixedHeight(text_height)

            # If the user accepts the changes than the values are sent to the motor
            # If the user dont accept the changes than the text boxes values return to the
            # current motor configurations
            if verify.exec() == QDialog.DialogCode.Accepted: 
                try:
                    # The server configurations are saved in the config file
                    # The motor configurations are also saved in the config file but
                    # must also be sent to the motor
                    self.logger.info("Starting motor configuration")

                    # for idx in keys:  # Uses the driver properties to send the new values to the motor
                    #     self.motor.set_param(idx, self._changed_settings[idx])
                    #     # setattr(self.motor.driver, self.motor.driver.property_handlers[_], self._changed_settings[_])
                    #     self.logger.info(f"Motor parameter changed: [{idx}] Previous value -> {self._motor_settings[idx]} | New value -> {self._changed_settings[idx]}") 

                    for key in keys:
                        if key in MotorParamsIdx:
                            self.motor.set_param(key, self._changed_settings[key])
                            self.logger.info(f"Motor parameter changed: [{self._config_settings[key.value].TAG}] Previous value -> {self._config_settings[key.value].VALUE} | New value -> {self._changed_settings[key]}")

                        elif key in ServerParamsIdx:
                            self.logger.info(f"Server parameter changed: [{self._config_settings[key.value].TAG}] Previous value -> {self._config_settings[key.value].VALUE} | New value -> {self._changed_settings[key]}")


                    self.signals.changed_settings.emit(self._changed_settings)      # Emits the changes to the main UI
                    self.motor.driver._store_to_flash()                             # Store the new settings to flash.
                    
                    # If everything went ok and the motor parameter was updated then the 
                    # configuration file and the current motor parameters 
                    # must be updated   
                    # #TODO: Atualizar o arquivo de configuração conforme cada parâmetro é atualizado 
                    self._create_backup_config()                                # Creates a backup of the current configuration file
                    self._update_config_file(config_file ,keys)                              # Updates Config file and saves new server configurations

                    if Config.name == "PE 160 Focuser":
                        self._update_config_file(config_file_160 ,keys)                              # Updates Config file and saves new motor configurations
                    elif Config.name == "IAG Focuser":
                        self._update_config_file(config_file_iag ,keys)                              # Updates Config file and saves new motor configurations

                    for key in keys:
                        self._config_settings[key.value].VALUE = self._changed_settings[key]                                               
                
                    
                    update_config()                                                 # Updates the Config object with the new values from config.toml
                    self._changed_settings.clear()                                  # Resets changes dictionary   
                    self._validate_parameters()
                    self.logger.info("Ended motor configuration")
                except Exception as e:
                    self.logger.info(f"Error saving new configuration to motor. {e}")
                    print(e)
            else:
                # If the user do not accept the new configurations than the current configurations are
                # written back in the text boxes
                self._changed_settings.clear()
                self._reset_text_boxes(self._config_settings)



    def _reset_text_boxes(self, settings: ConfigurableSettings):
        """Resets the parameters boxes according to the
        current settings.

        """
        for param in self._config_settings:
            # Signal must be disconnected because validation cannot be called when the
            # values are reset
            if isinstance(param.OBJ, QLineEdit) and isinstance(param.VALUE, str):
                param.OBJ.textChanged.disconnect()
                param.OBJ.setText(param.VALUE)
                param.OBJ.textChanged.connect(self._validate_parameters)

            # elif param.TYPE is int or param.TYPE is float:
            elif isinstance(param.OBJ, QSpinBox) and (isinstance(param.VALUE, int)):
                param.OBJ.valueChanged.disconnect()
                param.OBJ.setValue(param.VALUE)
                param.OBJ.valueChanged.connect(self._validate_parameters)
            elif isinstance(param.OBJ, QDoubleSpinBox) and (isinstance(param.VALUE, float)):
                param.OBJ.valueChanged.disconnect()
                param.OBJ.setValue(param.VALUE)
                param.OBJ.valueChanged.connect(self._validate_parameters)
            elif isinstance(param.OBJ, QCheckBox) and isinstance(param.VALUE, bool):
                # param.OBJ.valueChanged.disconnect()
                param.OBJ.setCheckable(param.VALUE)
                # param.OBJ.valueChanged.connect(self._validate_parameters)


        self._validate_parameters()



    def _login_engineering_mode(self):
        """Opens the dialog window to login/logoff of engineering mode"""
        print(self._motor_settings)
        self._login = LoginForm(self.logged_user)                               # Creates login widget
        # self._login.user.connect(self._logged_user_setter)                      # Connects the user name to the settings window logged user (A method is needed because a property setter cannot be directly used)
        self._login.user.connect(lambda user: setattr(self, 'logged_user', user))
        if self._login.exec() == QDialog.DialogCode.Accepted:                   # If the dialog box closes with an accepted signal
            if self.logged_user == "<b>ADMIN</b>":                                                    # If a user was set
                self.engineering_mode = True                                            # Enters engineering mode
            else:                                                                   # if no user set
                self.engineering_mode = False                                           # Exits engineering mode 



    def _validate_parameters(self):
        """Verifies if a new configuration for the parameters is avaiable"""
        #TODO: Adicionar validação por parâmetro? Considerando limites entre os parâmetros Ex. 'Backlash' não pode ser maior que 'pos_max'

        # Checks values and verifies if changed
        for param in self._config_settings:
            self._set_settings(param)

            # if isinstance(param.OBJ, QLineEdit):
            if param.TYPE is str:
                text = param.OBJ.text().replace(".", "")    # Remove dots from masked IPs
                if text == "":
                    param.OBJ.setStyleSheet("""
                        QLineEdit {border: 1px solid rgb(255,0,0);
                                    background-color: rgba(255,0,0, 20); 
                        border-radius:3}
                    """
                    )
                else:
                    param.OBJ.setStyleSheet("""none""")


                if param.OBJ.text() != param.VALUE:
                    param.OBJ.setProperty("change", True)
                else:
                    param.OBJ.setProperty("change", False)

            elif isinstance(param.OBJ, QSpinBox) or isinstance(param.OBJ, QDoubleSpinBox):
                if param.OBJ.value() != param.VALUE:
                    param.OBJ.setProperty("change", True)
                else:
                    param.OBJ.setProperty("change", False)

            self._update_gui_element(param.OBJ)

    # --- Adjust GUI limits

        # Backlash limits 0~150 steps
        self._config_settings.BACKLASH.OBJ.setMaximum(int(150 * Config.steps_2_encoder * Config.enc_2_microns))
        
        # Max pos limits 6000~12600 steps
        self._config_settings.MAX_POS.OBJ.setMinimum(int(8000 * Config.steps_2_encoder * Config.enc_2_microns * 0.9885853)) # 0.9885853 is the conversion for the maximum possible configuration
        self._config_settings.MAX_POS.OBJ.setMaximum(int(12700 * Config.steps_2_encoder * Config.enc_2_microns * 0.9885853))# 0.9885853 is the conversion for the maximum possible configuration

        # The Park position is limited by the maximum position
        self._config_settings.PARK_POS.OBJ.setMaximum(self._config_settings.MAX_POS.OBJ.value())

        # The Idle current is limited by the running current
        self._config_settings.IDLE_CURRENT.OBJ.setMaximum(self._config_settings.RUN_CURRENT.OBJ.value())

        # The Normal and Low speeds are limited by the High speed, but only if the max speed limit is 
        # lower than the default limits
        if self._config_settings.MAX_SPEED.OBJ.value() < 500:
            self._config_settings.NORMAL_SPEED.OBJ.setMaximum(self._config_settings.MAX_SPEED.OBJ.value())
        else:
            self._config_settings.NORMAL_SPEED.OBJ.setMaximum(500)

        if self._config_settings.MAX_SPEED.OBJ.value() < 167:
            self._config_settings.LOW_SPEED.OBJ.setMaximum(self._config_settings.MAX_SPEED.OBJ.value())
        else:
            self._config_settings.LOW_SPEED.OBJ.setMaximum(167)

    def _update_gui_element(self, widget: QWidget):
        """Updates the GUI element style after an event occured.
        According to QT framework this functions must be executed to update visual elements when a property is changed.
        Re-polish the style to apply CSS changes linked to this property
        
        Parameters
        ----------
        widget : QtWidgets
            Widget to be updated
        """
        w_style = widget.style()
        if w_style:
            w_style.unpolish(widget)
            w_style.polish(widget)
        widget.update()



    def closeEvent(self, event):
        """Event called when the settings window is closed

        Parameters
        ----------
        a0 : QCloseEvent
            Event that caused the window to close

        Returns
        -------
        Emits a signal informing that the window was closed, the main window uses this signal to delete the window
        """
        # If there are changed settings that were not sent to the motor
        # a window appears to inform the user
        self._validate_parameters()

        if self._changed_settings:
            message_window = QMessageBox(self)
            message_window.setWindowTitle("Confirmation")
            message_window.setText("There are new configurations that were not sent to the motor, "
                                   "are you sure you want to exit without saving the configurations?")
            message_window.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            message_window.setIcon(QMessageBox.Icon.Warning)
            resp = message_window.exec()

            if resp == QMessageBox.StandardButton.Yes:
                self.signals.window_closed.emit(True)
                event.accept()
            else:
                event.ignore()    
            
        else:
            self.signals.window_closed.emit(True)
            event.accept()
        
            
#endregion



#TODO: Talvez rodar isso só como um método da SettingsWindow ao invés de ser uma classe separada?
class RetrieveSettings(QThread):
    """Retrieves data from the motor
    - Device IP
    - Backlash
    - Maximum position
    - Park position (not implemented on DMX-ETH)
    - Maximum speed
    - Normal speed
    - Low speed
    
    Signals the progress to update progress bar
    """

    signal_running = pyqtSignal(bool)
    signal_progress = pyqtSignal(int)
    signal_motor_data = pyqtSignal(Motor)

    def __init__(self, motor: Motor):
        """
        Parameters
        ----------
        driver : FocuserDriver
            Motor driver to send commands to retrieve the data.
        """
        super().__init__()

        self.motor = motor
        self.motor_data = Motor(self.motor.model)

    def run(self):
        p = 0
        step_size = int(100/(1+len(MotorParamsIdx)))
        print(f"step size = {step_size}")
        self.signal_progress.emit(p)
        self.signal_running.emit(True)

        resp = self.motor.model
        if resp == MotorModels.ARCUS_DMX_ETH:
            self.motor_data.ID = "Focuser 160"
        elif resp == MotorModels.AMP_MOTOR:
            self.motor_data.ID = "Focuser IAG"
        else:
            self.motor_data.ID = "*Invalid motor ID*"

        self.motor_data._firmware_version = self.motor.firmware_version
            
        # Retrieves all motor parameters
        for param in MotorParamsIdx:
            p += step_size
            self.signal_progress.emit(p)
            if self.motor.get_param(param):
                self.motor_data.parameters[param] = self.motor.parameters[param]

        p = 100
        self.signal_progress.emit(p)
        time.sleep(0.2)
        
        self.signal_motor_data.emit(self.motor_data)
        self.signal_running.emit(False)

