import asyncio
import signal
import socket

import logging


class Server:
   
    def __init__(self, host:str, port: int) -> None:
        self.host = host
        self.port = port
        self.clients = {}

    async def start(self, ):
        self.server = await asyncio.start_server(self.__connection_handler, self.host, self.port)

        addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
        print(f'Serving on {addrs}')

        self.shutdown_event = asyncio.Event()

        async with self.server:
            await self.server.serve_forever()

    async def stop(self, event: str='explicit call') -> None:
        print('Server has been shut down.')
        self.shutdown_event.set()


    async def broadcast(self, message: str, sender_addr: dict) -> None:
        print(self.clients)
        for addr, client in self.clients.items():
            if client.get('status') != 'connected' or addr == sender_addr:
                continue
            try:
                writer = client.get('props',[None, None])[-1]
                if writer is None:
                    continue
                writer.write(message.encode())
                await writer.drain()
            except ConnectionError:
                print("Client suddenly closed, cannot send")
                self.clients[addr]['status'] = 'disconnected'

    async def __connection_handler(self, reader, writer) -> None:
        addr = writer.get_extra_info("peername")
        self.clients[addr] = {'props': (reader, writer), 'login': '','status': 'connected'}
        print(f"Connected by {addr}")

        try:
            while True:
                data = await reader.read(1024)
                print(f'>{data}')
                if not data:
                    print("none")
                    break
                message = data.decode()
                print(f"Received {message} from {addr}")
                await self.broadcast(f"Message from {addr}: {message}", addr)
        except ConnectionError:
            print(f"Client suddenly closed while receiving from {addr}")
        finally:
            print(f"Disconnected by {addr}")
            self.clients[addr]['status'] = 'disconnected'
            writer.close()
            await writer.wait_closed()



if __name__ == "__main__":
    from common.env import get_init_data

    server = Server(**get_init_data())

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print('Server stopped manually.')