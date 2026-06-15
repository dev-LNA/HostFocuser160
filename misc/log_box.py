from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, 
    QTextEdit,
    QLineEdit,
    QPushButton,
    QFileDialog)


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

log_path = resource_path('assets/ui/LOG.ui')

class LogBox(QWidget):

    closed = pyqtSignal(bool)
    def __init__(self):
        super().__init__()



        uic.loadUi(log_path, self)

        self.txtLog = self.findChild(QTextEdit, 'txtLog')
        self.txtLog: QTextEdit = self.txtLog

        self.txtPath: QLineEdit = self.findChild(QLineEdit, "txtPath")

        self.btnSearch: QPushButton = self.findChild(QPushButton, "btnSearch")

        self.btnSearch.clicked.connect(self._search_log_file)

    def _search_log_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "Open File", 
            "", 
            "Log Files (*.log)"
        )
        if file_name:
            self.txtPath.setText(file_name)
            self._read_log_file(file_name)

    def _read_log_file(self, file_path):
        """Open LOG file and read its content"""
        with open(file_path, "r") as file:                  # Opens log file in read only mode  
            log_content = file.read()                           # Saves log content
            self.txtLog.setPlainText(log_content)       # Puts the log content in the log window text box
            file.close()                                        # Closes the log file


    def closeEvent(self, a0):
        self.closed.emit(True)
        return super().closeEvent(a0)