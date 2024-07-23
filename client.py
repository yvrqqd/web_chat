import asyncio
import json
import random
import logging
import sys


from common.async_input import ainput



class Client:
    """simple asynchronous TCP client"""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self._name: str
        self._ask_name()

    async def connect(self) -> None:
        if self.writer and not self.writer.is_closing():
            print('Already connected.')
            return
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        except ConnectionRefusedError:
            print(f'Connection to {self.host}:{self.port} was refused. Please check if the server is running.')
        except Exception as e:
            print(f'Connection attempt to {self.host}:{self.port} caused {e}.')
        else:
            self.listener_task = asyncio.create_task(self.message_listener())
            await self._on_join_message()
            print(f'Connected to server at {self.host}:{self.port}')
    
    async def disconnect(self) -> None:
        if self.writer is None or self.writer.is_closing():
            print('Not connected.')
            return

        print('Disconnecting...')
        await self._on_leave_message()
        self.writer.close()
        await self.writer.wait_closed()
        print('Disconnected.')


    async def _on_join_message(self) -> None:
        join_message = {
            "event": "join",
            "login": self.name
        }
        await self.send_json_message(join_message)

    async def _on_leave_message(self) -> None:
        leave_message = {
            "event": "leave",
            "login": self.name
        }
        await self.send_json_message(leave_message)

    async def send_message(self, message: str='') -> None:
        message_json = {
            "event": "message",
            "text": message,
            "login": self.name
        }
        await self.send_json_message(message_json)
    
    async def send_json_message(self, message: dict) -> None:
        if self.writer is None or self.writer.is_closing():
            print('Not connected. Use the "connect" command to connect to the server.')
            return
        try:
            message_str = json.dumps(message)
            # print(f'Sending: {message_str}')
            self.writer.write(message_str.encode())
            await self.writer.drain()
        except ConnectionError:
            print('Connection error occurred.')

    async def close(self) -> None:
        print('Closing the connection')
        if self.writer is None:
            return
        await self._on_leave_message()
        self.writer.close()
        await self.writer.wait_closed()

    async def help(self) -> None:
        help_text = """
        Available commands:
        - connect:          connect to a server
        - disconnect:       disconnect from the server
        - send <message>:   send a message to the server
        - set_name <name>:  set the client's name
        - get_name:         get the client's name
        - help:             get 'help' text
        - quit:             quit the application
        """
        print(help_text)
    
    async def message_listener(self) -> None:
        while True:
            try:
                data = await self.reader.read(1024)
                if data:
                    print(f"Received: {data.decode()}")
                else:
                    print('Connection closed by the server.')
                    break
            except asyncio.CancelledError:
                print('Listener task cancelled.')
                break
            except Exception as e:
                print(f'Error while receiving data: {e}')
                break

    async def command_listener(self) -> None:
        while True:
            await asyncio.sleep(1)
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
                case command if command.startswith('send'):            # 'send'
                    message = command[4:].strip()
                    await self.send_message(message)
                case command if command.startswith('set_name'):        # 'set_name'
                    name = ' '.join(command.split(' ')[1:])
                    self._set_name(name)
                case 'get_name':
                    print(f'Your nickname: {self.name}')
                case _:
                    print("Unknown command. Type 'help' to list available ones.")
        await self.close()
    
    def _ask_name(self) -> None:
        name = input('Please, print your nickname > ')
        if not name:
            print('Name cannot be empty.')
            self._ask_name()
            return
        self.name = name
        print(f'Name set to: {self.name}')

    def _set_name(self, name: str) -> None:
        if self.writer and not self.writer.is_closing():
            print('You cannot change name while connected to server. Disconnect first')
            return
        if not name:
            print('Name cannot be empty.')
            return
        self.name = name
        print(f'Name set to: {self.name}')

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value) -> None:
        if not value:
            raise ValueError("Name cannot be empty.")
        self._name = value



if __name__ == "__main__":
    from common.env import get_init_data

    client = Client(**get_init_data())

    try:
        asyncio.run(client.command_listener())
    except EOFError:
        print('Server stopped manually.')
