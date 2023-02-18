from abc import ABC, abstractmethod

class Executor(ABC):

    def __init__(self):

        pass

    @abstractmethod
    def connect(self, addr = None, port = None, username = None, password = None):
        pass

    @abstractmethod
    def exec(self, command, handler = None):
        pass

    @abstractmethod
    def push(self, local, remote):
        pass

    @abstractmethod
    def pull(self, remote, local):
        pass