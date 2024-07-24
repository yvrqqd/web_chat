import asyncio
import json
from json import JSONDecodeError
import logging
import logging.config

from common.async_input import ainput


logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger('client')



class Client:
    """Asynchronous TCP client"""

    def __init__(self, host: str, port: int) -> None:
        self.shutdown_event = asyncio.Event()
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self._name: str
        self._ask_name()
        
    async def connect(self) -> None:
        if self.writer and not self.writer.is_closing():
            logger.info(f'Connection to {self.host}:{self.port} was refused. Already connected.')
            return
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        except ConnectionRefusedError as e:
            logger.warning(f'Connection to {self.host}:{self.port} was refused. Please check if the server is running. {e}')
        except Exception as e:
            logger.error(f'Connection attempt to {self.host}:{self.port} caused {e}.')
        else:
            logger.info(f'Connected to server at {self.host}:{self.port}')
            self.listener_task = asyncio.create_task(self.message_listener())
            await self._on_join_message()
    
    async def disconnect(self) -> None:
        if self.writer is None or self.writer.is_closing():
            logger.info('Tried to disconnect. But self.writer is None or self.writer.is_closing()')
            return

        await self._on_leave_message()
        self.writer.close()
        await self.writer.wait_closed()
        logger.info('Disconnected.')

    async def _on_join_message(self) -> None:
        join_message = {
            'event': 'join',
            'login': self.name
        }
        await self.send_json_message(join_message)

    async def _on_leave_message(self) -> None:
        leave_message = {
            'event': 'leave',
            'login': self.name
        }
        await self.send_json_message(leave_message)

    async def send_message(self, message: str='') -> None:
        message_json = {
            'event': 'message',
            'text': message,
            'login': self.name
        }
        await self.send_json_message(message_json)
    
    async def send_json_message(self, message: dict) -> None:
        if self.writer is None or self.writer.is_closing():
            logger.warning('Tried to send message while self.writer is None or self.writer.is_closing().')
            return
        try:
            message_str = json.dumps(message)
            self.writer.write(message_str.encode())
            await self.writer.drain()
        except ConnectionError:
            logger.warning(f'Connection error occurred in send_json_message. message: {message}')

    async def help(self) -> None:
        help_text = """
        Available commands:
        - connect           : connect to a server
        - disconnect        : disconnect from the server
        - send <message>    : send a message to the server
        - set_name <name>   : set the client's name
        - get_name          : get the client's name
        - help              : get 'help' text
        - quit              : quit the application
        """
        print(help_text)
    
    async def message_listener(self) -> None:
        try:
            while not self.shutdown_event.is_set():
                data = await self.reader.read(1024)
                if not data:
                    logger.warning('From message_listener: connection might be closed.')
                    break
                try:
                    message = json.loads(data)
                    event = message.get('event')
                    user = message.get('login', 'unknown')
                    match event:
                        case 'message':
                            text = message.get('text', '')
                            print(f'[{user}] > {text}')
                        case 'join':
                            print(f'User {user} has joined.')
                        case 'leave':
                            print(f'User {user} has left.')
                        case _:
                            logger.warning(f'Unknown event or message too big. [RAW] > {message}')
                except JSONDecodeError as e:
                    logger.warning(f'json.JSONDecodeError in message_listener {e}')

        except asyncio.CancelledError:
            logger.warning('Listener task cancelled.')
        except Exception as e:
            logger.warning(f'Error while receiving data: {e}')

    async def command_listener(self) -> None:
        while not self.shutdown_event.is_set():
            command = await ainput()
            match command.strip().lower():
                case 'quit':
                    await self.disconnect()
                    print('Exiting...')
                    break
                case 'connect':
                    await self.connect()
                case 'disconnect':
                    await self.disconnect()
                case 'help':
                    await self.help()
                case command if command.startswith('send'):         # 'send'
                    message = command[4:].strip()
                    await self.send_message(message)
                case command if command.startswith('set_name'):     # 'set_name'
                    name = ' '.join(command.split(' ')[1:])
                    self._set_name(name)
                case 'get_name':
                    print(f'Your nickname: {self.name}')
                case _:
                    print("Unknown command. Type 'help' to list available ones.")
        await self.close()

    async def close(self) -> None:
        logger.info('Closing the connection')
        if self.writer is None:
            return
        await self._on_leave_message()
        self.writer.close()
        await self.writer.wait_closed()

    def _ask_name(self) -> None:
        try:
            name = input('Please, print your nickname > ')
        except:
            self.shutdown_event.set()
            return
        if not name:
            logger.warning('Name cannot be empty.')
            self._ask_name()
            return
        self.name = name
        print(f'Name set to: {self.name}')

    def _set_name(self, name: str) -> None:
        if self.writer and not self.writer.is_closing():
            logger.warning('You cannot change name while connected to server. Disconnect first.')
            return
        if not name:
            logger.warning('Name cannot be empty.')
            return
        self.name = name
        print(f'Name set to: {self.name}')

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value) -> None:
        if not value:
            raise ValueError('Name cannot be empty.')
        self._name = value



if __name__ == '__main__':
    from common.env import get_init_data

    client = Client(**get_init_data())

    try:
        asyncio.run(client.command_listener())
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
