from core.sock import NetterServer
from core.bucket import ConnectionBucket
from core.command import CommandHandler

from threading import Thread
from sys import exit as _exit
from loguru import logger
from json import loads

config: dict = loads(open('config.json', 'r').read())['server']
bucket: ConnectionBucket = ConnectionBucket()

try:
    NetServer: NetterServer = NetterServer(
        connectionBucket = bucket,
        _bind_address = (
            config['bind_address'],
            config['bind_port']
        )
    )

except OSError:
    logger.error('Bind Address is already in use')
    _exit(1)

commandHandler: CommandHandler = CommandHandler(bucket, NetServer)
NetServer.commandHandler = commandHandler.command

# ====================================================================================================== #

Thread(target = NetServer.controller).start()

while NetServer.isRunning:
    if client := NetServer.accept():
        logger.info(f'{client.publib_address} ({client.hostname}) just hopped onto the server')
