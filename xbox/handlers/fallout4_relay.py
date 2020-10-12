"""
Fallout 4 AuxiliaryStream Relay client

Tunnels packets via TCP/27000 - compatible with regular PipBoy-clients
"""
import logging
import asyncio
from xbox.auxiliary.relay import AuxiliaryRelayService
from xbox.sg.utils.struct import XStructObj

LOGGER = logging.getLogger(__name__)

FALLOUT_TITLE_ID = 0x4ae8f9b2
LOCAL_PIPBOY_PORT = 27000


def on_connection_info(info: XStructObj):
    loop = asyncio.get_running_loop()
    print('Setting up relay on TCP/{0}...\n'.format(LOCAL_PIPBOY_PORT))
    service = AuxiliaryRelayService(loop, info, listen_port=LOCAL_PIPBOY_PORT)
    service.run()
