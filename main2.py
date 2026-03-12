from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QTimer, Qt, QPoint, QPropertyAnimation, QSize, QEasingCurve, QDynamicPropertyChangeEvent, QObject, QEvent, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import QMessageBox, QMenu, QSystemTrayIcon, QPushButton,QToolBar, QLabel, QWidget, QProgressBar

import sys
import os
from threading import Thread
from src.core.log import init_logging
import time


from src.utils.constants import constants

try:
    from src.core.config import Config, get_toml
    CONFIG_FILE = True
    ERR_VALUE = None
except Exception as e:
    ERR_VALUE = str(e)
    CONFIG_FILE = False

if CONFIG_FILE:
    from src.core.app import App
    
    from misc.client_sample import ClientSimulator
    from misc.settings import SettingsWindow
    from misc.load_bar import LoadBar
    from misc.ui_intellisense import UiWidgets
    from misc.log_box import LogBox
    

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

main_ui_path = resource_path('assets/ui/main.ui')
load_window_path = resource_path('assets/ui/load.ui')
icon_tray = resource_path('assets/icon.png')
icon_con_ok = resource_path('assets/ui/icons/status.png')
icon_con_nok = resource_path('assets/ui/icons/status-busy.png')
icon_con_wait = resource_path('assets/ui/icons/status-away.png')


class FocuserOPD(QtWidgets.QMainWindow):

    # Signals
    _expanding = pyqtSignal(bool)               # Informs that the expanding animation is in process  
    _expanded = False

    _reachable = False
    _run_thread = None
    _cooldown = time.time()

    def __init__(self):
        super(FocuserOPD, self).__init__()
        uic.loadUi(main_ui_path, self)

        self.clients = list[ClientSimulator]()
        self._num_clients = 0
        self._settings_window = None
        self.log_box = None
        self.load_window = None

        if not CONFIG_FILE:
            close = QMessageBox()
            close.setText(f"Arquivo de configuração com problemas!\n{ERR_VALUE}")
            close.setStandardButtons(QMessageBox.Ok)
            close = close.exec()

            if close == QMessageBox.Ok:   
                sys.exit()

        # self.control = App(logger)

        self.config_file = r"src/config/config.toml"                    # Path to configuration file
        self.log_file = r"logs/focuser.log"                             # Path to log file              # TODO: inicializar o arquivo com o nome padronizado, de acordo com a data (dia inicia ao meio dia)

        # Creates "ui_elements" widget to hold intellisense references to the widgets
        self.ui_elements = UiWidgets(self, "main")
        self.setFixedSize(QSize(310, 488))
        self.ui_elements.pageSelect.setCurrentIndex(0)

        self.ui_elements.btnStartServer.clicked.connect(self._config_server)
        self.menuBar().setVisible(False)
        self.ui_elements.toolBar.setVisible(False)

        self.control = App(logger)

        # Ui elements initialization and configuration
        self.ui_elements.lblSocketIP.setText(f"{self.control.ip_address}")
        self.ui_elements.lblPortPUB.setText(f"{self.control.port_pub}")
        self.ui_elements.lblPortREP.setText(f"{self.control.port_rep}")
        self.ui_elements.actionShow_Log.triggered.connect(self._toggle_log_box)
        self.ui_elements.actionClient_Simulator.triggered.connect(self._run_simulator)
        self.ui_elements.actionHide.triggered.connect(self._minimize_to_tray)
        self.ui_elements.actionSettings.triggered.connect(self._open_settings)

        self.ui_elements.conBarServerRouter.setProperty("conStatusBar", "waiting")
        self.ui_elements.conBarRouterMotor.setProperty("conStatusBar", "waiting")
       
        self.ui_elements.btnStart.clicked.connect(self._start)
        self.ui_elements.btnStop.clicked.connect(self._stop)

        self.ui_elements.btnArrow.clicked.connect(self._show_info)
        self.ui_elements.infoFrame.setVisible(False)

        self.ui_elements.posSlider.setValue(0) 
        
        self.ui_elements.actionShow_toolbar.triggered.connect(              
            lambda checked: self.ui_elements.toolBar.setVisible(checked)    # Action to toggle toolbar
        )   

        self._conIcon = QLabel()
        # self._conIcon.setPixmap(QPixmap(icon_con_ok))
        self._conIcon.setMaximumSize(21,21)
        self.statusBar().addPermanentWidget(self._conIcon)

        # Configuration of signals
        self.control._signals_router.info.connect(self.ui_elements.conBarServerRouter.setProperty)
        self.control._signals_motor.info.connect(self.ui_elements.conBarRouterMotor.setProperty)

        self.control._signals_router.info.connect(self.ui_elements.ledRouter.setProperty)
        self.control._signals_motor.info.connect(self.ui_elements.ledMotor.setProperty)

        self.control._signals_server.status.connect(self.ui_elements.btnStart.setDisabled)
        self.control._signals_server.status.connect(self.ui_elements.btnStop.setEnabled)
        self.control._signals_server.info.connect(self.ui_elements.ledServer.setProperty)

        self.control._statusMessage.connect(self.statusBar().showMessage)
        self.control._statusBar_led.connect(self._conIcon.setPixmap)
        self.control._connection_speed.connect(self.ui_elements.lblComSpeed.setText)

        # self.control._signal_client_id.connect(self.ui_elements.lblClientID_val.setText)
        # self.control._signal_transaction_id.connect(self.ui_elements.lblTransactionId_val.setText)
        
        self.control._signal_position_str.connect(self.ui_elements.lblPosition_val.setText)
        self.control._signal_encoder.connect(self.ui_elements.lblEncoder_val.setText)

        self.control._signal_position_int.connect(self.ui_elements.posSlider.setValue)
        self.control._signal_max_pos.connect(self.ui_elements.posSlider.setMaximum)
        self.control._signal_backlash.connect(self.ui_elements.posSlider.setMinimum)

        
        self.control._signals_moving.info.connect(self.ui_elements.ledMoving.setProperty)
        self.control._signals_lim_min.info.connect(self.ui_elements.ledLimMin.setProperty)
        self.control._signals_lim_max.info.connect(self.ui_elements.ledLimMax.setProperty)
        self.control._signals_initialized.info.connect(self.ui_elements.ledHome.setProperty)
        self.control._signals_parking.info.connect(self.ui_elements.ledPark.setProperty)

        self.control._signals_motor.status.connect(self.ui_elements.gbConnectivity.setEnabled)
        self.control._signals_motor.status.connect(self.ui_elements.gbCommandInfo.setEnabled)
        self.control._signals_motor.status.connect(self.ui_elements.gbFocuserStatus.setEnabled)
        self.control._signals_motor.status.connect(self.ui_elements.posSlider.setEnabled)

        self.control._signal_firmware_status.connect(self.ui_elements.lblStatus_val.setText)

        self.control._signal_last_command.connect(self._parse_last_command)




        # Imports the box to show log files                             # TODO: Adicionar mais funcionalidades ao log box, como pesquisar no log e escolher o log que se deseja abrir
        self.log_box = LogBox()                                         # TODO: Também é necessário alterar a forma que os arquivos são salvos, colocando um nome padrão de acordo com a data    
        self.log_box.closed.connect(self._closed_log_box)               # Signal to inform the main window that the log box was closed by pressing the X button            
        


        


        # TODO: Criar uma parte para a configuração de engenharia, para substituir a edição direta das configurações através de "settings"

        # System tray menu
        self.tray_icon = QSystemTrayIcon(self)                          # Creates system tray icon
        self.tray_icon.setIcon(QIcon(icon_tray))                        # Replace 'icon.png' with your icon file
        self.tray_icon.setToolTip('FocusServer')                        # Status tip of tray icon

        self.tray_menu = QMenu(self)                                    # Creates tray icon menu
        restore_action = QAction('Restore', self)                       # Action to restore window
        restore_action.triggered.connect(self._restore_from_tray)       # Connects action to method to restore window
        self.tray_menu.addAction(restore_action)                        # Adds the action to the menu

        self.tray_icon.setContextMenu(self.tray_menu)                   # Sets the tray icon context menu that opens when tray icon is right clicked
        self.tray_icon.activated.connect(self._tray_activated)          # Method executed when tray icon is activated by an event


        # Events definitions
        #   sets animations and install event filter on objects
        self.ui_elements.conBarServerRouter.setValue(0)
        self.ui_elements.conBarServerRouter.animation = QPropertyAnimation(
            self.ui_elements.conBarServerRouter, b'value', self
        )
        self.ui_elements.conBarServerRouter.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.ui_elements.conBarServerRouter.animation.setDuration(300)
        self.ui_elements.conBarServerRouter.installEventFilter(self)

        self.ui_elements.conBarRouterMotor.setValue(0)
        self.ui_elements.conBarRouterMotor.animation = QPropertyAnimation(
            self.ui_elements.conBarRouterMotor, b'value', self
        )
        self.ui_elements.conBarRouterMotor.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.ui_elements.conBarRouterMotor.animation.setDuration(300)
        self.ui_elements.conBarRouterMotor.installEventFilter(self)

        self.ui_elements.ledServer.installEventFilter(self)
        self.ui_elements.ledRouter.installEventFilter(self)
        self.ui_elements.ledMotor.installEventFilter(self)
        self.ui_elements.ledMoving.installEventFilter(self)
        self.ui_elements.ledLimMax.installEventFilter(self)
        self.ui_elements.ledLimMin.installEventFilter(self)
        self.ui_elements.ledHome.installEventFilter(self)
        self.ui_elements.ledPark.installEventFilter(self)

######### OUTROS TESTES ##########
        self.ui_elements.btnTestes.clicked.connect(self.control._testes)

        # self._starting_size = QSize(self.width(), self.height())    # Holds the initial screen size
        self._starting_size = QSize(310, self.height())    # Holds the initial screen size
        

    
        
        # self.ui_elements.pushButton.clicked.connect(self.teste1)
        self.ui_elements.btnTestes.clicked.connect(self.teste2)


        self.animation = QPropertyAnimation(self, b"size")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(1000)

        self.animation.finished.connect(self._expanded_ended)


        # self._expanding.connect(self.ui_elements.pushButton_2.setDisabled)
        self._expanding.connect(self.ui_elements.btnArrow.setDisabled)

    def teste1(self):

        if(self.ui_elements.ledServer.property("statusLed") == "OK"):
            self.ui_elements.ledServer.setProperty("statusLed", "NOK")
        else:
            self.ui_elements.ledServer.setProperty("statusLed", "OK")

        self._update_gui_element(self.ui_elements.ledServer)


        if(self.ui_elements.conBarServerRouter.value() == 0):
            # self.ui_elements.conBarServerRouter.setValue(50)
            # self.conBarServerRouterAnimation.setEndValue(50)
            # self.conBarServerRouterAnimation.start()
            self.ui_elements.conBarServerRouter.setProperty("conStatusBar", "connecting")
        elif(self.ui_elements.conBarServerRouter.value() == 50):
            # self.ui_elements.conBarServerRouter.setValue(100)
            # self.conBarServerRouterAnimation.setEndValue(100)
            # self.conBarServerRouterAnimation.start()
            self.ui_elements.conBarServerRouter.setProperty("conStatusBar", "connected")
        elif(self.ui_elements.conBarServerRouter.value() == 100):
            # self.ui_elements.conBarServerRouter.setValue(0)
            # self.conBarServerRouterAnimation.setEndValue(0)
            # self.conBarServerRouterAnimation.start()
            self.ui_elements.conBarServerRouter.setProperty("conStatusBar", "waiting")
        
        self._update_gui_element(self.ui_elements.conBarServerRouter)


    def teste2(self):

        if self._expanded is True:
            self.animation.setEndValue(self._starting_size)
            self._expanded = False
        else:
            self.animation.setEndValue(QSize(self.width() + 320, self.height()))
            self._expanded = True

        self._expanding.emit(True)
        self.animation.start()

######### FIM OUTROS TESTES ##########

    def _config_server(self):
        """Sets configurations according to the selected focuser"""
        if self.ui_elements.rb160.isChecked():
            print("INICIAR FOCALIZADOR DO 160")
            Config.focuser = "160"
            Config.device_ip = get_toml('Device', 'ip_160')                  #TODO: Alterar em config.toml o device_ip por 'f160_ip' e 'fiag_IP'
            self.ui_elements.lblTitle.setText("Focuser 160")
            self.control.init_device(constants.ARCUS_DMX_ETH)
            self._init_focuser()
        elif self.ui_elements.rbIAG.isChecked():
            print("INICIAR FOCALIZADOR DO IAG")
            Config.focuser = "IAG"
            Config.device_ip = get_toml('Device', 'ip_iag') #120  #"200.131.64.172" #TEST_VALUE: Usando o valor do ip do DMX para poder fazer testes     #TODO: Alterar em config.toml o device_ip por 'f160_ip' e 'fiag_IP'
            self.ui_elements.lblTitle.setText("Focuser IAG")
            self.control.init_device(constants.AMP_MOTOR)
            self._init_focuser()
        else:
            QMessageBox.information(
                None,  # Parent widget (None centers on the screen; 'self' for a parent window)
                "Attention",  
                "A focuser must be selected."  
    )

    def _init_focuser(self):
        """Initializes the focuser
        Sets the visibility for the menuBar an toolBar, changes the 
        page to show the focuser main window and starts the server if
        auto startup is configured """
        self.menuBar().setVisible(True)
        self.ui_elements.toolBar.setVisible(True)
        self.ui_elements.pageSelect.setCurrentIndex(1)  
        if Config.startup:
            self._start()          
            

    def _show_info(self):
        if self._expanded is True:
            self.setMinimumWidth(310)
            self.animation.setEndValue(self._starting_size)
            self._expanded = False
        else:
            self.setMaximumWidth(630)
            self.ui_elements.infoFrame.setVisible(True)
            self.animation.setEndValue(QSize(630, self.height()))
            self._expanded = True

        self._expanding.emit(True)
        self.animation.start()

    def _closed_log_box(self):
        """Guarantees that the action is unchecked if the Log Box is closed by pressing the X button"""
        self.ui_elements.actionShow_Log.setChecked(False)

    def _toggle_log_box(self, checked):
        """Toggles the log box

        Parameters
        ----------
        checked : bool
            State of the action "actionShow_Log"
        """
        if checked is True:
            try:
                if self.log_file is not None:
                    self._read_log_file(self.log_file)
                    self.log_box.show()
            except Exception as e:
                print(f"{str(e)}")
        else:
            self.log_box.hide()


    def _read_log_file(self, file_path):
        """Open LOG file"""
        with open(file_path, "r") as file:
            log_content = file.read()
            self.log_box.txtLog.setPlainText(log_content)   

    def _minimize_to_tray(self):
        """Minimize to tray"""
        self.hide()                                                     # Hides server window   
        self.tray_icon.show()                                           # Show tray icon menu

    def _restore_from_tray(self):
        """Restore window from Tray"""
        self.show()                                                     # Show server window
        self.tray_icon.hide()                                           # Hides tray icon menu
    
    def _tray_activated(self, reason):
        """Method called when an icon tray event occurs

        Parameters
        ----------
        reason : ActivationReason
            Reason that the tray icon was activated
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:      # If a double click was detected
            self._restore_from_tray()                                   # Restores the window

    def _run_simulator(self, checked):
        """Opens the simulator window"""

        client = ClientSimulator()
        client.client_ID = self._num_clients + 100              # Clients ID number beging in 100
        client.name = f"Simulador {str(self._num_clients)}"
        client.transaction_ID = 0

        client.sig.connect(self._simulator_closed)
        client.move(self.pos() + QPoint(self.width(), 0))

        self.clients.append(client)
        
        self.clients[len(self.clients)-1].show()
        self._num_clients+=1

        print(self.clients)

        # if checked is True:
        # if self.second_window is None:
        #     self.second_window = ClientSimulator()
        #     self.second_window.sig.connect(self._simulator_closed)          # Signal to inform the main window that the simulator was closed    
        #     self.second_window.move(self.pos() + QPoint(self.width(), 0))   # Positions the simulator window next to the main window
        #     self.second_window.show()                                       # Opens the simulator window
        # else:
        #     self.second_window.close()                                          # Closes the simulator if already opened

    def _simulator_closed(self, msg):
        """ Receives closed window signal from the simulator """

        for index, client in enumerate(self.clients):
            if msg == client.client_ID:
                removed = self.clients.pop(index)
                print(f"Cliente {removed.client_ID} encerrado")

        # self._num_clients-=1

        print(self.clients)
                
        # if msg is True:    
        #     self.second_window = None                                       # "Deletes" the simulator window from the main window
        #     self.ui_elements.actionClient_Simulator.setChecked(False)       # Unchecks action to open client simulator
        #     print("simulador fechado")


    def _open_settings(self):
        """Opens settings window"""
    # To open the settings the motor must be connected
        if self.control.device.connected:
            if self._settings_window is None:
                self._settings_window = SettingsWindow(self.control.device)
                self._settings_window._signal_window_closed.connect(self._settings_closed)
                self._settings_window._signals_changed_settings.connect(self._parse_changed_settings)
                self._settings_window.move(self.pos() + QPoint(self.width(), 0))
                self._settings_window.show()
        else:                                                                                   # If the motor is not connected asks the user if they would like to connect #TODO: Talvez dê só para conectar sem perguntar para o usuário
            msg = QMessageBox.information(
                self,  # Parent widget (None centers on the screen; 'self' for a parent window)
                "Attention",  
                "To open settings the focuser motor must be connected. \nConnect to motor?",
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if(msg == QMessageBox.StandardButton.Yes):                                                          # If the user whishes to connect the motor
                self._start()                                                                                   # Connects the server to the motor and starts server operation #TODO: Talvez seja bom ter essas coisas separadas, com um método só para conectar (criar o socket) e outro para iniciar a thread de App, pois a thread de App vai começar a fazer o polling de informações sem parar uma vez iniciada
                t = time.time()                                                                                 # Keeps current time
                while not self.control.device.connected:                                                        # Waits 5 seconds while the server tries to connect to the motor
                    if round(time.time()-t, 3) > 5:                                                             # If the server cannot connect in 5 seconds the code continues executing
                        break                                                                                       # Break the while loop
                if self.control.device.connected:                                                               # If the connection to the motor was successful
                    if self._settings_window is None:                                                               # If the settings windows was not yet defined
                        self._settings_window = SettingsWindow(self.control.device)                                 # Instantiate settings window
                        self._settings_window._signal_window_closed.connect(self._settings_closed)                  # Connects closed window signal
                        self._settings_window._signals_changed_settings.connect(self._parse_changed_settings)       # Connects signal to show the settings in the GUI
                        self._settings_window.move(self.pos() + QPoint(self.width(), 0))                            # Positions the settings window according to the main window position
                        self._settings_window.show()                                                                # Shows the settings window
                else:
                    raise Exception("Could not connect")                                                        # Exception if the connection was not successful


    def _parse_changed_settings(self, data: dict):
        if "MAX_POS" in data:
            self.ui_elements.posSlider.setMaximum(int(data["MAX_POS"]) + 5)
            self.ui_elements.posSlider.setMinimum(-12)

    def _settings_closed(self, msg):
        if msg is True:
            self._settings_window = None
            print("Configurações fechadas")

    def _parse_last_command(self, data: dict):
        self.ui_elements.lblTime.setText(data["timestamp"])
        self.ui_elements.lblClientName_val.setText(data["cmd"]["clientName"])
        self.ui_elements.lblClientID_val.setText(str(data["cmd"]["clientId"]))
        self.ui_elements.lblTransactionId_val.setText(str(data["cmd"]["clientTransactionId"]))
        self.ui_elements.lblCommand_val.setText(data["cmd"]["action"])
        if(data["cmd"]["action"] == "HOME" or data["cmd"]["action"] == "PARK"):
            self.ui_elements.lblLastHoming_val.setText(data["timestamp"])

    def _expanded_ended(self):
        if self._expanded == False:
            self.setMaximumWidth(self.width())
            self.ui_elements.infoFrame.setVisible(False)
        else:
            self.setMinimumWidth(self.width())
        self._expanding.emit(False)      

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

        # Events related to a 'Dynamic Property' being changed
        if event.type() == QEvent.Type.DynamicPropertyChange:

            if obj.__class__ is QtWidgets.QProgressBar:
                    # Animations related to progress bars
                    if obj.property("conStatusBar") == "waiting":
                        obj.animation.setEndValue(0)
                        obj.animation.start()
                    elif obj.property("conStatusBar") == "connecting":
                        obj.animation.setEndValue(50)
                        obj.animation.start()
                    elif obj.property("conStatusBar") == "connected":
                        obj.animation.setEndValue(100)
                        obj.animation.start()
                    self._update_gui_element(obj)
                    return True   
                    
            if obj.__class__ is QtWidgets.QLabel:
                    # Animations related to labels
                    self._update_gui_element(obj)
                    return True 
                
        # For all other events or objects, return False to allow normal handling
        return super().eventFilter(obj, event)


    def _start(self):
        """Start server"""
        if self._run_thread and self._run_thread.is_alive():
            print("Still Alive")
            return

        # if Config.focuser == "160":                                 # When the server is started it is important to guarantee that the IP value is updated according to the config file, the value could have been changed in the settings
        #     Config.device_ip = get_toml('Device', 'ip_160')
        # elif Config.focuser == "IAG":
        #     Config.device_ip = get_toml('Device', 'ip_iag')
        # else:
        #     RuntimeError("Invalid focuser value")

        self._run_thread = Thread(target = self.control.run)
        self._run_thread.start()
        # self._run_thread.daemon = True
    
    def _stop(self):
        """Stops main program and the main loop at Application interface with Device"""
    # Also closes second window if it is opened
        # if self.second_window is not None:
        #     self.second_window.close()


        while self.clients:             # Closes all opened client simulators
            self.clients[0].close()     # The close method will 'pop' the client from the list, so the client in position 0 is removed until there are no more clients opened


        if self._run_thread and self._run_thread.is_alive():    # If the server thread is running 
            self.control.stop_server_loop()                         # Stops the thread loop
            self._run_thread.join()                                 # Joins the thread to wait until it is finished
            self.control.stop_poller()                              # Unregisters server ZMQ poll


        if self.control:
            self.control.disconnect()                           # Closes the socket to communicate to the motor

        # if self.control:
        #     self.control.disconnect()
        # if self._run_thread and self._run_thread.is_alive():    # If the server thread is running 
        #     self.control._stop()                                    # Stops the thread loop and unregister zmq.poll #TODO: Separar isso em mais de uma função, o zmq.poll acho que tem que ser fechado depois que a thread finaliza
        #     self._run_thread.join()                                 # Joins the thread to wait until it is finished

        



    def closeEvent(self, event):
        """Close event

        Parameters
        ----------
        event : _type_
            _description_
        """
        close = QMessageBox()
        close.setWindowTitle("Close")
        close.setText("Deseja sair?")
        close.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        close = close.exec()

        if close == QMessageBox.StandardButton.Yes:   
            self._stop()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":

    logger = init_logging() 
    app = QtWidgets.QApplication([])       

    main_window1 = FocuserOPD()
    main_window1.show()
    

    sys.exit(app.exec()) 