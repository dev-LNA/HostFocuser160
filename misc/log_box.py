from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, 
    QTextEdit,)


import os
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

log_path = resource_path('../assets/ui/LOG.ui')

class LogBox(QWidget):

    closed = pyqtSignal(bool)
    def __init__(self):
        super().__init__()



        uic.loadUi(log_path, self)

        self.txtLog = self.findChild(QTextEdit, 'txtLog')
        self.txtLog: QTextEdit = self.txtLog


    def closeEvent(self, a0):
        self.closed.emit(True)
        return super().closeEvent(a0)