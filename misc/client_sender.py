from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
import zmq
import json

import misc.client_sample

class ReqSenderSignals(QObject):

    req = pyqtSignal(object)         # Object "zmq.SyncSocket"
    timeout_error = pyqtSignal(bool)
    response = pyqtSignal(str)

    subscriber = pyqtSignal(object)     # object "zmq.SyncSocket"

class ReqSender(QRunnable):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.signals = ReqSenderSignals()
        self.signals.req = kwargs.get("req", 0)
    
        self._clientId = ""
        self._clientTransactionId = 0
        self._clientName = ""
        self._action = ""

        self._msg_json = {
            "clientId": 0,
            "clientTransactionId": 0,
            "clientName": "",
            "action": "STATUS"
        }

        self._send = False
        self._timeout = 0

        self.finished = True    
        self._running = True

    @pyqtSlot()
    def run(self):
        try: 
            # while self._running:
            if self._send is True:

                self._msg_json = {
                    "clientId": self._clientId,
                    "clientTransactionId": self._clientTransactionId,     
                    "clientName": self._clientName,
                    "action": self._action
                }

                print(f"client = {self._msg_json["clientId"]}")
                print(f"clientTransactionId = {self._msg_json["clientTransactionId"]}")
                print(f"cmd = {self._msg_json["action"]}")
                # self.finished = True

                self.signals.req.send_string(json.dumps(self._msg_json))

                poller = zmq.Poller()
                poller.register(self.signals.req, zmq.POLLIN)

                socks = dict(poller.poll(self._timeout))  # Timeout in milliseconds
                if socks.get(self.signals.req) == zmq.POLLIN:
                    try:
                        self.signals.response.emit(self.signals.req.recv_string())      # Emits the response
                    except Exception as e:
                        print(f"Error receiving response: {e}")                         #TODO: Adicionar um sinal de erro
                        self.finished = True
                        self._send = False
                        # break
                else:
                    print(f"No response received within {self._timeout} milliseconds.")
                    print(f"Resetting client...")
                    self.signals.timeout_error.emit(True)
                    # break
                self.finished = True
                self._send = False
            

        except Exception as e:
            print(e)
        finally:
            self._send = False
            self.finished = True

    @pyqtSlot()
    def stop(self):
        self._running = False

    @pyqtSlot()
    def send_request(self, client: misc.client_sample.ClientSimulator, action, timeout=1500):
        if self._send is False:                 # Checks if a message is already being processed    #TODO: Implementar uma fila de comandos?
            self._clientId = client.client_ID
            self._clientTransactionId = client.transaction_ID
            self._clientName = client.name
            self._action = action
            self._timeout = timeout
            self._send = True
            self.finished = False