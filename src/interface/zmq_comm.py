from src.interface.comm_protocol import CommProtocol

# from src.core.server import ServerJson
from src.utils.constants import ServerJsonKeys as SJson
import zmq
import json
from datetime import datetime, UTC
import threading
from dataclasses import dataclass 

@dataclass
class PubControl:
    pub_interval: float
    stop_event: threading.Event
    thread: threading.Thread | None


class zmqComm(CommProtocol):
    def __init__(self, ip: str, port_pub: str | None = None, port_rep: str | None = None,
                  port_req: str | None = None, pub_interval: float = 1.0):
        super().__init__()

        self._connected = False

        self.context:zmq.Context | None = None
        self.ip_address = ip
        if port_pub:
            self.port_pub = port_pub
            self.publisher:zmq.Socket | None = None
        if port_rep:
            self.port_rep = port_rep
            self.replier:zmq.Socket | None = None  # Receives REQ and sends REP
        if port_req:
            self.port_req = port_req
            self.requester: zmq.Socket | None = None
        self.poller:zmq.Poller | None = None
        self.connection_speed = 0
        self._server_connected:bool = False

        # self.pub_interval = pub_interval
        # self.stop_event = threading.Event()
        # self.thread: threading.Thread | None = None
        # self.status_pub = status_pub        # Injection of object with the information to be published (json)

    def connect(self) -> bool:
        """Starts Server ZeroMQ, creating context 
        then binding PUB and REP sockets

        :raises ConnectionError: Binding pub error
        :raises ConnectionError: Binding req error
        """
        if not self._connected:
            self.context = zmq.Context()                                                    # Creates context

            try:
                # Status Publisher
                self.publisher = self.context.socket(zmq.PUB)                               # Creates PUB
                if self.publisher:
                    self.publisher.bind(f"tcp://{self.ip_address}:{self.port_pub}")             # Binds PUB to * IP address and configured PUB port
                    print(f"Publisher binded to {self.ip_address}:{self.port_pub}")
                else:
                    raise ConnectionError(f"Error Binding Publisher: Returned 'None' when binding publisher")
            except Exception as e:
                raise ConnectionError(f'Error Binding Publisher: {str(e)}')

            try:
                # Command REP
                self.replier = self.context.socket(zmq.REP)                                 # Creates REP
                if self.replier:
                    self.replier.bind(f"tcp://{self.ip_address}:{self.port_rep}")               # Binds REP to * IP adress and configured REP port
                    print(f"REP binded to {self.ip_address}:{self.port_rep}")
                else:
                    raise ConnectionError(f"Error Binding Replier: Returned 'None' when binding replier")
            except Exception as e:
                raise ConnectionError(f'Error Binding Replier: {str(e)}')

            # Poller
            self.poller = zmq.Poller()                                                      # Creates Poller
            self.poller.register(self.replier, zmq.POLLIN)                                  # Register poller to monitoring REP
            self._connected = True

            return self._connected
        else:
            raise RuntimeError('ZMQ already connected')

    
    def disconnect(self) -> bool:
        if self._connected:
            try:                                                  
                if self.publisher:
                    # self.stop_publisher()
                    endpoint = self.publisher.last_endpoint
                    if isinstance(endpoint, bytes):
                        last_pub_endpoint = endpoint.decode()
                    else:
                        last_pub_endpoint = str(endpoint)
                    self.publisher.unbind(last_pub_endpoint)           # Unbinds publisher considering last endpoint
                    self.publisher = None
            except Exception as e:
                raise ConnectionError(f'Error closing Publisher connection: {str(e)}')
            try:
                if self.replier:
                    endpoint = self.replier.last_endpoint
                    if isinstance(endpoint, bytes):
                        last_rep_endpoint = endpoint.decode()
                    else:
                        last_rep_endpoint = str(endpoint)
                    self.replier.unbind(last_rep_endpoint)               # Unbinds replier considering last endpoint                         
                    self.replier = None
            except Exception as e:
                raise ConnectionError(f'Error closing Replier connection: {str(e)}')
            
            if self.context is not None:                                                    # If context is instantiated
                self.context.destroy()                                                          # Destroy context
                self.context = None                                                             # Reassign context to allow for new instantiation
            self._connected = False
            return self._connected
        else:
            raise RuntimeError(f'ZMQ communication is already closed.')
    
    def receive(self):
        return super().receive()
    
    def send(self, msg):
        return super().send(msg)

    def pub(self, info: dict) -> datetime :
        """Publishes information  via ZeroMQ

        :param info: Information to be published to ZMQ
        :type info: dict
        :return: String with timestamp of the moment of the pub
        :rtype: str
        """
        timestamp = datetime.now(UTC).replace(tzinfo=None)
        info[SJson.TIMESTAMP] = datetime.isoformat(timestamp, timespec='milliseconds')              # Sets status timestamp
        json_string = json.dumps(info)
        try:      
            if self.publisher:
                self.publisher.send_string(json_string)                                        # If no error occurred while publishing logs the published JSON string
                return timestamp                                                                         # Returns time after publish #TODO: Isso não é necessário
            else:
                raise Exception(f'Error publishing JSON: Publisher not defined')
        except Exception as e:
            raise Exception(f'Error publishing JSON: {str(e)}')
    
    def stop_poller(self) -> str:
        """Unregisters the ZMQ poller"""
        try:
            if self.poller:                                         # If poller is defined
                self.poller.unregister(self.replier)                    # Unregisters poller
                self.poller = None                                      # Reassigns poller to allow new instantiation
            return f'ZMQ poller unregistered'
        except Exception as e:
            return f'Failed to unregister ZMQ poller: {str(e)}'
        
    def reply(self, msg: str):
        """Replies to the client safely without blocking the polling loop.

        Parameters
        ----------
        msg : str
            Response message to be sent to the client
        """
        if not self.replier:
            raise RuntimeError("Error ZMQ reply: Replier not defined")
            
        try:
            # zmq.DONTWAIT ensures that if the client vanished, 
            # the function returns instantly instead of freezing your loop.
            self.replier.send_string(msg, flags=zmq.DONTWAIT)
            
        except zmq.Again:
            # This exception happens if the message cannot be sent immediately
            print("Warning ZMQ reply: Client disconnected or buffer full. Dropping message.")
            
        except zmq.ZMQError as e:
            # Catches strict State Machine Violations (e.g., sending without receiving)
            print(f"Error ZMQ reply: State violation or socket error: {e}")


        # """Replies to the client

        # Parameters
        # ----------
        # msg : str
        #     Response message to be sent to the client
        # """
        # if self.replier:
        #     self.replier.send_string(msg)
        # else:
        #     raise RuntimeError("Error ZMQ reply: Replier not defined")





    # def start_publisher(self):
    #     "Starts timed publisher execution"
    #     if self.thread is not None and self.thread.is_alive():
    #         raise RuntimeError("Publisher already running")
    #     else:
    #         if self.publisher:
    #             self.stop_event.clear()
    #             self.thread = threading.Thread(target=self._run, daemon=True)
    #             self.thread.start()
    #             print("[+] Started publishing focuser status")
    #         else:
    #             raise RuntimeError("Error starting publisher thread: Publisher not defined.")
        
    # def stop_publisher(self):
    #     "Stops timed publisher execution"
    #     if self.thread is None:
    #         raise RuntimeError("Error stopping publisher thread: Pubblisher thread not running.")
    #     else:
    #         if self.publisher:
    #             self.stop_event.set()
    #             self.thread.join()
    #             print("[-] Stopped publishing focuser status")
    #         else:
    #             raise RuntimeError("Error stopping publisher thread. Publisher not defined")

    # def _run(self):
    #     """ Method that will run in a thread to publish the status
    #     in a configurable interval."""
    #     while not self.stop_event.wait(timeout=self.pub_interval):
    #         try:
    #             self.status_pub[SJson.TIMESTAMP] = self.pub(self.status_pub).isoformat("T", timespec='seconds') 
    #             print(f"[+] Status publicado: {self.status_pub[SJson.TIMESTAMP]}")
    #         except Exception as e:
    #             print(f"Error during PUB: {str(e)}")
