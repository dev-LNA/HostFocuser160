from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QTimer, Qt, QPoint, QPropertyAnimation, QSize, QEasingCurve, QDynamicPropertyChangeEvent, QObject, QEvent, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap, QShortcut, QKeySequence
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QMenu, QSystemTrayIcon, QPushButton,QToolBar, QLabel, QWidget, QProgressBar

import sys
import os
from threading import Thread
from src.core.log import init_logging
import time
import shutil

from src.core.server import Server
from misc.client_sample import ClientSimulator
from misc.ui_intellisense import UiWidgets
from src.utils.constants import constants, DynamicProperties
from src.utils.constants import ServerJsonKeys as SJson
from src.utils.motor import MotorModels

from misc.log_box import LogBox
from misc.settings import SettingsWindow
from misc.info import ServerInfoWindow
from misc.load_bar import LoadBar

try:
    from src.core.config import Config, update_config
    CONFIG_FILE = True
    ERR_VALUE = None
except Exception as e:
    ERR_VALUE = str(e)
    CONFIG_FILE = False

# def resource_path(relative_path):
#     """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller """
#     if hasattr(sys, '_MEIPASS'):
#         # No executável, sys._MEIPASS é a raiz da pasta temporária
#         base_path = sys._MEIPASS
#     else:
#         # No desenvolvimento 'main4.py' está na raiz
#         base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ""))

#     return os.path.normpath(os.path.join(base_path, relative_path))

def resource_path(relative_path, external=False):
    """
    Função universal para localização de arquivos.
    - No VS Code: Segue a estrutura de pastas do projeto.
    - No EXE (Interno): Busca arquivos embutidos (psw.cfg, assets).
    - No EXE (Externo): Busca arquivos na pasta do usuário (config.toml).
    """
    # 1. Checa se o programa está rodando como um executável do PyInstaller
    frozen = getattr(sys, 'frozen', False)
    
    if frozen:  # Se 'False' significa que está rodando do Visual Studio (modo desenvolvimento)
        if external:
            # Caminho ao lado do arquivo .exe
            base_path = os.path.dirname(sys.executable)
        else:
            # Caminho dentro da pasta temporária do .exe
            base_path = sys._MEIPASS
    else:
        # 2. Modo Desenvolvimento (Visual Studio / VS Code)
        # Como este arquivo está em src/core, subimos dois níveis para chegar na raiz
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ""))

    return os.path.normpath(os.path.join(base_path, relative_path))

main_ui_path = resource_path('assets/ui/main.ui')
load_window_path = resource_path('assets/ui/load.ui')
icon_tray = resource_path('assets/icon.png')

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
        self._server_info_window = None
        self.log_box:LogBox = LogBox()          # Initialize log window
        self.log_box.closed.connect(self._closed_log_box)               # Signal to inform the main window that the log box was closed by pressing the X button            
        self.load_window = None                 # Initialize load window as None    

        self.log_file = r"logs/focuser.log"                             # Path to log file              # TODO: inicializar o arquivo com o nome padronizado, de acordo com a data (dia inicia ao meio dia)

        self.server = Server(logger)

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

        
    #--- UI elements initialization and configuration
    #   Initializes every UI element of the main window.
    #   The initialization will set the initial values and the behavior of the elements.        
        self.ui_elements = UiWidgets(self, "main")                      # Creates "ui_elements" widget to hold intellisense references to the widgets
        self.setFixedSize(QSize(312, 550))                              # Sets a fixed size for the main window
        self.ui_elements.pageSelect.setCurrentIndex(0)                  # Initializes the main window in the focalizer seletion page

        self.ui_elements.btnStartServer.clicked.connect(self._config_server)
        self.menuBar().setVisible(False)                                        # The menu bar is not displayed in the focalizer selection page
        self.ui_elements.toolBar.setVisible(False)                              # The tool bar is not displayed in the focalizer selection page

        self.ui_elements.btnStart.clicked.connect(self._start)
        self.ui_elements.btnStop.clicked.connect(self._stop)
        self.ui_elements.btnArrow.clicked.connect(self._show_info)

        self.ui_elements.actionShow_Log.triggered.connect(self._toggle_log_box)
        self.ui_elements.actionClient_Simulator.triggered.connect(self._run_simulator)
        self.ui_elements.actionHide.triggered.connect(self._minimize_to_tray)    
        self.ui_elements.actionAbout.triggered.connect(self._open_server_info)
        self.ui_elements.actionEngineering.triggered.connect(self._open_settings)
        self.ui_elements.actionShow_toolbar.triggered.connect(              
            lambda checked: self.ui_elements.toolBar.setVisible(checked)    # Action to toggle toolbar
        )   

        self.ui_elements.lblSocketIP.setText("")
        self.ui_elements.lblPortPUB.setText("")
        self.ui_elements.lblPortREP.setText("")
        self.ui_elements.infoFrame.setVisible(False)
        self.ui_elements.posSlider.setValue(0) 

        self.ui_elements.conBarServerRouter.setProperty("conStatusBar", "waiting")
        self.ui_elements.conBarRouterMotor.setProperty("conStatusBar", "waiting")


    # Configuration of application wide shortcuts
    # Shortcuts without a visual representation are configured as a 'QShortcut'
        self.ui_elements.actionHide.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.ui_elements.actionShow_Log.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)

        shortcut = QShortcut(QKeySequence("Ctrl+M"), self)
        shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        shortcut.activated.connect(lambda: self.menuBar().setHidden(not self.menuBar().isHidden()))

    # Configuration of signals
        self.server.signals.socket_ip.connect(self.ui_elements.lblSocketIP.setText)
        self.server.signals.port_pub.connect(self.ui_elements.lblPortPUB.setText)
        self.server.signals.port_rep.connect(self.ui_elements.lblPortREP.setText)

        self.server.signals.router_status.info.connect(self.ui_elements.conBarServerRouter.setProperty)
        self.server.signals.motor_status.info.connect(self.ui_elements.conBarRouterMotor.setProperty)

        self.server.signals.router_status.info.connect(self.ui_elements.ledRouter.setProperty)
        self.server.signals.motor_status.info.connect(self.ui_elements.ledMotor.setProperty)

        self.server.signals.server_status.status.connect(self.ui_elements.btnStart.setDisabled)
        self.server.signals.server_status.status.connect(self.ui_elements.btnStop.setEnabled)
        self.server.signals.server_status.info.connect(self.ui_elements.ledServer.setProperty)

        self.server.signals.status_message.connect(lambda msg: self.statusBar().showMessage(msg, 10000))
        self.server.signals.connection_speed.connect(self.ui_elements.lblComSpeed.setText)
        
        # self.server.signals.position_str.connect(self.ui_elements.lblPosition_val.setText)
        # self.server.signals.encoder.connect(self.ui_elements.lblEncoder_val.setText)

        # self.server.signals.position_int.connect(self.ui_elements.posSlider.setValue)
        self.server.signals.max_pos.connect(self.ui_elements.posSlider.setMaximum)
        self.server.signals.backlash.connect(self.ui_elements.posSlider.setMinimum)

        
        # self.server.signals.moving.info.connect(self.ui_elements.ledMoving.setProperty)
        # self.server.signals.lim_min.info.connect(self.ui_elements.ledLimMin.setProperty)
        # self.server.signals.lim_max.info.connect(self.ui_elements.ledLimMax.setProperty)
        # self.server.signals.initialized.info.connect(self.ui_elements.ledHome.setProperty)
        # self.server.signals.parking.info.connect(self.ui_elements.ledPark.setProperty)

        self.server.signals.motor_status.status.connect(self.ui_elements.gbConnectivity.setEnabled)
        self.server.signals.motor_status.status.connect(self.ui_elements.gbCommandInfo.setEnabled)
        self.server.signals.motor_status.status.connect(self.ui_elements.gbFocuserStatus.setEnabled)

        # self.server.signals.firmware_status.connect(self.ui_elements.lblStatus_val.setText)
        self.server.signals.last_command.connect(self._parse_last_command)

    #--- Events definitions
        #   sets animations and install event filter on objects
        self.ui_elements.conBarServerRouter.setValue(0)
        self.ui_elements.conBarServerRouter.animation = QPropertyAnimation(                         # Animation for the connection bar between server and router
            self.ui_elements.conBarServerRouter, b'value', self                                     # The animation is triggered when the property value is changed
        )
        self.ui_elements.conBarServerRouter.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.ui_elements.conBarServerRouter.animation.setDuration(300)

        self.ui_elements.conBarRouterMotor.setValue(0)
        self.ui_elements.conBarRouterMotor.animation = QPropertyAnimation(                          # Animation for the connection bar between router and motor
            self.ui_elements.conBarRouterMotor, b'value', self                                      # The animation is triggered when the property value is changed
        )
        self.ui_elements.conBarRouterMotor.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.ui_elements.conBarRouterMotor.animation.setDuration(300)
        
        # Window animation
        self.window_expand_animation = QPropertyAnimation(self, b"size")                                          # Animation for the window expansion
        self.window_expand_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.window_expand_animation.setDuration(1000)
        self._starting_size = QSize(312, self.height())                                             # Holds the initial screen size
        self.window_expand_animation.finished.connect(self._expanded_ended)                                       # Connects a function to run after the animation is over
        self._expanding.connect(self.ui_elements.btnArrow.setDisabled)                              # Disables the arrow expansion button while the animation is being executed

        self._progress_bar = LoadBar()                                                  # Creates load bar

        self.statusBar().addPermanentWidget(self._progress_bar)                         # Add load bar to status bar, it is not visible by default and is made visible when needed


        # Install event filters in the LEDs so that when a property is changed the values are automatically updated
        for item in self.findChildren(QWidget):
            for prop in DynamicProperties:
                if item.property(prop):
                    item.installEventFilter(self)


######### OUTROS TESTES ##########
        self.ui_elements.btnTestes.clicked.connect(self._testes)


    def _config_server(self):
        """Sets configurations according to the selected focuser.
        The focuser is selected in the focuser selection page when the server is initialized and cannot be changed after the initial selection."""
        
        
        if self.ui_elements.rb160.isChecked():
            # Se 'False' significa que está rodando do Visual Studio (modo desenvolvimento)
            # Nesse caso a pasta com as configurações está dentro de 'src'
            if getattr(sys, 'frozen', False):
                config_file_path = resource_path("config/config_PE160.toml", external=True) #"src/config/config_PE160.toml"
            else:
                config_file_path = "src/config/config_PE160.toml"

            print(f'Loading configuration file -> {config_file_path}')
            logger.info(f'Loading configuration file -> {config_file_path}')

            # Loads the configuration file from the path according to the selected focuser
            self._load_config_file(config_file_path)

        elif self.ui_elements.rbIAG.isChecked():
            # Se 'False' significa que está rodando do Visual Studio (modo desenvolvimento)
            # Nesse caso a pasta com as configurações está dentro de 'src'
            if getattr(sys, 'frozen', False):
                config_file_path = resource_path("config/config_IAG.toml", external=True)
            else:
                config_file_path ="src/config/config_IAG.toml"

            print(f'Loading configuration file -> {config_file_path}')
            logger.info(f'Loading configuration file -> {config_file_path}')

            # Loads the configuration file from the path according to the selected focuser
            self._load_config_file(config_file_path)



        
        if not CONFIG_FILE:                     # If configuration file was not found a message is displayed and the program will close after check
            close = QMessageBox()                                                       # Creates message window
            close.setText(f"Arquivo de configuração com problemas!\n{ERR_VALUE}")       # Config window message
            logger.error(f'Configuration file not defined. {ERR_VALUE}')                
            close.setStandardButtons(QMessageBox.StandardButton.Ok)                     # Config window button
            close = close.exec()                                                        # Opens window and waits button press

            if close == QMessageBox.StandardButton.Ok:                                  # After press ok button
                sys.exit()                                                                  # Ends program
        
        
        
        if self.ui_elements.rb160.isChecked():                              # Checks radio button value
            print("INICIAR FOCALIZADOR DO 160")                                 # If the PE 160 was chosen
            # Config.focuser = "160"                                              # Changes Config according to selection
            # Config.device_ip = get_toml('Device', 'ip_160')                     # Sets the IP address according to selection
            self.ui_elements.lblTitle.setText("Focuser 160")                    # Sets main window label according to selection
            self.server.init_device(MotorModels.ARCUS_DMX_ETH)                   # Initializes the motor driver according to the focuser
            self.ui_elements.gbFocuserStatus.setFixedSize(QSize(295,240))
            self._init_focuser()                                                # Changes to the server page                                  
        elif self.ui_elements.rbIAG.isChecked():                            # Checks radio button value
            print("INICIAR FOCALIZADOR DO IAG")                                 # If the IAG was chosen
            # Config.focuser = "IAG"                                              # Changes Config according to selection
            # Config.device_ip = get_toml('Device', 'ip_iag')                     # Sets the IP address according to selection
            self.ui_elements.lblTitle.setText("Focuser IAG")                    # Sets main window label according to selection
            self.server.init_device(MotorModels.AMP_MOTOR)                       # Initializes the motor driver according to the focuser
            self.ui_elements.gbFocuserStatus.setFixedSize(QSize(295,240))
            self.ui_elements.lblMotor.setText("CLP")
            self._init_focuser()                                                # Changes to the server page      
        else:                                                               # If the 'start server' button is pressed with no focuser selected shows a message
            QMessageBox.information(                                            
                None,                                                           # Parent widget (None centers on the screen; 'self' for a parent window)
                "Attention",  
                "A focuser must be selected."                                   # Informs the user that a focuser must be selected
            )

    def _load_config_file(self, config_file_path: str):
        try:
            # from pathlib import Path
            # config_path = Path("src/config/config.toml")
            # config_path.unlink(missing_ok=True)

            config_path = resource_path('src/config/config.toml')       
            shutil.copy(config_file_path, config_path)            #TODO: 'copy' do not retain the metadata, if metadata is needed change to '.copy2'
            logger.info(f"Loaded configuration file: {config_file_path}")
            update_config()

        except FileNotFoundError:
            print("The source file was not found.")
            logger.error(f"Could not load configuration file. The source file was not found.")
        except PermissionError:
            print("Permission denied to access files or destination.")
            logger.error(f"Could not load configuration file. Permission denied to access files or destination.")
        except shutil.SameFileError:
            print("Source and destination are the same file.")
            logger.error(f"Could not load configuration file. Source and destination are the same file.")

   
    def _init_focuser(self):
        """Initializes the focuser
        Sets the visibility for the menuBar an toolBar, changes the 
        page to show the focuser main window and starts the server if
        auto startup is configured """
        # Now that the motor was instantiated the motor signals can be connected
        self.server.motor.signals.moving.info.connect(self.ui_elements.ledMoving.setProperty)
        self.server.motor.signals.lim_min.info.connect(self.ui_elements.ledLimMin.setProperty)
        self.server.motor.signals.lim_max.info.connect(self.ui_elements.ledLimMax.setProperty)
        self.server.motor.signals.position.string.connect(self.ui_elements.lblPosition_val.setText)
        self.server.motor.signals.position.value.connect(self.ui_elements.posSlider.setValue)
        self.server.motor.signals.encoder.connect(self.ui_elements.lblEncoder_val.setText)
        self.server.motor.signals.initialized.info.connect(self.ui_elements.ledHome.setProperty)
        self.server.motor.signals.firmware_status.connect(self.ui_elements.lblStatus_val.setText)
        self.server.motor.signals.parking.info.connect(self.ui_elements.ledPark.setProperty)
        self.server.motor.signals.alarm.info.connect(self.ui_elements.ledAlarm.setProperty)

        self.server.motor.driver.driver_comm.run_focus_in.info.connect(self.ui_elements.ledFocusIn.setProperty)
        self.server.motor.driver.driver_comm.run_focus_out.info.connect(self.ui_elements.ledFocusOut.setProperty)
        self.server.motor.driver.driver_comm.run_park.info.connect(self.ui_elements.ledPark.setProperty)

        self.server.motor.signals.progress.value.connect(self._progress_bar.setVisible)
        self.server.motor.signals.progress.string.connect(self._progress_bar.progress.setValue)

        self.menuBar().setVisible(True)                                     # Sets menu bar visibility
        self.ui_elements.toolBar.setVisible(True)                           # Sets tool bar visibility
        self.server.server_online = False                               # Emits signal with initial server status as disconnected
        self.ui_elements.pageSelect.setCurrentIndex(1)                      # Changes view to the main server page
        if Config.startup:                                                  # If configured to 'auto start'
            self._start()                                                       # Starts the server

    def _testes(self):
        
        self.server.teste()

    def _start(self):
        """Start server"""
        if self._run_thread and self._run_thread.is_alive():                # Checks if the thread is already being executed
            print("Still Alive")
            logger.warning(f'Trying to run server but server already running')
            return                                                              # If already running do nothing

        self._run_thread = Thread(target = self.server.run)                # If thread no running creates thread to execute the funtion 'run' on 'App'
        self._run_thread.start()                                            # Starts the thread

    def _stop(self):
        """Stops main program and the main loop at Application interface with Device"""
        while self.clients:             # Closes all opened client simulators
            self.clients[0].close()         # The close method will 'pop' the client from the list, so the client in position 0 is removed until there are no more clients opened

        if self._run_thread and self._run_thread.is_alive():    # If the server thread is running 
            self.server.stop_loop = True                            # Stops the thread loop
            self._run_thread.join()                                 # Joins the thread to wait until it is finished
            self.server.stop_poll()                                 #| The 'stop_poll' was separeted from the 'server.disconnect' to
                                                                    #| avoid problems during the server shutdown procedure
        if self.server:    
            self.server.disconnect()                               # Unregisters server ZMQ poll

    def _parse_last_command(self, data: dict):
        """Parses the information about the last command received by the server.
        This function is called according to the 'server' signal 'last_command', 
        which indicates that a new signal was received.

        Parameters
        ----------
        data : dict
            Dictionary holding the last command information
        """
        self.ui_elements.lblTime.setText(data[SJson.TIMESTAMP])                                     # Updates last command time
        # self.ui_elements.lblClientName_val.setText(data[SJson.CMD.value][SJson.CMD_CLIENT_NAME.value])                   # Updates last command client name
        self.ui_elements.lblClientID_val.setText(str(data[SJson.CMD.value][SJson.CMD_CLIENT_ID.value]))                  # Updates last command client ID
        self.ui_elements.lblTransactionId_val.setText(str(data[SJson.CMD.value][SJson.CMD_CLIENT_TRANSACTION_ID.value]))  # Updates last command client transaction number
        self.ui_elements.lblCommand_val.setText(data[SJson.CMD.value][SJson.CMD_ACTION.value])                          # Updates last command action
        if(data[SJson.CMD.value][SJson.CMD_ACTION.value] == "HOME" or data[SJson.CMD.value][SJson.CMD_ACTION] == "PARK"):                 # If the last command was 'HOME' or 'PARK'
            self.ui_elements.lblLastHoming_val.setText(data[SJson.TIMESTAMP])                           # Updates the last homing time

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

    def _open_server_info(self):
        
        if self._server_info_window is None:
            self._server_info_window = ServerInfoWindow()
            self._server_info_window.window_closed.connect(self._server_info_closed)
            self._server_info_window.show()

    def _server_info_closed(self, msg: bool):
        if msg is True:
            self._server_info_window.window_closed.disconnect(self._server_info_closed)
            self._server_info_window = None

    def _open_settings(self):
        """Opens the settings window"""
        #To open the settings the motor must be connected
        if self.server.motor.connected:
            if self._settings_window is None:
                self._settings_window = SettingsWindow(self.server.motor, logger)                                 # Starts the main window according to the initialized focuser
                self._settings_window.signals.window_closed.connect(self._settings_closed)                          # Connects function that must be executed when the settings window is closed
                self._settings_window.signals.changed_settings.connect(self._parse_changed_settings)               # Connects function to be executed when settings are changed
                self._settings_window.move(self.pos() + QPoint(self.width(), 0))                                    # Positions settings window next to the main window
                self._settings_window.show()                                                                        # Shows settings window
        else:
            msg = QMessageBox.information(                                                                      # Shows message to the user
                self,                                                                                       # Parent widget (None centers on the screen; 'self' for a parent window)
                "Attention",  
                "To open settings the focuser motor must be connected. \nConnect to motor?",                    # Asks the user if they want to connect to the motor
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)                         # Configures the message buttons
            if(msg == QMessageBox.StandardButton.Yes):                                                          # If the user whishes to connect the motor
                self._start()                                                                                       # Connects the server to the motor and starts server operation #TODO: Talvez seja bom ter essas coisas separadas, com um método só para conectar (criar o socket) e outro para iniciar a thread de App, pois a thread de App vai começar a fazer o polling de informações sem parar uma vez iniciada
                t = time.time()                                                                                     # Keeps current time
                while not self.server.motor.connected:                                                            # Waits 5 seconds while the server tries to connect to the motor
                    if round(time.time()-t, 3) > 5:                                                                     # If the server cannot connect after 5 seconds informs the user
                        QMessageBox.information(                                                                        # Shows message to the user
                            self,  # Parent widget (None centers on the screen; 'self' for a parent window)
                            "Attention",  
                            "The motor could not be reached after 5 seconds",                                           # Informs the user that the motor is not reachable
                            buttons=QMessageBox.StandardButton.Ok)                                                      # Configures the message button
                        self._stop()
                        break                                                                                           # Break the while loop and continues operation
                if self.server.motor.connected:                                                               # If the connection to the motor was successful
                    if self._settings_window is None:                                                               # If the settings windows was not yet defined
                        self._settings_window = SettingsWindow(self.server.motor, logger)                                 # Instantiate settings window
                        self._settings_window.signals.window_closed.connect(self._settings_closed)                  # Connects closed window signal
                        self._settings_window.signals.changed_settings.connect(self._parse_changed_settings)       # Connects signal to show the settings in the GUI
                        self._settings_window.move(self.pos() + QPoint(self.width(), 0))                            # Positions the settings window according to the main window position
                        self._settings_window.show()                                                                # Shows the settings window

    def _settings_closed(self, msg: bool):
        """Function executed when the settings window is closed.

        :param msg: Indicates that the settings window was closed
        :type msg: bool
        """
        #   To avoid astacking the signals connections it is necessary to 
        # disconnect the settings window signals before reassigning the 
        # _setting_window.
        if msg is True:                         # If the settings window was closed
            self._settings_window.signals.window_closed.disconnect(self._settings_closed)                          
            self._settings_window.signals.changed_settings.disconnect(self._parse_changed_settings)  
            self._settings_window = None            # Reassign the settings window to allow a new instantiation
            print("Configurações fechadas")

    def _parse_changed_settings(self, data: dict):
        """Parses the settings that were changed in the moto configuration and updates GUI elements that depends on the settings

        :param data: Dictionary with all the changed settings
        :type data: dict
        """
        if "MAX_POS" in data:                                                   # If the 'MAX_POS' is changed the slider must be resized accordingly
            self.ui_elements.posSlider.setMaximum(int(data["MAX_POS"]) + 5)         # Sets slider max value
            self.ui_elements.posSlider.setMinimum(-12)                              # Sets slider min value #TODO: Acho que esse valor vai ser dependente do 'backlash'

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

    def _update_gui_element(self, widget: QtWidgets):
        """Updates the GUI element style after an event occured.
        According to QT framework this functions must be executed to update visual elements when a property is changed.
        Re-polish the style to apply CSS changes linked to this property
        
        Parameters
        ----------
        widget : QtWidgets
            Widget to be updated
        """
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Process events.
        The events are processed according to the class of the object that called the event.

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
                    # The 'conStatusBar' property describes the current situation of the connection between 'server/router' and 'router/motor'
                    if obj.property("conStatusBar") == "waiting":           # Waiting to start connection
                        obj.animation.setEndValue(0)                            # The progress bar is set to 0 (not shown) and changes color to red (The color change is defined in the stylesheet)
                        obj.animation.start()                                   # Triggers the start of the animation
                    elif obj.property("conStatusBar") == "connecting":      # Connecting to the next device 'server to router' or 'router to motor'
                        obj.animation.setEndValue(50)                           # The progress bar is set to 50 and changes color to yellow (The color change is defined in the stylesheet)
                        obj.animation.start()                                   # Triggers the start of the animation
                    elif obj.property("conStatusBar") == "connected":       # The connection was estabilished
                        obj.animation.setEndValue(100)                          # The progress bar is set to 100 and changes color to green (The color change is defined in the stylesheet)
                        obj.animation.start()                                   # Triggers the start of the animation
                    self._update_gui_element(obj)                           # Updates the color of the progress bar
                    return True                                             # Returns OK
                    
            if obj.__class__ is QtWidgets.QLabel:
                # Animations related to labels
                    self._update_gui_element(obj)                           # Updates the color of the label
                    return True                                             # Returns OK
                
        # For all other events or objects, return False to allow normal handling
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """Close event

        Parameters
        ----------
        event : _type_
            _description_
        """
        close = QMessageBox()                                                                           # Creates confirmation window
        close.setWindowTitle("Close")                                                                   # Sets window title
        close.setText("Deseja sair?")                                                                   # Sets window message
        close.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)        # Sets window buttons
        close = close.exec()                                                                            # Shows window

        if close == QMessageBox.StandardButton.Yes:                                                     # If button 'Yes' pressed
            if self.ui_elements.pageSelect.currentIndex() == 1:                                             # In the first page no configuration was made so trying to disconnect generates errors
                self._stop()                                                                                # Stops the server execution
            event.accept()                                                                                  # Accepts the close event
        else:                                                                                           # If button "No" or X pressed
            event.ignore()  

if __name__ == "__main__":

    logger = init_logging()                     # Configures and initializes the logger
    app = QtWidgets.QApplication([])            # Instantiates QApplication

    main_window1 = FocuserOPD()                 # Instantiates main window
    main_window1.show()                         # Shows main window    
    
    logger.info("Focuser was started")
    
    sys.exit(app.exec())                        # Executes and waits for end of execution