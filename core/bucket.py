from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .device import ClientDevice

class ConnectionBucket:
    connectionList: list['ClientDevice'] = []
    _registry: dict[str, list] = {}

    def get_client_by_id(self, clientID: tuple) -> 'ClientDevice | None':
        if not clientID: return None

        data = [client for client in self.connectionList if client.clientUniqueID == clientID[0]]
        return data[0] if data else None
