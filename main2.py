from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QTimer, Qt, QPoint, QPropertyAnimation, QSize, QEasingCurve, QDynamicPropertyChangeEvent, QObject, QEvent, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import QMessageBox, QMenu, QSystemTrayIcon, QPushButton,QToolBar, QLabel

import sys
import os
from threading import Thread
from src.core.log import init_logging
import time

try:
    from src.core.config import Config    
    CONFIG_FILE = True
    ERR_VALUE = None
except Exception as e:
    ERR_VALUE = str(e)
    CONFIG_FILE = False

if CONFIG_FILE:
    from src.core.app import App
    
    from misc.client_sample import ClientSimulator
    from misc.ui_intellisense import UiWidgets

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

main_ui_path = resource_path('assets/ui/main.ui')
icon_tray = resource_path('assets/icon.png')


class FocuserOPD(QtWidgets.QMainWindow):

    # Signals
    _expanded = False                           # keeps the information if the gui is expanded
    _expanding = pyqtSignal(bool)               # Informs that the expanding animation is in process  

    def __init__(self):
        super(FocuserOPD, self).__init__()
        uic.loadUi(main_ui_path, self)
        self.second_window = None

        if not CONFIG_FILE:
            close = QMessageBox()
            close.setText(f"Arquivo de configuração com problemas!\n{ERR_VALUE}")
            close.setStandardButtons(QMessageBox.Ok)
            close = close.exec()

            if close == QMessageBox.Ok:   
                sys.exit()

        self.control = App(logger)

        self.config_file = r"src/config/config.toml"
        self.log_file = r"logs/focuser.log"

        # Creates "ui_elements" widget to hold intellisense references to the widgets
        self.ui_elements = UiWidgets(self)

        # Ui elements initialization and configuration
        self.ui_elements.txtSocketIP.setText(f"{self.control.ip_address}")
        self.ui_elements.txtPortPUB.setText(f"{self.control.port_pub}")
        self.ui_elements.txtPortREP.setText(f"{self.control.port_rep}")

























        self._starting_size = QSize(self.width(), self.height())    # Holds the initial screen size
        
        self.ui_elements.actionShow_toolbar.triggered.connect(              
            lambda checked: self.ui_elements.toolBar.setVisible(checked)    # Action to toggle toolbar
            )   
        
        self.ui_elements.ledServer.setProperty("statusLed", "NOK")

        self.ui_elements.conBarServerRouter.setValue(0)
        self.conBarAnimation = QPropertyAnimation(
            self.ui_elements.conBarServerRouter, b'value', self
        )
        self.conBarAnimation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.conBarAnimation.setDuration(300)

        self.ui_elements.conBarServerRouter.installEventFilter(self)
        
        # self.ui_elements.pushButton.clicked.connect(self.teste1)
        # self.ui_elements.pushButton_2.clicked.connect(self.teste2)


        self.animation = QPropertyAnimation(self, b"size")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(1000)

        self.animation.finished.connect(self._expanded_ended)

        # self._expanding.connect(self.ui_elements.pushButton_2.setDisabled)
        # self._expanding.connect(self.ui_elements.pushButton.setDisabled)


    def _expanded_ended(self):
        self._expanding.emit(False)      


        
    def teste1(self):

        if(self.ui_elements.ledServer.property("statusLed") == "OK"):
            self.ui_elements.ledServer.setProperty("statusLed", "NOK")
        else:
            self.ui_elements.ledServer.setProperty("statusLed", "OK")

        self._update_gui_element(self.ui_elements.ledServer)


        if(self.ui_elements.conBarServerRouter.value() == 0):
            # self.ui_elements.conBarServerRouter.setValue(50)
            # self.conBarAnimation.setEndValue(50)
            # self.conBarAnimation.start()
            self.ui_elements.conBarServerRouter.setProperty("conStatusBar", "connecting")
        elif(self.ui_elements.conBarServerRouter.value() == 50):
            # self.ui_elements.conBarServerRouter.setValue(100)
            # self.conBarAnimation.setEndValue(100)
            # self.conBarAnimation.start()
            self.ui_elements.conBarServerRouter.setProperty("conStatusBar", "connected")
        elif(self.ui_elements.conBarServerRouter.value() == 100):
            # self.ui_elements.conBarServerRouter.setValue(0)
            # self.conBarAnimation.setEndValue(0)
            # self.conBarAnimation.start()
            self.ui_elements.conBarServerRouter.setProperty("conStatusBar", "waiting")
        
        self._update_gui_element(self.ui_elements.conBarServerRouter)


    def teste2(self):

        if self._expanded is True:
            self.animation.setEndValue(self._starting_size)
            self._expanded = False
        else:
            self.animation.setEndValue(QSize(self.width() + 300, self.height()))
            self._expanded = True

        self._expanding.emit(True)
        self.animation.start()



    def _update_gui_element(self, widget: QtWidgets):
        """Updates the GUI element style after an event occured

        Parameters
        ----------
        widget : QtWidgets
            Widget to be updated
        """
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Process events

        Parameters
        ----------
        obj : QObject
            Object that triggered the event
        event : QEvent
            Event that occurred

        Returns
        -------
        bool
            Returns if everything went ok
        """
        if obj is self.ui_elements.conBarServerRouter:
            if event.type() == QEvent.Type.DynamicPropertyChange:   
                if self.ui_elements.conBarServerRouter.property("conStatusBar") == "waiting":
                    self.conBarAnimation.setEndValue(0)
                    self.conBarAnimation.start()
                elif self.ui_elements.conBarServerRouter.property("conStatusBar") == "connecting":
                    self.conBarAnimation.setEndValue(50)
                    self.conBarAnimation.start()
                elif self.ui_elements.conBarServerRouter.property("conStatusBar") == "connected":
                    self.conBarAnimation.setEndValue(100)
                    self.conBarAnimation.start()
                return True
        

        # For all other events or objects, return False to allow normal handling
        return super().eventFilter(obj, event)


if __name__ == "__main__":

    logger = init_logging() 
    app = QtWidgets.QApplication([])       

    main_window1 = FocuserOPD()
    main_window1.show()
    

    sys.exit(app.exec()) 