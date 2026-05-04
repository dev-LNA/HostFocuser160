from ast import Attribute

from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QLineEdit, QProgressBar, QDialog
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFontMetrics, QKeyEvent
# from src.core.exceptions import NotImplementedException
from misc.load_bar import LoadBar
from misc.ui_intellisense import UiWidgets
from misc.login_form import LoginForm
from misc.default_settings import LoadConfigForm
from misc.verification import VerificationDialog

# from src.interface.dmx_eth import FocuserDriver
# from src.interface.focuser_driver import FocuserDriver
from src.core.config import Config, get_toml  

from src.utils.constants import constants, MotorModels
from src.interface.motor_driver import Driver
from src.utils.motor import Motor, MotorParamsIdx

from logging import Logger
from datetime import datetime

import sys
from os import path
import toml
import shutil

import time




def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)

path_to_ui = resource_path('../assets/ui/settings.ui')              # Path to settings window UI
config_dir = "src/config/"
config_file = config_dir + "config.toml" #"src/config/config.toml"
config_file_backup = config_dir + "config_backup.toml" #"src/config/config_backup.toml"                #TODO: Possibilitar definir o nome do arquivo? Talvez nomear de acordo com a data que foi criado
config_file_default = config_dir + "config_default.toml" #"src/config/config_default.toml"



class SettingsSignals(QObject):
    window_closed = pyqtSignal(bool)
    engineering_mode = pyqtSignal(bool)
    command_response = pyqtSignal(str)
    progress = pyqtSignal(int)
    changed_settings = pyqtSignal(dict)

class SettingsWindow(QMainWindow):

    signals = SettingsSignals()

    _engineering_mode = False                                       # Engineering mode state
    _logged_user = ""                                               # Current logged user

    _motor_settings = dict()                                        # Motor current settings
    _settings_changed = False                                       # Informs if a setting was changed
    _changed_settings = dict()                                      # Dict of settings that were changed, keeping the old values for reference

    def __init__(self, motor: Motor, logger: Logger):
        super().__init__()

        if type(motor.driver).__base__ is not Driver:
            raise RuntimeError("Driver must be of Driver class")
        
        self.motor = motor
        self.logger = logger
        
        uic.loadUi(path_to_ui, self)                                # Loads the window UI

        self.ui_elements = UiWidgets(self, "settings")              # Generates UI elements intellisense

    # The QLineEdits must be initialized as 'disabled'. This is changed in engineering mode.
        lineEdits = self.findChildren(QLineEdit)                                        # Makes a list of all QLineEdit widgets
        for _ in lineEdits:                                                             # Connects the engineering mode signal to each QLineEdit setEnabled
            self.signals.engineering_mode.connect(_.setEnabled)                         #  this way when engineering mode is activated the line edits automatically become enabled   
            

        self.signals.engineering_mode.connect(self.ui_elements.btnSave.setEnabled)      # Save button is only enabled in engineering mode

        self.engineering_mode = False                                                   # Initializes engineering mode to false

        self.ui_elements.btnEngineering.clicked.connect(self._login_engineering_mode)   # Connects engineering login button
        self.ui_elements.btnSave.clicked.connect(self._save_settings)                   # Connects save settings button
        self.ui_elements.btnDefault.clicked.connect(self._load_config_values)           # Connects default settings button
        self.ui_elements.btnBackup.clicked.connect(self._load_config_values)            # Connects default settings button
        
        
        self.ui_elements.frameCommand.setVisible(False)                                 # Send commands frame begins not visible
        self.signals.engineering_mode.connect(self.ui_elements.frameCommand.setVisible) # The commands frame is only visible when in engineering mode

        self.ui_elements.btnDefault.setVisible(False)                                   # Defaul configurations button begins not visible
        self.signals.engineering_mode.connect(self.ui_elements.btnDefault.setVisible)   # The default configurations button is only visible in engineering mode

        self.ui_elements.btnBackup.setVisible(False)                                    # Defaul configurations button begins not visible
        self.signals.engineering_mode.connect(self.ui_elements.btnBackup.setVisible)    # The default configurations button is only visible in engineering mode

        self.ui_elements.btnSendCommand.clicked.connect(self._send_test_command)
        self.ui_elements.txtCommand.returnPressed.connect(self._send_test_command)
        self.ui_elements.txtCommand.textChanged.connect(self._command_changed)

        self.ui_elements.lblServerVer_val.setText(Config.server_version)

        self.signals.command_response.connect(self.ui_elements.lblResponse_Val.setText)

        # Dictionary holding the txtBoxes objects of the configurations
        self._config_txt_boxes = {                      
            MotorParamsIdx.MOTOR_IP : self.ui_elements.txtMotorIP,
            MotorParamsIdx.BACKLASH : self.ui_elements.txtBackComp,
            MotorParamsIdx.MAX_POS : self.ui_elements.txtMaxPos,
            MotorParamsIdx.PARK_POS : self.ui_elements.txtPark,
            MotorParamsIdx.MAX_SPEED : self.ui_elements.txtMaxSpeed,
            MotorParamsIdx.NORMAL_SPEED : self.ui_elements.txtNormalSpeed,
            MotorParamsIdx.LOW_SPEED : self.ui_elements.txtLowSpeed,
            MotorParamsIdx.MAX_STEP : self.ui_elements.txtMaxStep
        }

        self._progress_bar = LoadBar()                                                  # Creates load bar

        self.statusBar().addPermanentWidget(self._progress_bar)                         # Add load bar to status bar, it is not visible by default and is made visible when needed

        # The updater runs on a different thread and retrieves the motor current configured parameters
        self._updater = RetrieveSettings(self.motor)

        self._updater.signal_running.connect(self._progress_bar.setVisible)                   # The progress bar visibility is connected to the updater method running signal
        self._updater.signal_progress.connect(self._progress_bar.progress.setValue)    # The progress bar value is connected to the updater method progress
    
        # The motor data is kept in a dictionary and the parse function is responsible to parse the information
        self._updater.signal_motor_data.connect(self._parse_motor_data)

        # When the updater finishes reading the motor the dictionary with the current values must be updated
        self._updater.signal_running.connect(self._initialize_motor_settings)                 

        self._changed_settings.clear()          # Resets changes dictionary   

        if Config.focuser == "160":
            self._update_settings()                                                         # Runs the _updater to retrieve the current motor parameters
        else:
            raise RuntimeError("The IAG settings are not implemented yet")                  #TODO: Implementar configurações do IAG


#region  ========== PROPERTIES ========== # 

    @property
    def engineering_mode(self) -> bool:     # Property to read the engineering mode state
        return self._engineering_mode
    @engineering_mode.setter                # Engineering mode setter
    def engineering_mode(self, value: bool):
        self._engineering_mode = value  
        self.signals.engineering_mode.emit(self.engineering_mode)       # When the engineering mode changes signals all slots connected

    @property
    def logged_user(self) -> str:           # Property to read the current logged user
        return self._logged_user
    #TODO: Verificar outra forma de fazer isso. E se é necessário, acho que essa infomração nem existe atualmente.
    def _logged_user_setter(self, name: str):   # Logged user setter (A method was used in order to be able to connect this method to the signal from the login form)
        self._logged_user = name 

    @property
    def motor_settings(self):
        return self._motor_settings

#endregion

#region  ========== METHODS ========== # 

    def _update_settings(self):
        """Updates current settings by reading the values from the motor
        The thread will run one time only"""
        self._updater.start()               # Starts the thread

    def _initialize_motor_settings(self, value):
        """Updates the dictionary with the values retrieved from the motor
        This method is called automatically when the _updater thread
        finishes its execution"""
        if value is False:                                                                  # The motor reading finishes when the _running signal goes to False
            for idx in MotorParamsIdx:
                self._motor_settings[idx] = self._config_txt_boxes[idx].text()

    def _parse_motor_data(self, data: Motor):
        """Parses the motor data and updates the GUI with the information
        retrieved from the motor
        This method is called automatically when the _updater thread
        finishes its execution"""

        self.ui_elements.lblFocuser.setText(data.ID)
        self.ui_elements.lblFirmVer_value.setText(data.firmware_version)

        for idx in MotorParamsIdx:
            self._config_txt_boxes[idx].setText(data.parameters[idx])

    def _set_motor_settings(self, key:MotorParamsIdx, value:str):
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

    def _update_config_file(self, keys: str):

        with open(config_file, 'r') as f:
            config = toml.load(f)
            for k in keys:
                if k == MotorParamsIdx.MOTOR_IP:
                    if Config.focuser == '160':
                        config['Device']['ip_160'] = self._changed_settings[MotorParamsIdx.MOTOR_IP]
                        Config.device_ip = config['Device']['ip_160'] # get_toml('Device', 'ip_160')
                    elif Config.focuser == 'IAG':
                        config['Device']['ip_iag'] = self._changed_settings[MotorParamsIdx.MOTOR_IP]
                        Config.device_ip = config['Device']['ip_iag'] # get_toml('Device', 'ip_iag')
                else:
                    # config['Device'][k.lower()] = int(self._changed_settings[k])
                    config['Device'][self.motor.parameters[k].NAME] = int(self._changed_settings[k])

        with open(config_file, 'w') as f:
            toml.dump(config, f)

    def _load_config_values(self):
        """Opens the dialog window to confirm loading of default configurations"""
        if self.sender() is self.ui_elements.btnDefault:
            cfg_file = config_file_default
            msg = "DEFAULT"
            self.logger.info("Loading default motor configuration")
        elif self.sender() is self.ui_elements.btnBackup:
            cfg_file = config_file_backup
            msg = "BACKUP"
            self.logger.info("Loading backup motor configuration")

        self._default_widget = LoadConfigForm(msg)
        if self._default_widget.exec() == QDialog.DialogCode.Accepted:
            # If accepted must take the selected values and load them in the boxes
            for conf_key in self._config_txt_boxes.keys():              # Check each 
                if conf_key in self._default_widget.selected_items:     # If a configuration was selected in the Default Window
                    # default_config = self._get_config(conf_key, config_file_default)
                    # self._config_txt_boxes[conf_key].setText(default_config)
                    if conf_key == "MOTOR_IP":
                        if Config.focuser == "160":
                            config = get_toml('Device', 'ip_160', cfg_file)
                        elif Config.focuser == "IAG":
                            config = get_toml('Device', 'ip_iag', cfg_file)
                    else:
                        config = str(get_toml('Device', conf_key.lower(), cfg_file))

                    self._config_txt_boxes[conf_key].setText(config)       

        else:
            print("DO NOT RETURN TO DEFAULT VALUES")
        self._default_widget.destroy()


    def _login_engineering_mode(self):
        """Opens the dialog window to login/logoff of engineering mode"""
        print(self._motor_settings)
        self._login = LoginForm(self.logged_user)                               # Creates login widget
        self._login.user.connect(self._logged_user_setter)                      # Connects the user name to the settings window logged user (A method is needed because a property setter cannot be directly used)
        if self._login.exec() == QDialog.DialogCode.Accepted:                   # If the dialog box closes with an accepted signal
            if self.logged_user:                                                    # If a user was set
                self.engineering_mode = True                                            # Enters engineering mode
            else:                                                                   # if no user set
                self.engineering_mode = False                                           # Exits engineering mode 


    def closeEvent(self, a0):
        """Event called when the settings window is closed

        Parameters
        ----------
        a0 : QCloseEvent
            Event that caused the window to close

        Returns
        -------
        Emits a signal informing that the window was closed, the main window uses this signal to delete the window
        """

        self.signals.window_closed.emit(True)
        return super().closeEvent(a0)
   




#endregion




        





    def _save_settings(self):                                                                       # TODO: Terminar de implementar
        """Save to the motor the values configured in the text boxes                                           # TODO: Vai ser necessário rodar em uma thread pra não travar a gui?
        Checks if the value in the text box changed in relation to the one read from the motor
        during the initialization, and if the value has changed sends the command to the motor to 
        change the setting value."""
 
        for idx in MotorParamsIdx:
            self._set_motor_settings(idx, self._config_txt_boxes[idx].text())

        # If the "_changed_settings" dictionary has any elements than a setting was changed and the command store must be executed
        if self._changed_settings:                       
            verify = VerificationDialog()
            text = ""
            keys, values = zip(*self._changed_settings.items())
            for i in range(0, len(keys)):
                text += f"<font color=red> {keys[i]}</font>: {self._motor_settings[keys[i]]} -> {values[i]} <br>"
            
            text += f"<br>"
            text += f"<font color=red> * The motor must be restarted for the changes to take effect </font>"
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

                    self.logger.info("Starting motor configuration")
                    self._create_backup_config()                                # Creates a backup of the current configuration file
                    self._update_config_file(keys)
                    for idx in keys:  # Uses the driver properties to send the new values to the motor

                        self.motor.set_param(idx, self._changed_settings[idx])
                        # setattr(self.motor.driver, self.motor.driver.property_handlers[_], self._changed_settings[_])
                        self.logger.info(f"Motor parameter changed: [{idx}] Previous value -> {self._motor_settings[idx]} | New value -> {self._changed_settings[idx]}") 

                    self.signals.changed_settings.emit(self._changed_settings)      # Emits the changes to the main UI
                    self.motor.driver._store_to_flash()                             # Store the new settings to flash.
                    
                    # If everything went ok and the motor parameter was updated than the current motor parameters 
                    # must be updated in "_motor_settings"
                    for idx in keys:
                        self._motor_settings[idx] = self._changed_settings[idx]

                    self._changed_settings.clear()                                  # Resets changes dictionary   
                    self.logger.info("Ended motor configuration")
                except Exception as e:
                    self.logger.info(f"Error saving new configuration to motor. {e}")
                    print(e)
            else:
                self._changed_settings.clear()
                for idx in MotorParamsIdx:
                    self._config_txt_boxes[idx].setText(self._motor_settings[idx])



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
        self.motor_data = Motor()

    def run(self):
        p = 0
        step_size = 12
        self.signal_progress.emit(p)
        self.signal_running.emit(True)

        resp = self.motor.model
        if resp == MotorModels.ARCUS_DMX_ETH:
            self.motor_data.ID = "Focuser 160"
        elif resp == MotorModels.AMP_MOTOR:
            self.motor_data.ID = "Focuser IAG"
        else:
            self.motor_data.ID = "*Invalid motor ID*"

        self.motor_data.firmware_version = self.motor.firmware_version
            
        # Retrieves all motor parameters
        for param in MotorParamsIdx:
            p += step_size
            self.signal_progress.emit(p)
            self.motor_data.parameters[param] = self.motor.get_param(param)

        p = 100
        self.signal_progress.emit(p)
        time.sleep(0.2)
        
        self.signal_motor_data.emit(self.motor_data)
        self.signal_running.emit(False)

