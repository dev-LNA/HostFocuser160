from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QLineEdit, QFrame, QToolButton, QDialog, QPushButton, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

from misc.login_form import LoginForm
from src.core.config import get_toml
from logging import Logger

import sys
import os
import toml
import shutil

from typing import NamedTuple
from enum import StrEnum

def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # No executável, sys._MEIPASS é a raiz da pasta temporária
        base_path = sys._MEIPASS
    else:
        # No desenvolvimento, a base é a pasta raiz do projeto (onde está o main4.py)
        # Como este arquivo está em misc, pegamos o pai dele
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    return os.path.normpath(os.path.join(base_path, relative_path))

path_to_ui = resource_path('assets/ui/server_settings.ui')              # Path to settings window UI
config_dir = resource_path('src/config')#"src/config/"
config_file = config_dir + "config.toml" #"src/config/config.toml"
config_file_backup = config_dir + "config_backup.toml" #"src/config/config_backup.toml"                #TODO: Possibilitar definir o nome do arquivo? Talvez nomear de acordo com a data que foi criado
config_file_default = config_dir + "config_default.toml" #"src/config/config_default.toml"


class SettingsAttributes(NamedTuple):
    NAME: str
    OBJ: QLineEdit

class ConfigurableSettings(NamedTuple):
    IP_ADDRESS : SettingsAttributes
    PUB_PORT: SettingsAttributes
    REP_PORT: SettingsAttributes

class ServerSettingsSignals(QObject):
    window_closed = pyqtSignal(bool)
    logged = pyqtSignal(bool)

class ServerSettingsWindow(QMainWindow):

    signals = ServerSettingsSignals()
    _logged = False
    _logged_user = ''

    def __init__(self, logger: Logger):
            super().__init__()

            self.logger = logger
            self.current_config = dict()

            uic.loadUi(path_to_ui, self)

            self.frameSettings = self.findChild(QFrame, 'frameSettings')
            self.frameSettings: QFrame = self.frameSettings

            self.txtSocketIP = self.findChild(QLineEdit, 'txtSocketIP')
            self.txtSocketIP: QLineEdit = self.txtSocketIP

            self.txtPubPort = self.findChild(QLineEdit, 'txtPubPort')
            self.txtPubPort: QLineEdit = self.txtPubPort

            self.txtRepPort = self.findChild(QLineEdit, 'txtRepPort')
            self.txtRepPort: QLineEdit = self.txtRepPort

            self.txtServerVersion = self.findChild(QLineEdit, 'txtServerVersion')
            self.txtServerVersion: QLineEdit = self.txtServerVersion

            self.btnLogIn = self.findChild(QToolButton, 'btnLogIn')
            self.btnLogIn: QToolButton = self.btnLogIn

            self.btnSave = self.findChild(QPushButton, 'btnSave')
            self.btnSave: QPushButton = self.btnSave

            self.btnReturn = self.findChild(QToolButton, 'btnReturn')
            self.btnReturn: QToolButton = self.btnReturn

            self.btnDefault = self.findChild(QToolButton, 'btnDefault')
            self.btnDefault: QToolButton = self.btnDefault

            self.btnLogIn.clicked.connect(self._login)
            self.btnSave.clicked.connect(self._save_new_settings)
            self.btnReturn.clicked.connect(self._load_backup_settings)
            self.btnDefault.clicked.connect(self._load_backup_settings)

            self.signals.logged.connect(self.frameSettings.setEnabled)
            self.signals.logged.connect(self.txtSocketIP.setEnabled)
            self.signals.logged.connect(self.txtPubPort.setEnabled)
            self.signals.logged.connect(self.txtRepPort.setEnabled)
            self.signals.logged.connect(self.btnSave.setEnabled)
            self.signals.logged.connect(self.btnReturn.setEnabled)
            self.signals.logged.connect(self.btnDefault.setEnabled)

            self._read_settings()


            self.server_settings = ConfigurableSettings(
                IP_ADDRESS=SettingsAttributes("ip_address", self.txtSocketIP),
                PUB_PORT=SettingsAttributes("port_pub", self.txtPubPort),
                REP_PORT=SettingsAttributes("port_rep", self.txtRepPort)
            )


    @property
    def logged(self):
        return self._logged
    @logged.setter
    def logged(self, val: bool):
        self._logged = val
        self.signals.logged.emit(val)
        print(val)


    @property
    def logged_user(self):
        return self._logged_user
    @logged_user.setter
    def logged_user(self, user: str):
        self._logged_user = user



    def _read_settings(self):
         with open(config_file, 'r') as f:
            self.config = toml.load(f)

            self.txtServerVersion.setText(self.config["General"]["version"])
            self.txtSocketIP.setText(self.config["Network"]["ip_address"])
            self.txtPubPort.setText(str(self.config["Network"]["port_pub"]))
            self.txtRepPort.setText(str(self.config["Network"]["port_rep"]))

            # self.current_config = {
            #     "ip_address" : self.txtSocketIP.text(),
            #     "port_pub" : self.txtPubPort.text(),
            #     "port_rep" : self.txtRepPort.text()
            # }

    def _create_backup_config(self, backup_file_path: str = config_file_backup):
        """Creates a backup file of the current configurations

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

    def _save_new_settings(self):

        confirm = QMessageBox()                                                                           # Creates confirmation window
        confirm.setWindowTitle("Confirmation")                                                                   # Sets window title
        confirm.setText("Are you sure you want to change the server settings?")                                                                   # Sets window message
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)        # Sets window buttons
        confirm = confirm.exec()                                                                            # Shows window
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self._create_backup_config()
                for setting in self.server_settings:
                    if isinstance(self.config["Network"][setting.NAME], int):
                        if self.config["Network"][setting.NAME] != int(setting.OBJ.text()):
                            self.config["Network"][setting.NAME] = int(setting.OBJ.text())
                    else:
                        if self.config["Network"][setting.NAME] != setting.OBJ.text():
                            self.config["Network"][setting.NAME] = setting.OBJ.text()
                            

                with open(config_file, 'w') as f:
                    toml.dump(self.config, f)

            except Exception as e:
                self.logger.error(e)

        else:
            for setting in self.server_settings:
                setting.OBJ.setText( str(self.config["Network"][setting.NAME]) )

    def _load_backup_settings(self):
        if self.sender() is self.btnDefault:
            cfg_file = config_file_default
            self.logger.info("Loading default server configuration")
        elif self.sender() is self.btnReturn:
            cfg_file = config_file_backup
            self.logger.info("Loading backup server configuration")
    
        for setting in self.server_settings:

            backup_value = get_toml('Network', setting.NAME, cfg_file)

            if isinstance(self.config["Network"][setting.NAME], int):
                if self.config["Network"][setting.NAME] != int(backup_value):
                    setting.OBJ.setText(str(backup_value))
            else:
                if self.config["Network"][setting.NAME] != setting.OBJ.text():
                    setting.OBJ.setText(backup_value)


    def _validate_parameters(self):
        for setting in self.server_settings:
            if setting.OBJ.text() != str(self.config["Network"][setting.OBJ.text()]):
                ...


    def _login(self):
        
        self._login_window = LoginForm(self.logged_user)                               # Creates login widget
        self._login_window.user.connect(lambda user: self.__setattr__("logged_user", user))                      # Connects the user name to the settings window logged user (A method is needed because a property setter cannot be directly used)
        if self._login_window.exec() == QDialog.DialogCode.Accepted:                   # If the dialog box closes with an accepted signal
            if self.logged_user:                                                    # If a user was set
                self.logged = True                                            # Enters engineering mode
            else:                                                                   # if no user set
                self.logged = False                                           # Exits engineering mode 

    def closeEvent(self, event):
        self.signals.window_closed.emit(True)