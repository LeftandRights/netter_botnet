from dataclasses import dataclass, field

import pickle, hashlib

from .handler import ClientWrapper
from .bucket import ConnectionBucket

@dataclass
class ClientDevice:
    hostname: str
    publib_address: str
    local_address: str

    clientUniqueID: str
    additionalData: dict = field(default_factory = dict)

    def load_data(self, client_data: bytes, socketInstance: ClientWrapper, connectionBucket: ConnectionBucket) -> bool:
        print(self.additionalData)
        self.hostname, self.publib_address, self.local_address = pickle.loads(client_data)
        clientUniqueID: str = hashlib.sha256(str(self.hostname + self.publib_address + self.local_address).encode('UTF-8')).hexdigest()

        if (clientUniqueID not in [client.clientUniqueID for client in connectionBucket.connectionList]):
            connectionBucket.connectionList.append(self)
            socketInstance.send_packet('0') # Indicates the client is eligable to join the server

            self.socket: ClientWrapper = socketInstance
            self.clientUniqueID = clientUniqueID
            return True

        return False
