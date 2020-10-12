import logging
# import gevent
import asyncio
from typing import Optional

from xbox.sg.crypto import PKCS7Padding
from xbox.sg.utils.events import Event
from xbox.auxiliary import packer
from xbox.auxiliary.packet import aux_header_struct, AUX_PACKET_MAGIC
from xbox.auxiliary.crypto import AuxiliaryStreamCrypto
from xbox.sg.utils.struct import XStructObj

log = logging.getLogger(__name__)


class AuxiliaryPackerException(Exception):
    pass


class ConsoleConnection(object):
    BUFFER_SIZE = 2048

    def __init__(self, address, port, crypto):
        self.address = address
        self.port = port
        self.crypto = crypto

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

        self._recv_task: Optional[asyncio.Task] = None
        self.on_message = Event()

    def start(self):
        self._reader, self._writer = asyncio.open_connection(
            self.address, self.port
        )
        self._recv_task = asyncio.create_task(self._recv())

    def stop(self):
        self._recv_task.cancel()

    def handle(self, data):
        try:
            msg = packer.unpack(data, self.crypto)
            # Fire event
            self.on_message(msg)
        except Exception as e:
            log.exception("Exception while handling Console Aux data, error: {}".format(e))

    async def _recv(self):
        while True:
            data = await self._reader.read(4)
            header = aux_header_struct.parse(data)

            if header.magic != AUX_PACKET_MAGIC:
                raise Exception('Invalid packet magic received from console')

            payload_sz = header.payload_size + PKCS7Padding.size(
                header.payload_size, 16
            )
            remaining_payload_bytes = payload_sz

            while remaining_payload_bytes > 0:
                tmp = await self._reader.read(remaining_payload_bytes)
                remaining_payload_bytes -= len(tmp)
                data += tmp

            data += await self._reader.read(32)

            self.handle(data)

    async def send(self, msg):
        packets = packer.pack(msg, self.crypto)

        if not packets:
            raise Exception('No data')

        for packet in packets:
            self._writer.write(packet)


class LocalConnection(asyncio.Protocol):
    data_received_event = Event()
    connection_made_event = Event()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport
        self.connection_made(transport)

    def data_received(self, data: bytes) -> None:
        self.data_received(data)

    def close_connection(self) -> None:
        print('Close the client socket')
        self.transport.close()


class AuxiliaryRelayService(object):
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        connection_info: XStructObj,
        listen_port: int
    ):
        if len(connection_info.endpoints) > 1:
            raise Exception(
                'Auxiliary Stream advertises more than one endpoint!'
            )

        self._loop = loop
        self.crypto = AuxiliaryStreamCrypto.from_connection_info(
            connection_info
        )
        self.target_ip = connection_info.endpoints[0].ip
        self.target_port = connection_info.endpoints[0].port

        self.console_connection = ConsoleConnection(
            self.target_ip,
            self.target_port,
            self.crypto
        )

        self.server = self._loop.create_server(
            lambda: LocalConnection(),
            '0.0.0.0', listen_port
        )

        self.client_transport = None

    async def run(self):
        async with self.server as local_connection:
            local_connection.data_received_event += self._handle_client_data
            local_connection.connection_made_event += self.connection_made

            while True:
                # HACK / FIXME
                await asyncio.sleep(10000)

    def connection_made(self, transport):
        self.client_transport = transport
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))

        self.console_connection.on_message += self._handle_console_data
        self.console_connection.start()

    def _handle_console_data(self, data):
        # Data from console gets decrypted and forwarded to aux client
        if self.client_transport:
            self.client_transport.send(data)

    def _handle_client_data(self, data):
        # Data from aux client gets encrypted and sent to console
        self.console_connection.send(data)
