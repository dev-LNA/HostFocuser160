from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QProgressBar
from PyQt6.QtCore import QThread, pyqtSlot

import os
import sys


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

path_to_ui = resource_path('assets/ui/load.ui')

class LoadBar(QWidget):
    def __init__(self):
        super().__init__()

        uic.loadUi(path_to_ui, self)
        

        self.progress = self.findChild(QProgressBar, 'progressBar')
        self.progress: QProgressBar = self.progress

        self.progress.setValue(0)
