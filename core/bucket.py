from typing import Callable, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from .device import ClientDevice

class ConnectionBucket:
    connectionList: list['ClientDevice'] = []
    _registry: dict[str, list] = {}

    def get_client_by_id(self, clientID: tuple) -> 'ClientDevice | None':
        if not clientID: return None

        data = [client for client in self.connectionList if client.clientUniqueID == clientID[0]]
        return data[0] if data else None

    def command(self, name: str | list, accept_args: bool = False) -> Callable:

        def wrapper(function: Callable) -> None:
            if (isinstance(name, str)):
                self._registry[name.lower()] = [function, accept_args]

            else:
                for aliases in name:
                    self._registry[aliases.lower()] = [function, accept_args]

        return wrapper

    def handle_command(self, command: str) -> None:
        function: list | None = self._registry.get((splited := command.split())[0], None)
        commandArgs: list | None = splited if ' ' in command else None

        if not (function):
            self.on_command_not_found(command.split()[0])
            return

        if not commandArgs or not function[1]: function[0](); return
        function[0](*commandArgs[1:])

    def on_command_not_found(self, command_name: str) -> None:
        logger.error('The command "%s" is not found.' % command_name)
