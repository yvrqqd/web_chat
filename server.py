
import asyncio
import json
import logging
import logging.config
from typing import Tuple

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger('server')



class Server:
    """Asynchronous TCP server"""

    def __init__(self, host:str, port: int) -> None:
        self.host = host
        self.port = port
        self.clients = {}

    async def start(self) -> None:
        try:
            self.server = await asyncio.start_server(self.__connection_handler, self.host, self.port)
        except OSError as e:
            logger.error(f'Error while attempting to bind on address {self.host}:{self.port}')
            return

        addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
        logger.info(f'Serving on {addrs}')

        # self.shutdown_event = asyncio.Event()

        async with self.server:
            await self.server.serve_forever()

    # async def stop(self, event: str='explicit call') -> None:
    #     logging.info(f'Server has been shut down by {event}')
    #     self.shutdown_event.set()

    async def broadcast(self, message: any, sender_addr: Tuple) -> None:
        logger.info(f'Broadcasted message from {sender_addr}')
        for addr, client in self.clients.items():
            if client.get('status') != 'connected' or addr == sender_addr:
                continue
            try:
                writer = client.get('props',[None, None])[-1]
                if writer is None:
                    continue
                writer.write(message)
                await writer.drain()
            except ConnectionError:
                logger.warning(f'ConnectionError {addr} - {client}')
                self.clients[addr]['status'] = 'disconnected'

    async def __connection_handler(self, reader, writer) -> None:
        addr = writer.get_extra_info("peername")
        self.clients[addr] = {'props': (reader, writer), 'login': '','status': 'connected'}
        logger.info(f'Connected by {addr}')

        try:
            while True:
                data = await reader.read(1024)
                print(f'>{data}')
                if not data:
                    break
                message = json.loads(data)
                logger.info(f'Received {message} from {addr}')
                await self.broadcast(data, addr)

                if message.get('event','') == 'leave':
                    logger.info(f'Leave message was sent by {addr}')
                    self.clients[addr]['status'] = 'disconnected'
                    break
        except ConnectionError:
            logger.warning(f'ConnectionError while receiving from {addr}')
        finally:
            logger.info(f'{addr} disconnected')
            self.clients[addr]['status'] = 'disconnected'
            writer.close()
            await writer.wait_closed()



if __name__ == '__main__':
    from common.env import get_init_data

    server = Server(**get_init_data())
    logger.info(f'Server initialised')

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
