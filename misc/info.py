from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QLabel
from PyQt6.QtCore import pyqtSignal, QSize, Qt
from PyQt6.QtGui import QPixmap

from misc.login_form import LoginForm
from src.core.config import get_toml

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
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        # No desenvolvimento, a base é a pasta raiz do projeto (onde está o main4.py)
        # Como este arquivo está em misc, pegamos o pai dele
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    return os.path.normpath(os.path.join(base_path, relative_path))

path_to_ui = resource_path('assets/ui/info.ui')              # Path to settings window UI
path_to_logo = resource_path('assets/assets/PadroVert.jpg')   # Path to logo image



class ServerInfoWindow(QMainWindow):

    window_closed = pyqtSignal(bool)

    def __init__(self):
            super().__init__()

            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

            uic.loadUi(path_to_ui, self) # type: ignore

            self.versao = self.findChild(QLabel, 'lblVersao')
            self.versao: QLabel = self.versao

            self.data = self.findChild(QLabel, 'lblData')
            self.data: QLabel = self.data

            self.versao.setText(f"{get_toml('General', 'version')}")
            self.data.setText(f"{get_toml('General', 'date')}")

    def closeEvent(self, event):
        self.window_closed.emit(True)