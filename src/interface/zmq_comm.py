from src.interface.comm_protocol import CommProtocol

# from src.core.server import ServerJson
from src.utils.constants import ServerJsonKeys as SJson
import zmq
import json
from datetime import datetime

class zmqComm(CommProtocol):
    def __init__(self, ip: str, port_pub: str = None, port_rep: str = None,
                  port_req: str = None):
        super().__init__()

        self._connected = False

        self.context:zmq.Context = None
        self.ip_address = ip
        if port_pub:
            self.port_pub = port_pub
            self.publisher:zmq.Socket = None
        if port_rep:
            self.port_rep = port_rep
            self.replier:zmq.Socket = None  # Receives REQ and sends REP
        if port_req:
            self.port_req = port_req
            self.requester: zmq.Socket = None
        self.poller:zmq.Poller = None
        self.connection_speed = 0
        self._server_connected:bool = False

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
                self.publisher.bind(f"tcp://{self.ip_address}:{self.port_pub}")             # Binds PUB to * IP address and configured PUB port
                print(f"Publisher binded to {self.ip_address}:{self.port_pub}")
            except Exception as e:
                raise ConnectionError(f'Error Binding Publisher: {str(e)}')

            try:
                # Command REP
                self.replier = self.context.socket(zmq.REP)                                 # Creates REP
                self.replier.bind(f"tcp://{self.ip_address}:{self.port_rep}")               # Binds REP to * IP adress and configured REP port
                print(f"REP binded to {self.ip_address}:{self.port_rep}")
            except Exception as e:
                raise ConnectionError(f'Error Binding Replier: {str(e)}')

            # Poller
            self.poller = zmq.Poller()                                                      # Creates Poller
            self.poller.register(self.replier, zmq.POLLIN)                                  # Register poller to monitoring REP
            self._connected = True
            return self._connected

    
    def disconnect(self) -> bool:
        if self._connected:
            try:                                                  
                    self.publisher.unbind(f"{self.publisher.last_endpoint.decode()}")           # Unbinds publisher considering last endpoint
                    self.publisher = None
            except Exception as e:
                raise ConnectionError(f'Error closing Publisher connection: {str(e)}')
            try:
                    self.replier.unbind(f"{self.replier.last_endpoint.decode()}")               # Unbinds replier considering last endpoint                         
                    self.replier = None
            except Exception as e:
                raise(f'Error closing Replier connection: {str(e)}')
            
            if self.context is not None:                                                    # If context is instantiated
                self.context.destroy()                                                          # Destroy context
                self.context = None                                                             # Reassign context to allow for new instantiation
            self._connected = False
            return self._connected
        else:
            raise ConnectionError(f'ZMQ communication is already closed.')
    
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
        timestamp = datetime.now()
        info[SJson.TIMESTAMP] = datetime.isoformat(timestamp, timespec='milliseconds')              # Sets status timestamp
        json_string = json.dumps(info)
        try:      
            self.publisher.send_string(json_string)                                        # If no error occurred while publishing logs the published JSON string
            return timestamp                                                                          # Returns time after publish #TODO: Isso não é necessário
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
        """Replies to the client

        Parameters
        ----------
        msg : str
            Response message to be sent to the client
        """
        self.replier.send_string(msg)

        