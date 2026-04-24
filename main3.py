from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QTimer, Qt, QPoint, QPropertyAnimation, QSize, QEasingCurve, QDynamicPropertyChangeEvent, QObject, QEvent, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QMenu, QSystemTrayIcon, QPushButton,QToolBar, QLabel, QWidget, QProgressBar

import sys
import os
from threading import Thread
from src.core.log import init_logging
import time

try:
    from src.core.config import Config, get_toml
    CONFIG_FILE = True
    ERR_VALUE = None
except Exception as e:
    ERR_VALUE = str(e)
    CONFIG_FILE = False

from core.server import Server
from misc.client_sample import ClientSimulator
from misc.ui_intellisense import UiWidgets
from src.utils.constants import constants
from src.utils.motor import MotorModels
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

class FocuserOPD (QMainWindow):

    # Signals
    _expanding = pyqtSignal(bool)               # Informs that the expanding animation is in process  
    _expanded = False                           # Informs expansion ended

    _run_thread = None
    _cooldown = time.time()

    def __init__(self):
        super(FocuserOPD, self).__init__()
        uic.loadUi(main_ui_path, self)          # Loads UI file

        self.clients = list[ClientSimulator]()  # Initializes client simulators list
        self._num_clients = 0                   # Number of opened clients
        self._settings_window = None            # Initialize settings window as None
        self.log_box:LogBox = LogBox()          # Initialize log window
        self.load_window = None                 # Initialize load window as None    

        if not CONFIG_FILE:                     # If configuration file was not found a message is displayed and the program will close after check
            close = QMessageBox()                                                       # Creates message window
            close.setText(f"Arquivo de configuração com problemas!\n{ERR_VALUE}")       # Config window message
            logger.error(f'Configuration file not defined. {ERR_VALUE}')                
            close.setStandardButtons(QMessageBox.StandardButton.Ok)                     # Config window button
            close = close.exec()                                                        # Opens window and waits button press

            if close == QMessageBox.StandardButton.Ok:                                  # After press ok button
                sys.exit()                                                                  # Ends program

        self.config_file = r"src/config/config.toml"                    # Path to configuration file
        self.log_file = r"logs/focuser.log"                             # Path to log file              # TODO: inicializar o arquivo com o nome padronizado, de acordo com a data (dia inicia ao meio dia)

        
        self.ui_elements = UiWidgets(self, "main")                      # Creates "ui_elements" widget to hold intellisense references to the widgets
        self.setFixedSize(QSize(310, 488))                              # Sets a fixed size for the main window
        self.ui_elements.pageSelect.setCurrentIndex(0)                  # Initializes the main window in the focalizer seletion page

        self.ui_elements.btnStartServer.clicked.connect(self._config_server)
        self.menuBar().setVisible(False)                                        # The menu bar is not displayed in the focalizer selection page
        self.ui_elements.toolBar.setVisible(False)                              # The tool bar is not displayed in the focalizer selection page

        self.control = Server(logger)                                              # Instantiates the server app class

    #--- UI elements initialization and configuration
    #   Initializes every UI element of the main window.
    #   The initialization will set the initial values and the behavior of the elements.        
        self.ui_elements.btnStart.clicked.connect(self._start)
        self.ui_elements.btnStop.clicked.connect(self._stop)
        self.ui_elements.btnArrow.clicked.connect(self._show_info)

        self.ui_elements.actionShow_Log.triggered.connect(self._toggle_log_box)
        self.ui_elements.actionClient_Simulator.triggered.connect(self._run_simulator)
        self.ui_elements.actionHide.triggered.connect(self._minimize_to_tray)
        # self.ui_elements.actionSettings.triggered.connect(self._open_settings)

        self.ui_elements.actionShow_toolbar.triggered.connect(              
            lambda checked: self.ui_elements.toolBar.setVisible(checked)    # Action to toggle toolbar
        )   


        self.ui_elements.lblSocketIP.setText(f"{self.control.ip_address}")
        self.ui_elements.lblPortPUB.setText(f"{self.control.port_pub}")
        self.ui_elements.lblPortREP.setText(f"{self.control.port_rep}")
        self.ui_elements.infoFrame.setVisible(False)
        self.ui_elements.posSlider.setValue(0) 


        self.ui_elements.conBarServerRouter.setProperty("conStatusBar", "waiting")
        self.ui_elements.conBarRouterMotor.setProperty("conStatusBar", "waiting")

        # Configuration of signals
        self.control.signals.router_status.info.connect(self.ui_elements.conBarServerRouter.setProperty)
        self.control.signals.motor_status.info.connect(self.ui_elements.conBarRouterMotor.setProperty)

        self.control.signals.router_status.info.connect(self.ui_elements.ledRouter.setProperty)
        self.control.signals.motor_status.info.connect(self.ui_elements.ledMotor.setProperty)

        self.control.signals.server_status.status.connect(self.ui_elements.btnStart.setDisabled)
        self.control.signals.server_status.status.connect(self.ui_elements.btnStop.setEnabled)
        self.control.signals.server_status.info.connect(self.ui_elements.ledServer.setProperty)

        self.control.signals.status_message.connect(self.statusBar().showMessage)
        # self.control.signal_statusBar_led.connect(self._conIcon.setPixmap)
        self.control.signals.connection_speed.connect(self.ui_elements.lblComSpeed.setText)
        
        # self.control.signals.signal_position_str.connect(self.ui_elements.lblPosition_val.setText)
        # self.control.signal_encoder.connect(self.ui_elements.lblEncoder_val.setText)

        # self.control.signal_position_int.connect(self.ui_elements.posSlider.setValue)
        # self.control.signal_max_pos.connect(self.ui_elements.posSlider.setMaximum)
        # self.control.signal_backlash.connect(self.ui_elements.posSlider.setMinimum)

        
        # self.control.signals_moving.info.connect(self.ui_elements.ledMoving.setProperty)
        # self.control.signals_lim_min.info.connect(self.ui_elements.ledLimMin.setProperty)
        # self.control.signals_lim_max.info.connect(self.ui_elements.ledLimMax.setProperty)
        # self.control.signals_initialized.info.connect(self.ui_elements.ledHome.setProperty)
        # self.control.signals_parking.info.connect(self.ui_elements.ledPark.setProperty)

        # self.control.signals_motor.status.connect(self.ui_elements.gbConnectivity.setEnabled)
        # self.control.signals_motor.status.connect(self.ui_elements.gbCommandInfo.setEnabled)
        # self.control.signals_motor.status.connect(self.ui_elements.gbFocuserStatus.setEnabled)
        # self.control.signals_motor.status.connect(self.ui_elements.posSlider.setEnabled)

        # self.control.signal_firmware_status.connect(self.ui_elements.lblStatus_val.setText)

        # self.control.signal_last_command.connect(self._parse_last_command)




        # Imports the box to show log files                             # TODO: Adicionar mais funcionalidades ao log box, como pesquisar no log e escolher o log que se deseja abrir de acordo com a data
        self.log_box.closed.connect(self._closed_log_box)               # Signal to inform the main window that the log box was closed by pressing the X button            
  

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


    #--- Events definitions
        #   sets animations and install event filter on objects
        # self.ui_elements.conBarServerRouter.setValue(0)
        # self.ui_elements.conBarServerRouter.animation = QPropertyAnimation(                         # Animation for the connection bar between server and router
        #     self.ui_elements.conBarServerRouter, b'value', self                                     # The animation is triggered when the property value is changed
        # )
        # self.ui_elements.conBarServerRouter.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        # self.ui_elements.conBarServerRouter.animation.setDuration(300)
        # self.ui_elements.conBarServerRouter.installEventFilter(self)

        # self.ui_elements.conBarRouterMotor.setValue(0)
        # self.ui_elements.conBarRouterMotor.animation = QPropertyAnimation(                          # Animation for the connection bar between router and motor
        #     self.ui_elements.conBarRouterMotor, b'value', self                                      # The animation is triggered when the property value is changed
        # )
        # self.ui_elements.conBarRouterMotor.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        # self.ui_elements.conBarRouterMotor.animation.setDuration(300)
        # self.ui_elements.conBarRouterMotor.installEventFilter(self)

        self.window_expand_animation = QPropertyAnimation(self, b"size")                                          # Animation for the window expansion
        self.window_expand_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.window_expand_animation.setDuration(1000)
        self._starting_size = QSize(310, self.height())                                             # Holds the initial screen size
 
        self.window_expand_animation.finished.connect(self._expanded_ended)                                       # Connects a function to run after the animation is over
        self._expanding.connect(self.ui_elements.btnArrow.setDisabled)                              # Disables the arrow expansion button while the animation is being executed

        # Install event filters in the LEDs so that when a property is changed the values are automatically updated
        # self.ui_elements.ledServer.installEventFilter(self)                                         
        # self.ui_elements.ledRouter.installEventFilter(self)
        # self.ui_elements.ledMotor.installEventFilter(self)
        # self.ui_elements.ledMoving.installEventFilter(self)
        # self.ui_elements.ledLimMax.installEventFilter(self)
        # self.ui_elements.ledLimMin.installEventFilter(self)
        # self.ui_elements.ledHome.installEventFilter(self)
        # self.ui_elements.ledPark.installEventFilter(self)

######### OUTROS TESTES ##########
        self.ui_elements.btnTestes.clicked.connect(self.control._testes)



    def _config_server(self):
        """Sets configurations according to the selected focuser.
        The focuser is selected in the focuser selection page when the server is initialized and cannot be changed after the initial selection."""
        if self.ui_elements.rb160.isChecked():                              # Checks radio button value
            print("INICIAR FOCALIZADOR DO 160")                                 # If the PE 160 was chosen
            Config.focuser = "160"                                              # Changes Config according to selection
            Config.device_ip = get_toml('Device', 'ip_160')                     # Sets the IP address according to selection
            self.ui_elements.lblTitle.setText("Focuser 160")                    # Sets main window label according to selection
            self.control.init_device(MotorModels.ARCUS_DMX_ETH)                   # Initializes the motor driver according to the focuser
            self._init_focuser()                                                # Changes to the server page                                  
        elif self.ui_elements.rbIAG.isChecked():                            # Checks radio button value
            print("INICIAR FOCALIZADOR DO IAG")                                 # If the IAG was chosen
            Config.focuser = "IAG"                                              # Changes Config according to selection
            Config.device_ip = get_toml('Device', 'ip_iag')                     # Sets the IP address according to selection
            self.ui_elements.lblTitle.setText("Focuser IAG")                    # Sets main window label according to selection
            self.control.init_device(MotorModels.AMP_MOTOR)                       # Initializes the motor driver according to the focuser
            self._init_focuser()                                                # Changes to the server page      
        else:                                                               # If the 'start server' button is pressed with no focuser selected shows a message
            QMessageBox.information(                                            
                None,                                                           # Parent widget (None centers on the screen; 'self' for a parent window)
                "Attention",  
                "A focuser must be selected."                                   # Informs the user that a focuser must be selected
            )

    def _init_focuser(self):
        """Initializes the focuser
        Sets the visibility for the menuBar an toolBar, changes the 
        page to show the focuser main window and starts the server if
        auto startup is configured """
        self.menuBar().setVisible(True)                                     # Sets menu bar visibility
        self.ui_elements.toolBar.setVisible(True)                           # Sets tool bar visibility
        self.control.server_online = False                               # Emits signal with initial server status as disconnected
        self.ui_elements.pageSelect.setCurrentIndex(1)                      # Changes view to the main server page
        if Config.startup:                                                  # If configured to 'auto start'
            self._start()                                                       # Starts the server

    def _start(self):
        """Start server"""
        if self._run_thread and self._run_thread.is_alive():                # Checks if the thread is already being executed
            print("Still Alive")
            return                                                              # If already running do nothing

        self._run_thread = Thread(target = self.control.run)                # If thread no running creates thread to execute the funtion 'run' on 'App'
        self._run_thread.start()                                            # Starts the thread
           
    def _stop(self):
        """Stops main program and the main loop at Application interface with Device"""
        while self.clients:             # Closes all opened client simulators
            self.clients[0].close()         # The close method will 'pop' the client from the list, so the client in position 0 is removed until there are no more clients opened


        if self._run_thread and self._run_thread.is_alive():    # If the server thread is running 
            self.control.stop_server_loop()                         # Stops the thread loop
            self._run_thread.join()                                 # Joins the thread to wait until it is finished
            self.control.stop_poller()                              # Unregisters server ZMQ poll

        if self.control:
            self.control.disconnect()                           # Closes the socket to communicate to the motor and ends PUB and SUB

    def _show_info(self):
        """Expands or shrinks the main window"""
        if self._expanded is True:                                          # If the window is already expanded   
            self.setMinimumWidth(310)                                           # Sets new minimal width
            self.window_expand_animation.setEndValue(self._starting_size)                     # Sets window size after animation
            self._expanded = False                                              # Resets '_expanded' value
        else:                                                               # Else if the window is not expanded 
            self.setMaximumWidth(630)                                           # Sets new max width  
            self.ui_elements.infoFrame.setVisible(True)                         # Sets 'infoFrame' visibility        
            self.window_expand_animation.setEndValue(QSize(630, self.height()))               # Sets window size after animation
            self._expanded = True                                               # Sets '_expanded' value

        self._expanding.emit(True)                                          # Emits signal informing that the window is expanding
        self.window_expand_animation.start()                                              # Starts expantion/shrinking animation

    def _expanded_ended(self):
        """Function executed after an expansion/shrinking animation ended."""
        if self._expanded == False:                             # If the window is not expanded
            self.setMaximumWidth(self.width())                      # Saves maximum width as the current size (avoids resizing)
            self.ui_elements.infoFrame.setVisible(False)            # Hides info frame
        else:                                                   # If the window is expanded
            self.setMinimumWidth(self.width())                      # Saves maximum width as the current size (avoids resizing)
        self._expanding.emit(False)                             # Emits signal informing that the expansion animation ended

    def _toggle_log_box(self, checked):
        """Toggles the log box

        Parameters
        ----------
        checked : bool
            State of the action "actionShow_Log"
        """
        if checked is True:                                 #TODO: Abre por padrão o último logger (o da data atual caso exista), mas possibita a abertura de outros logs de outras datas
            try:
                if self.log_file is not None:               # Checks if the log file path is defined
                    self._read_log_file(self.log_file)          # Reads the log file and saves its content
                    self.log_box.show()                         # Show log content in a separate window
                else:                                       # If the log file path is not defined
                    QMessageBox.information(                                            
                        None,                           # Parent widget (None centers on the screen; 'self' for a parent window)
                        "Attention",  
                        "Log file path was not defined."   # Informs the user that the log file path was not defined
                    )
            except Exception as e:
                print(f"{str(e)}")
        else:
            # self.log_box.hide()
            self.log_box.close()
        
    def _closed_log_box(self):
        """Guarantees that the action is unchecked if the Log Box is closed by pressing the X button"""
        self.ui_elements.actionShow_Log.setChecked(False)                   # Unchecks logBox action when the logBox is closed


    def _read_log_file(self, file_path):
        """Open LOG file and read its content"""
        with open(file_path, "r") as file:                  # Opens log file in read only mode  
            log_content = file.read()                           # Saves log content
            self.log_box.txtLog.setPlainText(log_content)       # Puts the log content in the log window text box
            file.close()                                        # Closes the log file

    def _run_simulator(self, checked):
        """Opens the simulator window"""

        client = ClientSimulator()                              # Instantiates the client simulator
        client.client_ID = self._num_clients + 100              # Clients ID number beging in 100
        client.name = f"Simulador {str(self._num_clients)}"     # Names the client simulator according to the number of clients
        client.transaction_ID = 0                               # Resets the client transaction ID

        client.sig.connect(self._simulator_closed)              # Connects closed signal to the function that must be executed when a client is closed
        client.move(self.pos() + QPoint(self.width(), 0))       # Positions the client window next to the main window

        self.clients.append(client)                             # Adds the new client to the 'clients' pool
        
        self.clients[len(self.clients)-1].show()                # Shows the client that was created
        self._num_clients+=1                                    # Adds the number of clients

        print(self.clients)                                     # Prints the list of clients

    def _simulator_closed(self, msg):
        """ Receives closed window signal from the simulator """
        for index, client in enumerate(self.clients):               # Enumerates all clients in the pool
            if msg == client.client_ID:                                 # Selects the client that was closed according to the ID sent by the signal 'msg'
                removed = self.clients.pop(index)                       # Removes the closed client from the pool
                print(f"Cliente {removed.client_ID} encerrado")         # Prints the client that was removed

        print(self.clients)                                         # Prints the list of clients

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
        if QSystemTrayIcon.ActivationReason.DoubleClick:      # If a double click was detected
            self._restore_from_tray()                                   # Restores the window


if __name__ == "__main__":

    logger = init_logging()                     # Configures and initializes the logger
    app = QtWidgets.QApplication([])            # Instantiates QApplication

    main_window1 = FocuserOPD()                 # Instantiates main window
    main_window1.show()                         # Shows main window    
    
    logger.info("Focuser was started")
    
    sys.exit(app.exec())                        # Executes and waits for end of execution