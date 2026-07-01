from abc import ABC, abstractmethod

class CommProtocol(ABC):
    _connected: bool

    @abstractmethod
    def connect(self) -> str | bool:
        """Must be defined by driver"""
        ...

    @abstractmethod
    def disconnect(self) -> str | bool:
        """Must be defined by driver"""
        ...

    @abstractmethod
    def send(self, msg: str) -> str:
        """Must be defined by driver"""
        raise RuntimeError("Method 'send' not defined in the driver")

    @abstractmethod
    def receive(self) -> str:
        """Must be defined by driver"""
        raise RuntimeError("Method 'receive' not defined in the driver")
    