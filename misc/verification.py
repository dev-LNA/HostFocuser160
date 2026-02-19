import string
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QTextEdit
from PyQt6.QtCore import pyqtSignal

from configparser import ConfigParser
import sys
from os import path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)

path_to_ui = resource_path('../assets/ui/verification.ui')                # Path to login UI                                     

class VerificationDialog(QDialog):
    def __init__(self):
        super(VerificationDialog, self).__init__()

        uic.loadUi(path_to_ui, self)                                    # Loads Ui file
        
                    
        btnBox = self.findChild(QDialogButtonBox, 'btnConfirmation')
        btnBox: QDialogButtonBox = btnBox

        btnSaveAll = btnBox.button(QDialogButtonBox.StandardButton.SaveAll)
        btnSaveAll.clicked.connect(self._saveAll)

        btnDiscard = btnBox.button(QDialogButtonBox.StandardButton.Discard)
        btnDiscard.clicked.connect(self._discard)

        self.txtChanges = self.findChild(QTextEdit, 'txtChanges')
        self.txtChanges: QTextEdit = self.txtChanges


    def _saveAll(self):
        self.accept()

    def _discard(self):
        self.reject()
