from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QLineEdit, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal

from misc.load_bar import LoadBar
from src.interface.dmx_eth import FocuserDriver
from misc.ui_intellisense import UiWidgets
from src.core.config import Config  

import sys
from os import path

import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)

path_to_ui = resource_path('../assets/ui/settings.ui')

class SettingsWindow(QMainWindow):

    _signal_window_closed = pyqtSignal(bool)
    _signal_engineering_mode = pyqtSignal(bool)

    _signal_progress = pyqtSignal(int)

    _engineering_mode = False


    def __init__(self, driver: FocuserDriver):
        super().__init__()

        self.driver = driver
        
        uic.loadUi(path_to_ui, self)

        self.ui_elements = UiWidgets(self, "settings")

        # The QLineEdits must be initialized as 'disabled'. This is changed in engineering mode.
        lineEdits = self.findChildren(QLineEdit)                                # Makes a list of all QLineEdit widgets
        for _ in lineEdits:                                                     # connects the engineering mode signal to each QLineEdit setEnabled
            self._signal_engineering_mode.connect(_.setEnabled)
        self._signal_engineering_mode.disconnect(self.ui_elements.txtPark.setEnabled)
        self.ui_elements.txtPark.setEnabled(False)

        self._signal_engineering_mode.connect(self.ui_elements.btnSave.setEnabled)  # Save is only allowed in engineering mode

        self.engineering_mode = False                                               # Initializes engineering mode to false

        self.ui_elements.btnEngineering.clicked.connect(self._log_engineering_mode)
        self.ui_elements.btnSave.clicked.connect(self._save_settings)


        # self._progress_bar = QProgressBar()
        # self._progress_bar.setVisible(False)
        # self._progress_bar.setTextVisible(False)
        # self._progress_bar.setMaximumWidth(100)
        self._progress_bar = LoadBar()

        self.statusBar().addPermanentWidget(self._progress_bar)

        self.updater = RetrieveSettings(self.driver)

        self.updater._running.connect(self._progress_bar.setVisible)
        self.updater._signal_progress.connect(self._progress_bar.progress.setValue)
        self.updater._signal_device_IP.connect(self.ui_elements.txtMotorIP.setText)
        self.updater._signal_backlash.connect(self.ui_elements.txtBackComp.setText)
        self.updater._signal_max_pos.connect(self.ui_elements.txtMaxPos.setText)
        self.updater._signal_park_pos.connect(self.ui_elements.txtPark.setText)
        self.updater._signal_max_speed.connect(self.ui_elements.txtMaxSpeed.setText)
        self.updater._signal_normal_speed.connect(self.ui_elements.txtNormalSpeed.setText)
        self.updater._signal_low_speed.connect(self.ui_elements.txtLowSpeed.setText)

        self._update_settings()




    def _update_settings(self):
        """Updates current settings"""
        self.updater.start()
        

    def _log_engineering_mode(self):
        if self.engineering_mode:
            self.engineering_mode = False
        else:
            self.engineering_mode = True

    def _save_settings(self):

        current_pos = self.driver.position                                  # Reads the current position
        self.driver.set_max_pos = self.ui_elements.txtMaxPos.text()         # Saves new max pos value
        if int(self.ui_elements.txtMaxPos.text()) < current_pos:                
             print("Necessário realizar homing")                            # TODO: Se o novo valor máximo for menor que a posição atual vai ser necessário realizar o homing para garantir que a posição atual vai ser válida dentro do novo limite
           

    @property
    def engineering_mode(self) -> bool:
        return self._engineering_mode
    
    @engineering_mode.setter
    def engineering_mode(self, value: bool):
        self._engineering_mode = value
        self._signal_engineering_mode.emit(self._engineering_mode)

        

    def closeEvent(self, a0):
        self._signal_window_closed.emit(True)
        return super().closeEvent(a0)
    






class RetrieveSettings(QThread):

    _running = pyqtSignal(bool)

    _signal_device_IP = pyqtSignal(str)
    _signal_backlash = pyqtSignal(str)
    _signal_max_pos = pyqtSignal(str)
    _signal_park_pos = pyqtSignal(str)
    _signal_max_speed = pyqtSignal(str)
    _signal_normal_speed = pyqtSignal(str)
    _signal_low_speed = pyqtSignal(str)

    _signal_progress = pyqtSignal(int)


    def __init__(self, driver: FocuserDriver):
        super().__init__()

        self.driver = driver


    def run(self):
        p = 0
        self._signal_progress.emit(p)
        self._running.emit(True)

        self._signal_device_IP.emit(self.driver.get_device_IP)
        p += 12
        self._signal_progress.emit(p)
        self._signal_backlash.emit(self.driver.get_backlash)
        p += 12
        self._signal_progress.emit(p)
        self._signal_max_pos.emit(self.driver.get_max_pos)
        p += 12
        self._signal_progress.emit(p)
        self._signal_park_pos.emit(self.driver.get_park_pos)
        p += 12
        self._signal_progress.emit(p)
        self._signal_max_speed.emit(self.driver.get_max_speed)
        p += 12
        self._signal_progress.emit(p)
        self._signal_normal_speed.emit(self.driver.get_normal_speed)
        p += 12
        self._signal_progress.emit(p)
        self._signal_low_speed.emit(self.driver.get_low_speed)
        p = 100
        self._signal_progress.emit(p)
        time.sleep(0.2)

        self._running.emit(False)

