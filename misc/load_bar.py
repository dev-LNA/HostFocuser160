from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QProgressBar
from PyQt6.QtCore import QThread, pyqtSlot

from os import path
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)

path_to_ui = resource_path('../assets/ui/load.ui')

class LoadBar(QWidget):
    def __init__(self):
        super().__init__()

        uic.loadUi(path_to_ui, self)
        

        self.progress = self.findChild(QProgressBar, 'progressBar')
        self.progress: QProgressBar = self.progress

        self.progress.setValue(0)
