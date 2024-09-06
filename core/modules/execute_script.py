import typing, threading, ctypes
from datetime import datetime

if typing.TYPE_CHECKING:
    from core.handler import ServerHandler

class Process(threading.Thread):
    def __init__(self, socket: 'ServerHandler', script: str, fileName: str) -> None:
        threading.Thread.__init__(self)
        self.script, self.socket, self.filename = (
            script, socket, fileName
        )

    def run(self) -> None:
        self.socket.runningProccess[str(self.ident)] = {
            'started_on': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
            'fileName': self.filename,
            'process': self
        }

        try:
            exec(self.script)

        finally:
            del self.socket.runningProccess[str(self.ident)]

    def kill(self) -> None:
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, ctypes.py_object(SystemExit))
        if (res > 1):
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)

def run(socket: 'ServerHandler', fileName: str, script: str) -> None:
    proc: threading.Thread = Process(socket = socket, script = script, fileName = fileName)
    proc.start()

    print(proc.ident)
    socket.socketInstance.send_packet(str(proc.ident))
