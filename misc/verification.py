import string
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QTextEdit
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

path_to_ui = resource_path('assets/ui/verification.ui')                # Path to login UI                                     

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
