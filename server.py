from core.sock import NetterServer
from core.bucket import ConnectionBucket
from core.device import ClientDevice

from sys import exit as _exit
from loguru import logger
from json import loads

config: dict = loads(open('config.json', 'r').read())['server']
bucket: ConnectionBucket = ConnectionBucket()

try:
    NetServer: NetterServer = NetterServer(
        _bind_address = (
            config['bind_address'],
            config['bind_port']
        )
    )

except OSError:
    logger.error('Bind Address is already in use')
    _exit(1)

while NetServer.isRunning:
    client: ClientDevice | None = NetServer.accept()

    if client:
        logger.info(f'{client.publib_address} ({client.hostname}) just hopped onto the server')
