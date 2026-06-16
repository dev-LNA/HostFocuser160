from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
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

    lbl_clientId_style = pyqtSignal(str, str)
    lbl_conn_style = pyqtSignal(str, str)
    lbl_init_style = pyqtSignal(str, str)
    lbl_mov_style = pyqtSignal(str, str)

    focus_in_status = pyqtSignal(str, str)
    focus_out_status = pyqtSignal(str, str)


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

    @pyqtSlot()
    def run(self):
        try:
            while self.running:
                # print(self.running)
                # print("programa rodando")
                self.socks = dict(self.signals.poller.poll(10))
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
                                # self.signals.clientID.emit("")
                                self.signals.lbl_clientId_style.emit("statusLed", "OFF")
                            else:                                
                                # self.signals.clientID.emit(str(data["cmd"]["clientId"]))
                                self.signals.lbl_clientId_style.emit("statusLed", "OK")
                            cmd = str(data["cmd"]["action"]).split("=")[0]
                            if cmd == "FOCUSIN":
                                self.signals.focus_in_status.emit("statusLed", "WAIT")
                            else:
                                self.signals.focus_in_status.emit("statusLed", "OFF")  
                            if cmd == "FOCUSOUT":
                                self.signals.focus_out_status.emit("statusLed", "WAIT")
                            else:
                                self.signals.focus_out_status.emit("statusLed", "OFF")    
                            # print(data["cmd"]["clientId"])
                        if data["connected"] != self._connected:
                            self._connected = data["connected"]
                            self.signals.connected.emit(self._connected)
                            if self._connected is False:
                                self.signals.lbl_conn_style.emit("statusLed", "OFF")
                            else:                                
                                self.signals.lbl_conn_style.emit("statusLed", "OK")
                        if data["homing"] != self._homing:
                            self._homing = data["homing"]
                            self.signals.homing.emit(self._homing)
                            if self._homing is False:
                                self.signals.lbl_init_style.emit("statusLed", "OFF")
                            else:                                
                                self.signals.lbl_init_style.emit("statusLed", "OK")
                        if data["isMoving"] != self._isMoving:
                            self._isMoving = data["isMoving"]
                            self.signals.is_moving.emit(self._isMoving)
                            if self._isMoving is False:
                                self.signals.lbl_mov_style.emit("statusLed", "OFF")
                                pass
                            else:                                
                                self.signals.lbl_mov_style.emit("statusLed", "OK")
                                pass
                        
                    except Exception as e:
                        print(e)
                # print(self.finished)
            self.finished = True
        except Exception as e:
            print(e)
        finally:
            self.finished = True

    @pyqtSlot()
    def stop(self):
        self.running = False