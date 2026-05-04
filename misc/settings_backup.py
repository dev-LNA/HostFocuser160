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

from src.utils.constants import constants
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



class SettingsWindow(QMainWindow):

    _signal_window_closed = pyqtSignal(bool)                        # Signal to inform that the window was closed
    _signal_engineering_mode = pyqtSignal(bool)                     # Signal to inform that the engineering mode is activated
    _signal_command_response = pyqtSignal(str)

    _signal_progress = pyqtSignal(int)                              # Progress signal
    _engineering_mode = False                                       # Engineering mode state
    _logged_user = ""                                               # Current logged user

    _motor_settings = dict()                                        # Motor current settings
    _settings_changed = False                                       # Informs if a setting was changed
    _changed_settings = dict()                                      # Dict of settings that were changed, keeping the old values for reference

    _signals_changed_settings = pyqtSignal(dict)

    def __init__(self, motor: Motor, logger: Logger):
        super().__init__()

        if motor.driver.__class__ is not Driver:
            raise RuntimeError("Driver must be of Driver class")
        
        self.motor = motor
        # self.motor.driver: FocuserDriver
        # self.motor.driver = driver                                        # Reference to the motor driver
        self.logger = logger
        
        uic.loadUi(path_to_ui, self)                                # Loads the window UI

        self.ui_elements = UiWidgets(self, "settings")              # Generates UI elements intellisense

    # The QLineEdits must be initialized as 'disabled'. This is changed in engineering mode.
        lineEdits = self.findChildren(QLineEdit)                                        # Makes a list of all QLineEdit widgets
        for _ in lineEdits:                                                             # Connects the engineering mode signal to each QLineEdit setEnabled
            self._signal_engineering_mode.connect(_.setEnabled)                         #  this way when engineering mode is activated the line edits automatically become enabled    
        # self._signal_engineering_mode.disconnect(self.ui_elements.txtPark.setEnabled)   # Park position not implemented in DMX-ETH
        # self.ui_elements.txtPark.setEnabled(False)                                      # Always false because is not implemented #TODO: Implementar posição Park no DMX-ETH

        self._signal_engineering_mode.connect(self.ui_elements.btnSave.setEnabled)      # Save is only allowed in engineering mode

        self.engineering_mode = False                                                   # Initializes engineering mode to false

        self.ui_elements.btnEngineering.clicked.connect(self._log_engineering_mode)     # Connects engineering login button
        self.ui_elements.btnSave.clicked.connect(self._save_settings)                   # Connects save settings button
        self.ui_elements.btnDefault.clicked.connect(self._load_config_values)           # Connects default settings button
        self.ui_elements.btnBackup.clicked.connect(self._load_config_values)            # Connects default settings button
        
        
        self.ui_elements.frameCommand.setVisible(False)                                 # Send commands frame begins not visible
        self._signal_engineering_mode.connect(self.ui_elements.frameCommand.setVisible) # The commands frame is only visible when in engineering mode

        self.ui_elements.btnDefault.setVisible(False)                                   # Defaul configurations button begins not visible
        self._signal_engineering_mode.connect(self.ui_elements.btnDefault.setVisible)   # The default configurations button is only visible in engineering mode

        self.ui_elements.btnBackup.setVisible(False)                                    # Defaul configurations button begins not visible
        self._signal_engineering_mode.connect(self.ui_elements.btnBackup.setVisible)    # The default configurations button is only visible in engineering mode

        self.ui_elements.btnSendCommand.clicked.connect(self._send_test_command)
        self.ui_elements.txtCommand.returnPressed.connect(self._send_test_command)
        self.ui_elements.txtCommand.textChanged.connect(self._command_changed)

        self.ui_elements.lblServerVer_val.setText(Config.server_version)

        self._signal_command_response.connect(self.ui_elements.lblResponse_Val.setText)

        self._config_txt_boxes = {                      # Dictionary holding the txtBoxes objects of the configurations
            MotorParamsIdx.MOTOR_IP : self.ui_elements.txtMotorIP,
            MotorParamsIdx.BACKLASH : self.ui_elements.txtBackComp,
            MotorParamsIdx.MAX_POS : self.ui_elements.txtMaxPos,
            MotorParamsIdx.PARK_POS : self.ui_elements.txtPark,
            MotorParamsIdx.MAX_SPEED : self.ui_elements.txtMaxSpeed,
            MotorParamsIdx.NORMAL_SPEED : self.ui_elements.txtNormalSpeed,
            MotorParamsIdx.LOW_SPEED : self.ui_elements.txtLowSpeed,
        }
        

        # self._progress_bar = QProgressBar()
        # self._progress_bar.setVisible(False)
        # self._progress_bar.setTextVisible(False)
        # self._progress_bar.setMaximumWidth(100)
        self._progress_bar = LoadBar()                                                  # Creates load bar

        self.statusBar().addPermanentWidget(self._progress_bar)                         # Add load bar to status bar, it is not visible by default and is made visible when needed

        self._updater = RetrieveSettings(self.motor)                                   # Initializes thread that reads current settings from the motor

        self._updater._running.connect(self._progress_bar.setVisible)                   # The progress bar visibility is connected to the updater method running signal
        self._updater._signal_progress.connect(self._progress_bar.progress.setValue)    # The progress bar value is connected to the updater method progress
    
        # The motor data is kept in a dictionary and the parse function is responsible to parse the information
        self._updater.signal_motor_data.connect(self._parse_motor_data)

        self._updater._running.connect(self._initialize_motor_settings)                 # When the updater finishes reading the motor the dictionary with the current values must be updated

        self._changed_settings.clear()          # Resets changes dictionary   

        if Config.focuser == "160":
            self._update_settings()                                                         # Updates current settings by reading the values from the motor
        else:
            raise RuntimeError("The IAG settings are not implemented yet")


    def _parse_motor_data(self, data: Motor):
        self.ui_elements.lblFocuser.setText(data.ID)
        self.ui_elements.txtMotorIP.setText(data.parameters[MotorParamsIdx.MOTOR_IP])
        self.ui_elements.lblFirmVer_value.setText(data.firmware_version)
        self.ui_elements.txtBackComp.setText(data.parameters[MotorParamsIdx.BACKLASH])
        self.ui_elements.txtMaxPos.setText(data.parameters[MotorParamsIdx.MAX_POS])
        self.ui_elements.txtPark.setText(data.parameters[MotorParamsIdx.PARK_POS])
        self.ui_elements.txtMaxSpeed.setText(data.parameters[MotorParamsIdx.MAX_SPEED])
        self.ui_elements.txtNormalSpeed.setText(data.parameters[MotorParamsIdx.NORMAL_SPEED])
        self.ui_elements.txtLowSpeed.setText(data.parameters[MotorParamsIdx.LOW_SPEED])

    def _update_settings(self):
        """Updates current settings by reading the values from the motor"""
        self._updater.start()               # Starts the thread
        
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

    def _log_engineering_mode(self):
        """Opens the dialog window to login/logoff of engineering mode"""
        print(self._motor_settings)
        self._login = LoginForm(self.logged_user)                               # Creates login widget
        self._login.user.connect(self._logged_user_setter)                      # Connects the user name to the settings window logged user (A method is needed because a property setter cannot be directly used)
        if self._login.exec() == QDialog.DialogCode.Accepted:                   # If the dialog box closes with an accepted signal
            if self.logged_user:                                                    # If a user was set
                self.engineering_mode = True                                            # Enters engineering mode
            else:                                                                   # if no user set
                self.engineering_mode = False                                           # Exits engineering mode 



    @property
    def engineering_mode(self) -> bool:     # Property to read the engineering mode state
        return self._engineering_mode
    
    @engineering_mode.setter                # Engineering mode setter
    def engineering_mode(self, value: bool):
        self._engineering_mode = value  
        self._signal_engineering_mode.emit(self.engineering_mode)       # When the engineering mode changes signals all slots connected



    @property
    def logged_user(self) -> str:           # Property to read the current logged user
        return self._logged_user
    
    def _logged_user_setter(self, name: str):   # Logged user setter (A method was used in order to be able to connect this method to the signal from the login form)
        self._logged_user = name 
        

    @property
    def motor_settings(self):
        return self._motor_settings
    
    def _send_test_command(self):
        if self.engineering_mode and self.ui_elements.txtCommand.text():   # The button is not supposed to be visible when not in engineering mode, this is just a safeguard
            try:
                self._signal_command_response.emit(self.motor.driver.sendCommand(self.ui_elements.txtCommand.text()))
            except Exception as e:
                print(e)

    def _command_changed(self):
        self.ui_elements.txtCommand.setText(self.ui_elements.txtCommand.text().upper())


    def _set_motor_settings(self, key:MotorParamsIdx, value:str):

        if value == self._motor_settings[key]:
            if key in self._changed_settings:
                print(f"{self._changed_settings}")
                print("deleting key")
                del self._changed_settings[key]
                print(f"{self._changed_settings}")

        if (self._motor_settings[key] != value) or ( (key in self._changed_settings) and self._changed_settings[key] != value):
            self._changed_settings[key] = value      # Indicates that this value has changed and saves the new value
            # self._changed_settings[key] = self._motor_settings[key]      # Indicates that this value has changed and saves the old value for reference
            # self._motor_settings[key] = value
            self._settings_changed = True
            print(f"{key} value changed to {value}")
        else:
            self._settings_changed = False
            print(f"{key} value NOT changed")
        

    def _initialize_motor_settings(self, value):
        if value is False:                                                                  # The motor reading finishes when the _running signal goes to False
            self._motor_settings[MotorParamsIdx.MOTOR_IP] = self.ui_elements.txtMotorIP.text()
            self._motor_settings[MotorParamsIdx.BACKLASH] = self.ui_elements.txtBackComp.text()
            self._motor_settings[MotorParamsIdx.MAX_POS] = self.ui_elements.txtMaxPos.text()
            self._motor_settings[MotorParamsIdx.PARK_POS] = self.ui_elements.txtPark.text()
            self._motor_settings[MotorParamsIdx.MAX_SPEED] = self.ui_elements.txtMaxSpeed.text()
            self._motor_settings[MotorParamsIdx.NORMAL_SPEED] = self.ui_elements.txtNormalSpeed.text()
            self._motor_settings[MotorParamsIdx.LOW_SPEED] = self.ui_elements.txtLowSpeed.text()
            

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

        self._signal_window_closed.emit(True)
        return super().closeEvent(a0)
    

    def _save_settings(self):                                                                       # TODO: Terminar de implementar
            """Save the values in the text boxes in the motor                                           # TODO: Vai ser necessário rodar em uma thread pra não travar a gui?
            Checks if the value in the text box changed in relation to the one read from the motor
        during the initialization, and if the value has changed sends the command to the motor to 
        change the setting value."""
 
            # self._changed_settings.clear()          # Resets changes dictionary         
        # Device IP
            self._set_motor_settings(MotorParamsIdx.MOTOR_IP, self.ui_elements.txtMotorIP.text())

        # Backlash compensation
            self._set_motor_settings(MotorParamsIdx.BACKLASH, self.ui_elements.txtBackComp.text())
            # if self._settings_changed:
            #     self.motor.driver.backlash = self._motor_settings["BACKLASH"]
        # Max position
            self._set_motor_settings(MotorParamsIdx.MAX_POS, self.ui_elements.txtMaxPos.text())
            # if self._settings_changed:
                # current_pos = self.motor.driver.position                                  # Reads the current position
                # self.motor.driver.max_pos = self._motor_settings["MAX_POS"]         # Saves new max pos value
                # if int(self._motor_settings["MAX_POS"]) < current_pos:            # If the new max position is lower than the current position informs that a homing is needed    #TODO: É necessário mesmo?                
                #     print("Necessário realizar homing")                            # TODO: Se o novo valor máximo for menor que a posição atual vai ser necessário realizar o homing para garantir que a posição atual vai ser válida dentro do novo limite
        # Park position
            self._set_motor_settings(MotorParamsIdx.PARK_POS, self.ui_elements.txtPark.text())
        # Max speed
            self._set_motor_settings(MotorParamsIdx.MAX_SPEED, self.ui_elements.txtMaxSpeed.text())  #TODO: No firmware do motor está limitado em 214400
        # Normal speed
            self._set_motor_settings(MotorParamsIdx.NORMAL_SPEED, self.ui_elements.txtNormalSpeed.text())
        # Normal speed
            self._set_motor_settings(MotorParamsIdx.LOW_SPEED, self.ui_elements.txtLowSpeed.text())

            if self._changed_settings:                       # If the changes dictionary has any elements then a setting was changed and the command store must be executed
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

                if verify.exec() == QDialog.DialogCode.Accepted: 
                    try:

                        self.logger.info("Starting motor configuration")
                        self._create_backup_config()                        # Salva um backup das configurações atuais do motor
                        # If the motor IP is changed it is important to keep the config file updated so that when the server is restarted the new IP address is saved   
                        #TODO: Vai ser necessário salvar todas as novas configurações e não só o IP
                        self._update_config_file(keys)
                        # if 'DEVICE_IP' in keys:
                        #     self.motor.driver.device_IP = self._motor_settings["DEVICE_IP"]
                        #     with open(config_file, 'r') as f:
                        #         config = toml.load(f)

                        #     if Config.focuser == '160':
                        #         config['Device']['ip_160'] = self._changed_settings["DEVICE_IP"]
                        #         Config.device_ip = config['Device']['ip_160'] # get_toml('Device', 'ip_160')
                        #     elif Config.focuser == 'IAG':
                        #         config['Device']['ip_iag'] = self._changed_settings["DEVICE_IP"]
                        #         Config.device_ip = config['Device']['ip_iag'] # get_toml('Device', 'ip_iag')

                        #     with open(config_file, 'w') as f:
                        #         toml.dump(config, f)

                        for _ in keys:  # Uses the driver properties to send the new values to the motor
                            setattr(self.motor.driver, self.motor.driver.property_handlers[_], self._changed_settings[_])
                            self.logger.info(f"Motor parameter changed: [{_}] Previous value -> {self._motor_settings[_]} | New value -> {self._changed_settings[_]}") 

                        self._signals_changed_settings.emit(self._changed_settings)     # Emits the changes to the main UI
                        self.motor.driver._store_to_flash()                                   # Store the new settings to flash.
                        self._changed_settings.clear()                                  # Resets changes dictionary   
                        self.logger.info("Ended motor configuration")
                    except Exception as e:
                        self.logger.info(f"Error saving new configuration to motor. {e}")
                        print(e)
                else:
                    self.ui_elements.txtMotorIP.setText(self._motor_settings["MOTOR_IP"])
                    self.ui_elements.txtBackComp.setText(self._motor_settings["BACKLASH"])
                    self.ui_elements.txtMaxPos.setText(self._motor_settings["MAX_POS"])
                    self.ui_elements.txtPark.setText(self._motor_settings["PARK"])
                    self.ui_elements.txtMaxSpeed.setText(self._motor_settings["MAX_SPEED"])
                    self.ui_elements.txtNormalSpeed.setText(self._motor_settings["NORMAL_SPEED"])
                    self.ui_elements.txtLowSpeed.setText(self._motor_settings["LOW_SPEED"])


    def _create_backup_config(self):
        try:
            shutil.copy(config_file, config_file_backup)            #TODO: 'copy' do not retain the metadata, if metadata is needed change to '.copy2'
            self.logger.info(f"Created backup configuration file: {config_file_backup}")

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

    _running = pyqtSignal(bool)
    _signal_progress = pyqtSignal(int)

    motor_data = Motor(constants.ARCUS_DMX_ETH)

    signal_motor_data = pyqtSignal(Motor)


    def __init__(self, motor: Motor):
        """
        Parameters
        ----------
        driver : FocuserDriver
            Motor driver to send commands asking for the data.
        """
        super().__init__()


        self.motor = motor


    def run(self):
        p = 0
        step_size = 12
        self._signal_progress.emit(p)
        self._running.emit(True)

        resp = self.motor.ID
        if resp == constants.ID_FOCUSER_160:
            self.motor_data.ID = "Focuser 160"
        elif resp == constants.ID_FOCUSER_IAG:
            self.motor_data.ID = "Focuser IAG"
        else:
            self.motor_data.ID = "*Invalid motor ID*"

        self.motor_data.firmware_version = self.motor.driver.read_firmware_version()
            
        for param in MotorParamsIdx:
            p += step_size
            self._signal_progress.emit(p)
            self.motor_data.parameters[param] = self.motor.get_param[param]

        # p += step_size
        # self._signal_progress.emit(p)
        # self.motor_data.parameters[MotorParams.MOTOR_IP] = self.motor.get_param(MotorParams.MOTOR_IP)
        # p += step_size
        # self._signal_progress.emit(p)
        # # self._signal_backlash.emit(self.motor.driver.backlash)
        # self.motor_data.parameters[MotorParams.BACKLASH] = self.motor.get_param(MotorParams.BACKLASH)
        # p += step_size
        # self._signal_progress.emit(p)
        # self.motor_data.parameters[MotorParams.MAX_POS] = self.motor.get_param(MotorParams.MAX_POS)
        # p += step_size
        # self._signal_progress.emit(p)
        # self.motor_data.parameters[MotorParams.PARK_POS] = self.motor.get_param(MotorParams.PARK_POS)
        # p += step_size
        # self._signal_progress.emit(p)
        # self.motor_data.parameters[MotorParams.MAX_SPEED] = self.motor.get_param(MotorParams.MAX_SPEED)
        # p += step_size
        # self._signal_progress.emit(p)
        # self.motor_data.parameters[MotorParams.NORMAL_SPEED] = self.motor.get_param(MotorParams.NORMAL_SPEED)
        # p += step_size
        # self._signal_progress.emit(p)
        # self.motor_data.parameters[MotorParams.LOW_SPEED] = self.motor.get_param(MotorParams.LOW_SPEED)
        p = 100
        self._signal_progress.emit(p)
        time.sleep(0.2)
        
        self.signal_motor_data.emit(self.motor_data)
        self._running.emit(False)

