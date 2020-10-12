import logging

from typing import Any

from xbox.sg import factory
from xbox.sg.manager import Manager
from xbox.sg.enum import ServiceChannel, MessageType
from xbox.sg.constants import MessageTarget
from xbox.sg.utils.events import Event

log = logging.getLogger(__name__)


class TitleManagerError(Exception):
    """
    Exception thrown by TitleManager
    """
    pass


class TitleManager(Manager):
    __namespace__ = 'title'

    def __init__(self, console):
        """
        Title Manager (ServiceChannel.Title)

        Args:
             console (:class:`.Console`): Console object, internally passed
                                          by `Console.add_manager`
        """
        super(TitleManager, self).__init__(console, ServiceChannel.Title)
        self._active_surface = None
        self._connection_info = None

        self.on_surface_change = Event()
        self.on_connection_info = Event()

    def _on_message(self, msg, channel):
        """
        Internal handler method to receive messages from Title Channel

        Args:
            msg (:class:`XStructObj`): Message
            channel (:class:`ServiceChannel`): Service channel
        """
        msg_type = msg.header.flags.msg_type
        payload = msg.protected_payload
        if msg_type == MessageType.AuxilaryStream:
            if payload.connection_info_flag == 0:
                log.debug('Received AuxiliaryStream HELLO')
                self._request_connection_info()
            else:
                log.debug('Received AuxiliaryStream CONNECTION INFO')
                self.connection_info = payload.connection_info

        elif msg_type == MessageType.ActiveSurfaceChange:
            self.active_surface = payload

        else:
            raise TitleManagerError(
                f'Unhandled Msg: {msg_type}, Payload: {payload}'
            )

    async def _request_connection_info(self) -> None:
        msg = factory.title_auxiliary_stream()
        return await self._send_message(msg)

    async def start_title_channel(self, title_id: int) -> Any:
        return await self.console.protocol.start_channel(
            ServiceChannel.Title,
            MessageTarget.TitleUUID,
            title_id=title_id
        )

    @property
    def active_surface(self):
        """
        Get `Active Surface`.

        Returns:
             :class:`XStructObj`: Active Surface
        """
        return self._active_surface

    @active_surface.setter
    def active_surface(self, value):
        """
        Set `Active Surface`.

        Args:
            value (:class:`XStructObj`): Active Surface payload

        Returns: None
        """
        self._active_surface = value
        self.on_surface_change(value)

    @property
    def connection_info(self):
        """
        Get current `Connection info`

        Returns:
            :class:`XStructObj`: Connection info
        """
        return self._connection_info

    @connection_info.setter
    def connection_info(self, value):
        """
        Set `Connection info` and setup `Crypto`-context

        Args:
            value (:class:`XStructObj`): Connection info

        Returns: None
        """
        self._connection_info = value
        self.on_connection_info(value)
