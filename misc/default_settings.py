import string
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton, QMessageBox, QCheckBox, QDialogButtonBox
from PyQt6.QtCore import pyqtSignal

from configparser import ConfigParser
import sys
from os import path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)

path_to_ui = resource_path('../assets/ui/default_select.ui')                # Path to login UI

class DefaultForm(QDialog):

    _signal_selected_list = pyqtSignal(object)

    def __init__(self):
        super(DefaultForm, self).__init__()

        # Loads Ui file
        uic.loadUi(path_to_ui, self)

        # Creates UI intellisense
        self.cbIpAddress = self.findChild(QCheckBox, 'cbIpAddress')     
        self.cbIpAddress: QCheckBox = self.cbIpAddress

        self.cbBacklash = self.findChild(QCheckBox, 'cbBacklash')     
        self.cbBacklash: QCheckBox = self.cbBacklash

        self.cbPosMax = self.findChild(QCheckBox, 'cbPosMax')     
        self.cbPosMax: QCheckBox = self.cbPosMax

        self.cbPark = self.findChild(QCheckBox, 'cbPark')     
        self.cbPark: QCheckBox = self.cbPark

        self.cbMaxSpeed = self.findChild(QCheckBox, 'cbMaxSpeed')     
        self.cbMaxSpeed: QCheckBox = self.cbMaxSpeed

        self.cbNormalSpeed = self.findChild(QCheckBox, 'cbNormalSpeed')     
        self.cbNormalSpeed: QCheckBox = self.cbNormalSpeed

        self.cbMinSpeed = self.findChild(QCheckBox, 'cbMinSpeed')     
        self.cbMinSpeed: QCheckBox = self.cbMinSpeed

        self.buttonBox = self.findChild(QDialogButtonBox, 'buttonBox')     
        self.buttonBox: QDialogButtonBox = self.buttonBox

        self.check_list = (self.cbIpAddress, self.cbBacklash, self.cbPosMax, self.cbPark,
                           self.cbMaxSpeed, self.cbNormalSpeed, self.cbMinSpeed)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

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