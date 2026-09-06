from abc import ABC, abstractmethod


class AudioSource(ABC):

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def stop(self):
        pass
