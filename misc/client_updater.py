from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
import zmq
import json
import time

class UpdaterSignals(QObject):

    # poller = pyqtSignal(object)         # Object "zmq.Poller"
    # subscriber = pyqtSignal(object)     # object "zmq.SyncSocket"
    poller: zmq.Poller | None = None         # Object "zmq.Poller"
    subscriber: zmq.SyncSocket | None = None     # object "zmq.SyncSocket"

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

    alarm = pyqtSignal(str, str)
    initialized = pyqtSignal(str, str)


class Updater(QRunnable):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.signals = UpdaterSignals()
        if "poller" in kwargs:
            self.signals.poller = kwargs["poller"]
        else:
            raise ValueError("poller argument is required")
        if "subscriber" in kwargs:
            self.signals.subscriber = kwargs["subscriber"]
        else:
            raise ValueError("subscriber argument is required")

        # self.signals.poller = kwargs.get("poller", 0)
        # self.signals.subscriber = kwargs.get("subscriber", 0)

        self._clientId = 0
        self._connected = False
        self._homing = False
        self._isMoving = False
        self._alarm = False
        self._initialized = False

        self.finished = False
        self.running = True

        self.data: dict = dict()

    @pyqtSlot()
    def run(self):
        try:
            while self.running and self.signals.poller is not None and self.signals.subscriber is not None:
                # print(self.running)
                # print("programa rodando")
                time.sleep(0.05)
                self.socks = dict(self.signals.poller.poll(10))             
                if self.socks.get(self.signals.subscriber) == zmq.POLLIN:
                    received = self.signals.subscriber.recv_string()        # type: ignore # subscriber signal is of type "zmq.SyncSocket" and has a method "recv_string"
                    self.signals.message.emit(received)
                    self.data = json.loads(received)
                    print(f"[ZMQ Client] Received: {self.data}")
                    print(f"data type: {type(self.data)}")
                    try:
                        # self.signals.message.emit(str(data["position"]))
                        self.signals.position.emit(round(self.data["position"]))
                        if self.data["cmd"]["clientId"] != self._clientId:
                            self._clientId = self.data["cmd"]["clientId"]
                            if self._clientId == 0:
                                # self.signals.clientID.emit("")
                                self.signals.lbl_clientId_style.emit("statusLed", "OFF")
                            else:                                
                                # self.signals.clientID.emit(str(data["cmd"]["clientId"]))
                                self.signals.lbl_clientId_style.emit("statusLed", "OK")
                            cmd = str(self.data["cmd"]["action"]).split("=")[0]
                            if cmd == "FOCUSIN":
                                self.signals.focus_in_status.emit("statusLed", "WAIT")
                            else:
                                self.signals.focus_in_status.emit("statusLed", "OFF")  
                            if cmd == "FOCUSOUT":
                                self.signals.focus_out_status.emit("statusLed", "WAIT")
                            else:
                                self.signals.focus_out_status.emit("statusLed", "OFF")    
                            # print(data["cmd"]["clientId"])
                        if self.data["connected"] != self._connected:
                            self._connected = self.data["connected"]
                            self.signals.connected.emit(self._connected)
                            if self._connected is False:
                                self.signals.lbl_conn_style.emit("statusLed", "OFF")
                            else:                                
                                self.signals.lbl_conn_style.emit("statusLed", "OK")
                        if self.data["homing"] != self._homing:
                            self._homing = self.data["homing"]
                            self.signals.homing.emit(self._homing)
                            if self._homing is False:
                                self.signals.lbl_init_style.emit("statusLed", "OFF")
                            else:                                
                                self.signals.lbl_init_style.emit("statusLed", "OK")
                        if self.data["isMoving"] != self._isMoving:
                            self._isMoving = self.data["isMoving"]
                            self.signals.is_moving.emit(self._isMoving)
                            if self._isMoving is False:
                                self.signals.lbl_mov_style.emit("statusLed", "OFF")
                            else:                                
                                self.signals.lbl_mov_style.emit("statusLed", "OK")
                        if self.data["alarm"] != self._alarm:
                            self._alarm = self.data["alarm"]
                            if self._alarm is False:
                                self.signals.alarm.emit("statusLed", "OFF")
                            else:                                
                                self.signals.alarm.emit("statusLed", "NOK")
                        if self.data["initialized"] != self._initialized:
                            self._initialized = self.data["initialized"]
                            if self._initialized is False:
                                self.signals.initialized.emit("statusLed", "OFF")
                            else:                                
                                self.signals.initialized.emit("statusLed", "OK")
                        
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