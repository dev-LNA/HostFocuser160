import string
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import pyqtSignal

from configparser import ConfigParser
import sys
from os import path


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)

path_to_ui = resource_path('../assets/ui/login_form.ui')                # Path to login UI
path_to_psw = resource_path('psw.cfg')                               # Path to configurations        # TODO: colocar em outro lugar? Vai ter mais configurações no mesmo arquivo? mudar nome do arquivo?

                                                        

class LoginForm(QDialog):
    user = pyqtSignal(str)

    def __init__(self, current_user: str=""):
        super(LoginForm, self).__init__()

        uic.loadUi(path_to_ui, self)                                    # Loads Ui file

    # Creates UI intellisense
        self.txtPassword = self.findChild(QLineEdit, 'txtPassword')     
        self.txtPassword: QLineEdit = self.txtPassword

        self.btnLogin = self.findChild(QPushButton, 'btnLogin')
        self.btnLogin: QPushButton = self.btnLogin

        self.btnLogin.clicked.connect(self._handle_login_logoff)        # Connects button to method

        self._current_user = current_user                               # Initializes current user with the one passed from the settings window
        if self._current_user:                                          # Checks if is not empty. 
            self.txtPassword.setEnabled(False)                          # If it is not empty than it is already logged in, so the password box is
            self.btnLogin.setText("Logoff")                             #  disabled and the button text changes to 'logoff'


        self._config = ConfigParser()                                   # Creates configParse
        self._config.read(resource_path(path_to_psw))                # Reads and parses the config file

            
        
    def _handle_login_logoff(self):
        """Handles engineering admin login and logoff"""
        if self._current_user == "":                                            # If not logged in
            if self.txtPassword.text() == self._config['USER']['password']:         # Checks if entered password matches the one configured
                self.user.emit("admin")                                                 # If matches signals to settings window that the new user is "admin"
                self.accept()                                                           # Signals accept and closes dialog box
            else:
                QMessageBox.warning(                                                    # If don't match shows error message and keeps dialog box open
                    self, 'Error', 'Bad user or password')
        else:                                                                   # If already logged in
            self.user.emit("")                                                      # Signals to settings window that no user is connected
            self.accept()                                                           # Signals accept and closes dialog box