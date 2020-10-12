"""
Smartglass protocol core

**NOTE**: Should not be used directly, use :class:`.Console` !
"""

import uuid
import json
import base64
import logging

import asyncio
import socket

from typing import List, Optional, Tuple, Dict, Union

from xbox.sg import factory, packer, crypto, console
from xbox.sg.packet.message import message_structs
from xbox.sg.enum import PacketType, ConnectionResult, DisconnectReason,\
    ServiceChannel, MessageType, AckStatus, SGResultCode, ActiveTitleLocation,\
    PairedIdentityState, PublicKeyType
from xbox.sg.constants import WindowsClientInfo, AndroidClientInfo,\
    MessageTarget
from xbox.sg.manager import MediaManager, InputManager, TextManager
from xbox.sg.utils.events import Event
from xbox.sg.utils.struct import XStruct

LOGGER = logging.getLogger(__name__)

PORT = 5050
BROADCAST = '255.255.255.255'
MULTICAST = '239.255.255.250'

CHANNEL_MAP = {
    ServiceChannel.SystemInput: MessageTarget.SystemInputUUID,
    ServiceChannel.SystemInputTVRemote: MessageTarget.SystemInputTVRemoteUUID,
    ServiceChannel.SystemMedia: MessageTarget.SystemMediaUUID,
    ServiceChannel.SystemText: MessageTarget.SystemTextUUID,
    ServiceChannel.SystemBroadcast: MessageTarget.SystemBroadcastUUID
}


class ProtocolError(Exception):
    """
    Exception thrown by CoreProtocol
    """
    pass


class SmartglassProtocol(asyncio.DatagramProtocol):
    HEARTBEAT_INTERVAL = 3.0

    def __init__(
        self,
        address: Optional[str] = None,
        crypto_instance: Optional[crypto.Crypto] = None
    ):
        """
        Instantiate Smartglass Protocol handler.

        Args:
            address: Address
            crypto_instance: Crypto instance
        """
        self.address = address
        self._transport: Optional[asyncio.DatagramTransport] = None
        self.crypto = crypto_instance

        self._discovered = {}

        self.target_participant_id = None
        self.source_participant_id = None

        self._pending: Dict[str, asyncio.Future] = {}
        self._chl_mgr = ChannelManager()
        self._seq_mgr = SequenceManager()
        self._frg_mgr = FragmentManager()

        self.on_timeout = Event()
        self.on_discover = Event()
        self.on_message = Event()
        self.on_json = Event()

        self.started = False

    async def stop(self) -> None:
        """
        Dummy
        """
        pass

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.started = True
        self._transport = transport

    def error_received(self, exc: OSError):
        print('Error received:', exc.args)

    def connection_lost(self, exc: Optional[Exception]):
        print("Connection closed")
        self._transport.close()
        self.started = False

    async def send_message(
        self,
        msg,
        channel=ServiceChannel.Core,
        addr: Optional[str] = None,
        blocking: bool = True,
        timeout: int = 5,
        retries: int = 3
    ) -> Optional[XStruct]:
        """
        Send message to console.

        Packing and encryption happens here.

        Args:
            msg: Unassembled message to send
            channel: Channel to send the message on,
                           Enum member of `ServiceChannel`
            addr: IP address of target console
            blocking: If set and `msg` is `Message`-packet, wait for ack
            timeout: Seconds to wait for ack, only useful if `blocking`
                           is `True`
            retries: Max retry count.

        Returns: None

        Raises:
            ProtocolError: On failure
        """
        if msg.header.pkt_type == PacketType.Message:
            msg.header(
                sequence_number=self._seq_mgr.next_sequence_num(),
                target_participant_id=self.target_participant_id,
                source_participant_id=self.source_participant_id,
                channel_id=self._chl_mgr.get_channel_id(channel)
            )

        if self.crypto:
            data = packer.pack(msg, self.crypto)
        else:
            data = packer.pack(msg)

        if self.address:
            addr = self.address

        if not addr:
            raise ProtocolError("No address specified in send_message")
        elif not data:
            raise ProtocolError("No data")

        if msg.header.pkt_type == PacketType.Message \
                and msg.header.flags.need_ack and blocking:
            LOGGER.debug(
                "Sending %s message on ServiceChannel %s to %s",
                msg.header.flags.msg_type.name, channel.name, addr,
                extra={'_msg': msg}
            )
            seqn = msg.header.sequence_number
            tries = 0
            result = None

            while tries < retries and not result:
                if tries > 0:
                    LOGGER.warning(
                        f"Message {msg.header.flags.msg_type.name} on "
                        f"ServiceChannel {channel.name} to {addr} not ack'd "
                        f"in time, attempt #{tries + 1}",
                        extra={'_msg': msg}
                    )

                await self._send(data, (addr, PORT))
                result = await self._await_ack('ack_%i' % seqn, timeout)
                tries += 1

            if result:
                return result

            raise ProtocolError("Exceeded retries")
        elif msg.header.pkt_type == PacketType.ConnectRequest:
            LOGGER.debug(
                f"Sending ConnectRequest to {addr}", extra={'_msg': msg}
            )

        await self._send(data, (addr, PORT))

    async def _send(self, data: bytes, target: Tuple[str, int]):
        """
        Send data on the connected transport.

        If addr is not provided, the target address that was used at the time
        of instantiating the protocol is used.
        (e.g. asyncio.create_datagram_endpoint in Console-class).

        Args:
            data: Data to send
            target: Tuple of (ip_address, port)
        """
        if self._transport:
            self._transport.sendto(data, target)
        else:
            LOGGER.error('Transport not ready...')

    def datagram_received(self, data: bytes, addr: str) -> None:
        """
        Handle incoming smartglass packets

        Args:
            data: Raw packet
            addr: IP address of sender

        Returns: None
        """
        try:
            host, _ = addr

            if self.crypto:
                msg = packer.unpack(data, self.crypto)
            else:
                msg = packer.unpack(data)

            if msg.header.pkt_type == PacketType.DiscoveryResponse:
                LOGGER.debug(
                    f"Received DiscoverResponse from {host}",
                    extra={'_msg': msg}
                )
                self._discovered[host] = msg
                self.on_discover(host, msg)

            elif msg.header.pkt_type == PacketType.ConnectResponse:
                LOGGER.debug(
                    f"Received ConnectResponse from {host}",
                    extra={'_msg': msg}
                )
                if 'connect' in self._pending:
                    self._set_result('connect', msg)

            elif msg.header.pkt_type == PacketType.Message:
                channel = self._chl_mgr.get_channel(msg.header.channel_id)
                message_info = msg.header.flags.msg_type.name

                if msg.header.flags.is_fragment:
                    message_info = 'MessageFragment ({0})'.format(message_info)

                LOGGER.debug(
                    "Received %s message on ServiceChannel %s from %s",
                    message_info, channel.name, host, extra={'_msg': msg}
                )
                seq_num = msg.header.sequence_number
                self._seq_mgr.add_received(seq_num)

                if msg.header.flags.need_ack:
                    asyncio.create_task(
                        self.ack(
                            [msg.header.sequence_number],
                            [],
                            ServiceChannel.Core
                        )
                    )

                self._seq_mgr.low_watermark = seq_num

                if msg.header.flags.is_fragment:
                    sequence_begin = msg.protected_payload.sequence_begin
                    sequence_end = msg.protected_payload.sequence_end
                    fragment_payload = self._frg_mgr.reassemble_message(msg)
                    if not fragment_payload:
                        return

                    msg(protected_payload=fragment_payload)
                    LOGGER.debug("Assembled {0} (Seq {1}:{2})".format(
                        message_info, sequence_begin, sequence_end
                    ), extra={'_msg': msg})

                self._on_message(msg, channel)
            else:
                self._on_unk(msg)
        except Exception:
            LOGGER.exception("Exception in CoreProtocol datagram handler")

    @staticmethod
    def _on_unk(msg) -> None:
        LOGGER.error(f'Unhandled message: {msg}')

    async def _await_ack(
        self,
        identifier: str,
        timeout: int = 5
    ) -> Optional[XStruct]:
        """
        Wait for acknowledgement of message

        Args:
            identifier: Identifier of ack
            timeout: Timeout in seconds

        Returns:
            :obj:`.Event`: Event
        """
        fut = asyncio.Future()
        self._pending[identifier] = fut

        try:
            await asyncio.wait_for(fut, timeout)
            return fut.result()
        except asyncio.TimeoutError:
            return None

    def _set_result(
        self,
        identifier: str,
        result: Union[AckStatus, XStruct]
    ) -> None:
        """
        Called when an acknowledgement comes in, unblocks `_await_ack`

        Args:
            identifier: Identifier of ack
            result: Ack status

        Returns: None
        """
        self._pending[identifier].set_result(result)
        del self._pending[identifier]

    async def _heartbeat_task(self) -> None:
        """
        Task checking for console activity, firing `on_timeout`-event on
        timeout.

        Heartbeats are empty "ack" messages that are to be ack'd by the console

        Returns:
            None
        """
        while self.started:
            try:
                await self.ack([], [], ServiceChannel.Core, need_ack=True)
            except ProtocolError:
                self.on_timeout()
                self.connection_lost(TimeoutError())
                break
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)

    def _on_message(self, msg: XStruct, channel: ServiceChannel) -> None:
        """
        Handle msg of type `Message`.

        Args:
            msg: Message
            channel: Channel the message was received on

        Returns: None
        """
        msg_type = msg.header.flags.msg_type

        # First run our internal handlers
        if msg_type == MessageType.Ack:
            self._on_ack(msg)

        elif msg_type == MessageType.StartChannelResponse:
            self._chl_mgr.handle_channel_start_response(msg)

        elif msg_type == MessageType.Json:
            self._on_json(msg, channel)

        # Then our hooked handlers
        self.on_message(msg, channel)

    def _on_ack(self, msg: XStruct) -> None:
        """
        Process acknowledgement message.

        Args:
            msg: Message

        Returns: None
        """

        for num in msg.protected_payload.processed_list:
            identifier = 'ack_%i' % num
            self._seq_mgr.add_processed(num)
            if identifier in self._pending:
                self._set_result(identifier, AckStatus.Processed)
        for num in msg.protected_payload.rejected_list:
            identifier = 'ack_%i' % num
            self._seq_mgr.add_rejected(num)
            if identifier in self._pending:
                self._set_result(identifier, AckStatus.Rejected)

    def _on_json(self, msg: XStruct, channel: ServiceChannel) -> None:
        """
        Process json message.

        Args:
            msg: Message
            channel: Channel the message was received on

        Returns: None
        """
        text = msg.protected_payload.text

        if 'fragment_data' in text:
            text = self._frg_mgr.reassemble_json(text)
            if not text:
                # Input message is a fragment, but cannot assemble full msg yet
                return

        self.on_json(text, channel)

    async def discover(
            self,
            addr: str = None,
            tries: int = 5,
            blocking: bool = True,
            timeout: int = 5
    ) -> Dict[str, XStruct]:
        """
        Discover consoles on the network

        Args:
            addr (str): IP address
            tries (int): Discover attempts
            blocking (bool): Wait a given time for responses, otherwise
                             return immediately
            timeout (int): Timeout in seconds (only if `blocking` is `True`)

        Returns:
            list: List of discovered consoles
        """
        self._discovered = {}
        msg = factory.discovery()

        task = asyncio.create_task(self._discover(msg, addr, tries))

        # Blocking for a discovery is different than connect or regular message
        if blocking:
            try:
                await asyncio.wait_for(task, timeout)
            except asyncio.TimeoutError:

                pass

        return self.discovered

    async def _discover(
        self,
        msg,
        addr: str,
        tries: int
    ) -> None:
        for _ in range(tries):
            await self.send_message(msg, addr=BROADCAST)
            await self.send_message(msg, addr=MULTICAST)

            if addr:
                await self.send_message(msg, addr=addr)

            await asyncio.sleep(0.5)

    @property
    def discovered(self) -> Dict[str, XStruct]:
        """
        Return discovered consoles

        Returns:
            Discovered consoles
        """
        return self._discovered

    async def connect(
        self,
        userhash: str,
        xsts_token: str,
        client_uuid: uuid.UUID = uuid.uuid4(),
        request_num: int = 0,
        retries: int = 3
    ) -> PairedIdentityState:
        """
        Connect to console

        Args:
            userhash: Userhash from Xbox Live Authentication
            xsts_token: XSTS Token from Xbox Live Authentication
            client_uuid: Client UUID (default: Generate random uuid)
            request_num: Request number
            retries: Max. connect attempts

        Returns: Pairing State

        Raises:
            ProtocolError: If connection fails
        """
        if not self.crypto:
            raise ProtocolError("No crypto")

        if isinstance(userhash, type(None)):
            userhash = ''
        if isinstance(xsts_token, type(None)):
            xsts_token = ''

        iv = self.crypto.generate_iv()
        pubkey_type = self.crypto.pubkey_type
        pubkey = self.crypto.pubkey_bytes

        msg = factory.connect(
            client_uuid, pubkey_type, pubkey, iv, userhash, xsts_token,
            request_num, request_num, request_num + 1
        )

        payload_len = packer.payload_length(msg)
        if payload_len < 1024:
            messages = [msg]
        else:
            messages = _fragment_connect_request(
                self.crypto, client_uuid, pubkey_type, pubkey,
                userhash, xsts_token, request_num
            )

        tries = 0
        result = None
        while tries < retries and not result:
            for m in messages:
                await self.send_message(m)

            result = await self._await_ack('connect')

        if not result:
            raise ProtocolError("Exceeded connect retries")

        connect_result = result.protected_payload.connect_result
        if connect_result != ConnectionResult.Success:
            raise ProtocolError(
                "Connecting failed! Result: %s" % connect_result
            )

        self.target_participant_id = 0
        self.source_participant_id = result.protected_payload.participant_id

        await self.local_join()

        for channel, target_uuid in CHANNEL_MAP.items():
            await self.start_channel(channel, target_uuid)

        asyncio.create_task(self._heartbeat_task())
        return result.protected_payload.pairing_state

    async def local_join(
        self,
        client_info: Union[WindowsClientInfo, AndroidClientInfo] = WindowsClientInfo,
        **kwargs
    ) -> None:
        """
        Pair client with console.

        Args:
            client_info: Either `WindowsClientInfo` or `AndroidClientInfo`
            **kwargs:

        Returns: None
        """
        msg = factory.local_join(client_info)
        await self.send_message(msg, **kwargs)

    async def start_channel(
        self,
        channel: ServiceChannel,
        messagetarget_uuid: uuid.UUID,
        title_id: int = 0,
        activity_id: int = 0,
        **kwargs
    ) -> None:
        """
        Request opening of specific ServiceChannel

        Args:
            channel: Channel to start
            messagetarget_uuid: Message Target UUID
            title_id: Title ID, Only used for ServiceChannel.Title
            activity_id: Activity ID, unknown use-case
            **kwargs: KwArgs

        Returns: None
        """
        request_id = self._chl_mgr.get_next_request_id(channel)
        msg = factory.start_channel(
            request_id, title_id, messagetarget_uuid, activity_id
        )
        await self.send_message(msg, **kwargs)

    async def ack(
        self,
        processed: List[int],
        rejected: List[int],
        channel: ServiceChannel,
        need_ack: bool = False
    ) -> None:
        """
        Acknowledge received messages that have `need_ack` flag set.

        Args:
            processed: Processed sequence numbers
            rejected: Rejected sequence numbers
            channel: Channel to send the ack on
            need_ack: Whether we want this ack to be acknowledged by the target
                      participant.
                      Will be blocking if set.
                      Required for heartbeat messages.

        Returns: None
        """
        low_watermark = self._seq_mgr.low_watermark
        msg = factory.acknowledge(
            low_watermark, processed, rejected, need_ack=need_ack
        )
        await self.send_message(msg, channel=channel, blocking=need_ack)

    async def json(
        self,
        data: str,
        channel: ServiceChannel
    ) -> None:
        """
        Send json message

        Args:
            data: JSON dict
            channel: Channel to send the message to

        Returns: None
        """
        msg = factory.json(data)
        await self.send_message(msg, channel=channel)

    async def power_on(
        self,
        liveid: str,
        addr: Optional[str] = None,
        tries: int = 2
    ) -> None:
        """
        Power on console.

        Args:
            liveid: Live ID of console
            addr: IP address of console
            tries: PowerOn attempts

        Returns: None
        """
        msg = factory.power_on(liveid)

        for i in range(tries):
            await self.send_message(msg, addr=BROADCAST)
            await self.send_message(msg, addr=MULTICAST)
            if addr:
                await self.send_message(msg, addr=addr)

            await asyncio.sleep(0.1)

    async def power_off(
        self,
        liveid: str
    ) -> None:
        """
        Power off console

        Args:
            liveid: Live ID of console

        Returns: None
        """
        msg = factory.power_off(liveid)
        await self.send_message(msg)

    async def disconnect(
        self,
        reason: DisconnectReason = DisconnectReason.Unspecified,
        error: int = 0
    ) -> None:
        """
        Disconnect console session

        Args:
            reason: Disconnect reason
            error: Error Code

        Returns: None
        """
        msg = factory.disconnect(reason, error)
        await self.send_message(msg)

    async def game_dvr_record(
        self,
        start_delta: int,
        end_delta: int
    ) -> AckStatus:
        """
        Start Game DVR recording

        Args:
            start_delta: Start time
            end_delta: End time

        Returns: Acknowledgement status
        """
        msg = factory.game_dvr_record(start_delta, end_delta)
        return await self.send_message(msg)

    async def launch_title(
        self,
        uri: str,
        location: ActiveTitleLocation = ActiveTitleLocation.Full
    ) -> AckStatus:
        """
        Launch title via URI

        Args:
            uri: Uri string
            location: Location

        Returns: Ack status
        """
        msg = factory.title_launch(location, uri)
        return await self.send_message(msg)


class SequenceManager:
    def __init__(self):
        """
        Process received messages by sequence numbers.
        Also add processed / rejected messages to a list.
        Tracks the `Low Watermark` that's sent with
        `Acknowledgement`-Messages too.
        """
        self.processed = []
        self.rejected = []
        self.received = []

        self._low_watermark = 0
        self._sequence_num = 0

    def add_received(self, sequence_num: int) -> None:
        """
        Add received sequence number

        Args:
            sequence_num: Sequence number

        Returns: None
        """
        if sequence_num not in self.received:
            self.received.append(sequence_num)

    def add_processed(self, sequence_num: int) -> None:
        """
        Add sequence number of message that was sent to console
        and succeeded in processing.

        Args:
            sequence_num: Sequence number

        Returns: None
        """
        if sequence_num not in self.processed:
            self.processed.append(sequence_num)

    def add_rejected(self, sequence_num: int) -> None:
        """
        Add sequence number of message that was sent to console
        and was rejected by it.

        Args:
            sequence_num: Sequence number

        Returns: None
        """
        if sequence_num not in self.rejected:
            self.rejected.append(sequence_num)

    def next_sequence_num(self) -> int:
        """
        Get next sequence number to use for outbound `Message`.

        Returns: None
        """
        self._sequence_num += 1
        return self._sequence_num

    @property
    def low_watermark(self) -> int:
        """
        Get current `Low Watermark`

        Returns: Low Watermark
        """
        return self._low_watermark

    @low_watermark.setter
    def low_watermark(self, value: int) -> None:
        """
        Set `Low Watermark`

        Args:
            value: Last received sequence number from console

        Returns: None
        """
        if value > self._low_watermark:
            self._low_watermark = value


class ChannelError(Exception):
    """
    Exception thrown by :class:`ChannelManager`.
    """
    pass


class ChannelManager:
    CHANNEL_CORE = 0
    CHANNEL_ACK = 0x1000000000000000

    def __init__(self):
        """
        Keep track of established ServiceChannels
        """
        self._channel_mapping = {}
        self._requests = {}
        self._request_id = 0

    def handle_channel_start_response(self, msg: XStruct) -> ServiceChannel:
        """
        Handle message of type `StartChannelResponse`

        Args:
            msg: Start Channel Response message

        Raises:
            :class:`ChannelError`: If channel acquire failed

        Returns: Acquired ServiceChannel
        """
        # Find ServiceChannel by RequestId
        request_id = msg.protected_payload.channel_request_id
        channel = self._requests.get(request_id)

        if not channel:
            raise ChannelError("Request Id %d not found. Was the channel request saved?" % request_id)

        if msg.protected_payload.result != SGResultCode.SG_E_SUCCESS:
            raise ChannelError("Acquiring ServiceChannel %s failed" % channel.name)

        # Save Channel Id for appropriate ServiceChannel
        channel_id = msg.protected_payload.target_channel_id
        self._channel_mapping[channel] = channel_id

        self._requests.pop(request_id)
        LOGGER.debug("Acquired ServiceChannel %s -> Channel: 0x%x", channel.name, channel_id)
        return channel

    def get_next_request_id(self, channel: ServiceChannel) -> int:
        """
        Get next Channel request id for ServiceChannel

        Incremented on each call.

        Args:
            channel: Service channel

        Returns: Channel request id
        """
        # Clear old request for same ServiceChannel
        self._requests = {key: val for key, val in self._requests.items()
                          if val != channel}

        self._request_id += 1
        self._requests[self._request_id] = channel
        return self._request_id

    def get_channel(self, channel_id: int) -> ServiceChannel:
        """
        Get matching ServiceChannel enum for provided Channel ID of `Message`

        Args:
            channel_id: Channel of Message

        Returns: Service channel
        """
        # Core and Ack are fixed, don't need mapping
        if channel_id == self.CHANNEL_CORE:
            return ServiceChannel.Core
        elif channel_id == self.CHANNEL_ACK:
            return ServiceChannel.Ack

        for key, value in self._channel_mapping.items():
            if value == channel_id:
                return key
        raise ChannelError("ServiceChannel not found for channel_id: 0x%x"
                           % channel_id)

    def get_channel_id(self, channel: ServiceChannel) -> int:
        """
        Get Channel ID for use in `Message` for provided ServiceChannel

        Args:
            channel: Service channel

        Returns: Channel ID for use in `Message`
        """

        # Core and Ack are fixed, don't need mapping
        if channel == ServiceChannel.Core:
            return self.CHANNEL_CORE
        elif channel == ServiceChannel.Ack:
            return self.CHANNEL_ACK

        if channel not in self._channel_mapping:
            raise ChannelError(
                f"Channel ID not found for ServiceChannel: {channel}"
            )
        return self._channel_mapping[channel]

    def reset(self) -> None:
        """
        Erase the channels table

        Returns:
            None
        """
        self._requests = {}
        self._channel_mapping = {}
        self._request_id = 0


class FragmentError(Exception):
    """
    Exception thrown by :class:`FragmentManager`.
    """
    pass


class FragmentManager:
    """
    Assembles fragmented messages
    """
    def __init__(self):
        self.msg_queue = {}
        self.json_queue = {}

    def reassemble_message(self, msg: XStruct) -> Optional[XStruct]:
        """
        Reassemble message fragment

        Args:
            msg: Message fragment

        Returns: Reassembled / decoded payload on success,
                `None` if payload is not ready or assembly failed.
        """
        msg_type = msg.header.flags.msg_type
        payload = msg.protected_payload
        current_sequence = msg.header.sequence_number
        sequence_begin = payload.sequence_begin
        sequence_end = payload.sequence_end

        self.msg_queue[current_sequence] = payload.data

        wanted_sequences = list(range(sequence_begin, sequence_end))
        assembled = b''
        for s in wanted_sequences:
            data = self.msg_queue.get(s)
            if not data:
                return

            assembled += data

        [self.msg_queue.pop(s) for s in wanted_sequences]

        # Parse raw data with original message struct
        struct = message_structs.get(msg_type)
        if not struct:
            raise FragmentError(
                f'Failed to find message struct for fragmented {msg_type}'
            )

        return struct.parse(assembled)

    def reassemble_json(self, json_msg: dict) -> Optional[dict]:
        """
        Reassemble fragmented json message

        Args:
            json_msg: Fragmented json message

        Returns: Reassembled / Decoded json object on success,
                 `None` if datagram is not ready or assembly failed
        """
        datagram_id, datagram_size =\
            int(json_msg['datagram_id']), int(json_msg['datagram_size'])
        fragment_offset = int(json_msg['fragment_offset'])

        fragments = self.json_queue.get(datagram_id)

        if not fragments:
            # Just add initial fragment
            self.json_queue[datagram_id] = [json_msg]
            return None

        # It's a follow-up fragment
        # Check if we already received this datagram
        for entry in fragments:
            if fragment_offset == int(entry['fragment_offset']):
                return

        # Append current fragment to datagram list
        fragments.append(json_msg)

        # Check if fragment can be assembled
        # If so, assemble and pop the fragments from queue
        if sum(int(f['fragment_length']) for f in fragments) == datagram_size:
            sorted_fragments = sorted(
                fragments, key=lambda f: int(f['fragment_offset'])
            )

            output = ''.join(f['fragment_data'] for f in sorted_fragments)

            self.json_queue.pop(datagram_id)
            return self._decode(output)

        return None

    @staticmethod
    def _encode(obj: dict) -> str:
        """
        Dump a dict as json string, then encode with base64

        Args:
            obj: Dict to encode

        Returns: base64 encoded string
        """
        bytestr = json.dumps(obj, separators=(',', ':'), sort_keys=True)\
            .encode('utf-8')
        return base64.b64encode(bytestr).decode('utf-8')

    @staticmethod
    def _decode(data: str) -> dict:
        """
        Decode a base64 encoded json object

        Args:
            data: Base64 string

        Returns: Decoded json object
        """
        return json.loads(base64.b64decode(data).decode('utf-8'))


def _fragment_connect_request(
    crypto_instance: crypto.Crypto,
    client_uuid: uuid.UUID,
    pubkey_type: PublicKeyType,
    pubkey: bytes,
    userhash: str,
    auth_token: str,
    request_num: int = 0
) -> List:
    """
    Internal method to fragment ConnectRequest.

    Args:
        crypto_instance: Instance of :class:`Crypto`
        client_uuid: Client UUID
        pubkey_type Public Key Type
        pubkey: Public Key
        userhash: Xbox Live Account userhash
        auth_token: Xbox Live Account authentication token (XSTS)
        request_num: Request Number

    Returns:
        list: List of ConnectRequest fragments
    """
    messages = []

    # Calculate packet length (without authentication data)
    dummy_msg = factory.connect(
        client_uuid, pubkey_type, pubkey, b'\x00' * 16, u'', u'', 0, 0, 0
    )
    dummy_payload_len = packer.payload_length(dummy_msg)

    # Do fragmenting
    total_auth_len = len(userhash + auth_token)
    max_size = 1024 - dummy_payload_len

    fragments = total_auth_len // max_size
    overlap = total_auth_len % max_size

    if overlap > 0:
        fragments += 1

    group_start = request_num
    group_end = group_start + fragments

    if fragments <= 1:
        raise FragmentError('Authentication data too small to fragment')

    auth_position = 0
    for fragment_num in range(fragments):
        available = max_size
        current_hash = u''

        if fragment_num == 0:
            current_hash = userhash
            available -= len(current_hash)

        current_auth = auth_token[auth_position: auth_position + available]
        auth_position += len(current_auth)

        iv = crypto_instance.generate_iv()
        messages.append(
            factory.connect(
                client_uuid, pubkey_type, pubkey, iv,
                current_hash, current_auth, request_num + fragment_num,
                group_start, group_end)
        )

    return messages
