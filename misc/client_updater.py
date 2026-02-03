from PyQt5.QtCore import QRunnable, QObject, pyqtSignal
import zmq
import json

class UpdaterSignals(QObject):

    poller = pyqtSignal(object)         # Object "zmq.Poller"
    subscriber = pyqtSignal(object)     # object "zmq.SyncSocket"

    message = pyqtSignal(str)
    clientID = pyqtSignal(str)
    homing = pyqtSignal(bool)
    is_moving = pyqtSignal(bool)
    connected = pyqtSignal(bool)
    position = pyqtSignal(int)

    lbl_clientId_style = pyqtSignal(str)
    lbl_conn_style = pyqtSignal(str)
    lbl_init_style = pyqtSignal(str)
    lbl_mov_style = pyqtSignal(str)


class Updater(QRunnable):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.signals = UpdaterSignals()
        self.signals.poller = kwargs.get("poller", 0)
        self.signals.subscriber = kwargs.get("subscriber", 0)

        self._clientId = 0
        self._connected = False
        self._homing = False
        self._isMoving = False

        self.finished = False
        self.running = True

    def run(self):
        try:
            while self.running:
                # print(self.running)
                # print("programa rodando")
                self.socks = dict(self.signals.poller.poll(100))
                if self.socks.get(self.signals.subscriber) == zmq.POLLIN:
                    received = self.signals.subscriber.recv_string()
                    self.signals.message.emit(received)
                    data = json.loads(received)
                    try:
                        # self.signals.message.emit(str(data["position"]))
                        self.signals.position.emit(int(data["position"]))
                        if data["cmd"]["clientId"] != self._clientId:
                            self._clientId = data["cmd"]["clientId"]
                            if self._clientId == 0:
                                self.signals.clientID.emit("")
                                self.signals.lbl_clientId_style.emit("background-color: indianred")
                            else:                                
                                self.signals.clientID.emit(str(data["cmd"]["clientId"]))
                                self.signals.lbl_clientId_style.emit("background-color: lightgreen")
                            print(data["cmd"]["clientId"])
                        if data["connected"] != self._connected:
                            self._connected = data["connected"]
                            self.signals.connected.emit(self._connected)
                            if self._connected is False:
                                self.signals.lbl_conn_style.emit("background-color: indianred")
                            else:                                
                                self.signals.lbl_conn_style.emit("background-color: lightgreen")
                        if data["homing"] != self._homing:
                            self._homing = data["homing"]
                            self.signals.connected.emit(self._homing)
                            if self._homing is False:
                                self.signals.lbl_init_style.emit("background-color: indianred")
                            else:                                
                                self.signals.lbl_init_style.emit("background-color: lightgreen")
                        if data["isMoving"] != self._isMoving:
                            self._isMoving = data["isMoving"]
                            self.signals.connected.emit(self._isMoving)
                            if self._isMoving is False:
                                self.signals.lbl_mov_style.emit("background-color: indianred")
                            else:                                
                                self.signals.lbl_mov_style.emit("background-color: lightgreen")
                        
                    except Exception as e:
                        print(e)
                # print(self.finished)
            self.finished = True
        except Exception as e:
            print(e)
        finally:
            self.finished = True

    def stop(self):
        self.running = False