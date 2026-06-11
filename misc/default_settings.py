import string
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton, QMessageBox, QCheckBox, QDialogButtonBox, QLabel
from PyQt6.QtCore import pyqtSignal

from configparser import ConfigParser
import sys
import os

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

path_to_ui = resource_path('assets/ui/default_select.ui')                # Path to login UI

class LoadConfigForm(QDialog):

    _signal_selected_list = pyqtSignal(object)

    def __init__(self, message: str):
        super(LoadConfigForm, self).__init__()

        # Loads Ui file
        uic.loadUi(path_to_ui, self)

        # Creates UI intellisense
        self.cbIpAddress: QCheckBox = self.findChild(QCheckBox, 'cbIpAddress')

        self.cbBacklash: QCheckBox = self.findChild(QCheckBox, 'cbBacklash')

        self.cbPosMax: QCheckBox = self.findChild(QCheckBox, 'cbPosMax')

        self.cbPark: QCheckBox = self.findChild(QCheckBox, 'cbPark')

        self.cbMaxSpeed: QCheckBox = self.findChild(QCheckBox, 'cbMaxSpeed')

        self.cbNormalSpeed: QCheckBox = self.findChild(QCheckBox, 'cbNormalSpeed')

        self.cbMinSpeed: QCheckBox = self.findChild(QCheckBox, 'cbMinSpeed')

        self.cbAcceleration: QCheckBox = self.findChild(QCheckBox, 'cbAcceleration')

        self.cbDeceleration: QCheckBox = self.findChild(QCheckBox, 'cbDeceleration')

        self.cbIdleCurrent: QCheckBox = self.findChild(QCheckBox, 'cbIdleCurrent')

        self.cbRunCurrent: QCheckBox = self.findChild(QCheckBox, 'cbRunCurrent')

        self.cbAccCurrent: QCheckBox = self.findChild(QCheckBox, 'cbAccCurrent')

        self.buttonBox: QDialogButtonBox = self.findChild(QDialogButtonBox, 'buttonBox')

        self.lblInfo: QLabel = self.findChild(QLabel, 'lblInfo')

        self.check_list = (self.cbIpAddress, self.cbBacklash, self.cbPosMax, self.cbPark,
                           self.cbMaxSpeed, self.cbNormalSpeed, self.cbMinSpeed, self.cbAcceleration,
                           self.cbDeceleration, self.cbIdleCurrent, self.cbRunCurrent, self.cbAccCurrent)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.lblInfo.setText(f"Checked items will be changed to its {message} value")

        #Variables
        self.selected_items=[]

    def accept(self):
        for c in self.check_list:
            if c.isChecked():
                self.selected_items.append(c.property('TAG'))   # Gets the TAG for each selected item
        
        for sel in self.selected_items:
            print(f"{sel} selected")

        self._signal_selected_list.emit(self.selected_items)
        
        return super().accept()