"""
Smartglass protocol core

**NOTE**: Should not be used directly, use :class:`.Console` !
"""

import uuid
import json
import base64
import logging
import gevent
import gevent.event
from gevent import socket
from gevent.server import DatagramServer

from xbox.sg import factory, packer
from xbox.sg.enum import PacketType, ConnectionResult, DisconnectReason,\
    ServiceChannel, MessageType, AckStatus, SGResultCode, ActiveTitleLocation
from xbox.sg.constants import WindowsClientInfo, MessageTarget
from xbox.sg.utils.events import Event

log = logging.getLogger(__name__)

PORT = 5050
BROADCAST = '<broadcast>'
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


class CoreProtocol(DatagramServer):
    HEARTBEAT_INTERVAL = 3.0

    def __init__(self, address=None, crypto=None):
        """
        Instantiate Smartglass Protocol handler.

        Args:
            address (str): Optional IP address to send all packets to
            crypto (:class:`.Crypto`): Instance of crypto context
        """
        self.addr = address
        self.crypto = crypto

        self._discovered = {}

        self.target_participant_id = None
        self.source_participant_id = None

        self._pending = {}
        self._chl_mgr = ChannelManager()
        self._seq_mgr = SequenceManager()
        self._frg_mgr = FragmentManager()

        self.on_timeout = Event()
        self.on_discover = Event()
        self.on_message = Event()
        self.on_json = Event()

        super(DatagramServer, self).__init__(('*:0'))

    @classmethod
    def get_listener(cls, *args, **kwargs):
        sock = DatagramServer.get_listener(*args, **kwargs)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        return sock

    def stop(self, *args, **kwargs):
        """
        Stop protocol.

        Disconnect from console, then stop the protocol handler.

        Args:
            *args: Args
            **kwargs: KwArgs

        Returns: None
        """
        if self.started:
            self.disconnect()
            super(DatagramServer, self).stop(*args, **kwargs)

    def send_message(self, msg, channel=ServiceChannel.Core, addr=None,
                     blocking=True, timeout=5, retries=3):
        """
        Send message to console.

        Packing and encryption happens here.

        Args:
            msg (:obj:`XStruct`): Unassembled message to send
            channel (:class:`ServiceChannel`): Channel to send the message on,
                           Enum member of `ServiceChannel`
            addr (str): IP address of target console
            blocking (bool): If set and `msg` is `Message`-packet, wait for ack
            timeout (int): Seconds to wait for ack, only useful if `blocking`
                           is `True`
            retries (int): Max retry count.

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

        if self.addr:
            addr = self.addr

        if self.crypto:
            data = packer.pack(msg, self.crypto)
        else:
            data = packer.pack(msg)

        if not addr:
            raise ProtocolError("No address specified in send_message")

        if not data:
            raise ProtocolError("No data")

        if msg.header.pkt_type == PacketType.Message \
                and msg.header.flags.need_ack and blocking:
            log.debug(
                "Sending %s message on ServiceChannel %s to %s",
                msg.header.flags.msg_type.name, channel.name, addr,
                extra={'_msg': msg}
            )
            seqn = msg.header.sequence_number
            tries = 0
            result = None

            while tries < retries and not result:
                if tries > 0:
                    log.warning(
                        "Message %s on ServiceChannel %s to %s not ack'd in time, attempt #%d",
                        msg.header.flags.msg_type.name, channel.name, addr, tries + 1,
                        extra={'_msg': msg}
                    )

                self.socket.sendto(data, (addr, PORT))
                result = self._await_ack('ack_%i' % seqn, timeout)
                tries += 1

            if result:
                return result
            raise ProtocolError("Exceeded retries")
        elif msg.header.pkt_type == PacketType.ConnectRequest:
            log.debug("Sending ConnectRequest to %s", addr, extra={'_msg': msg})

        self.socket.sendto(data, (addr, PORT))

    def handle(self, data, addr):
        """
        Handle incoming smartglass packets

        Args:
            data (bytes): Raw packet
            addr (str): IP address of sender

        Returns: None
        """
        try:
            host, _ = addr

            if self.crypto:
                msg = packer.unpack(data, self.crypto)
            else:
                msg = packer.unpack(data)

            if msg.header.pkt_type == PacketType.DiscoveryResponse:
                log.debug("Received DiscoverResponse from %s", host, extra={'_msg': msg})
                self._discovered[host] = msg
                self.on_discover(host, msg)

            elif msg.header.pkt_type == PacketType.ConnectResponse:
                log.debug("Received ConnectResponse from %s", host, extra={'_msg': msg})
                if 'connect' in self._pending:
                    self._set_result('connect', msg)

            elif msg.header.pkt_type == PacketType.Message:
                channel = self._chl_mgr.get_channel(msg.header.channel_id)
                log.debug(
                    "Received %s message on ServiceChannel %s from %s",
                    msg.header.flags.msg_type.name, channel.name, host,
                    extra={'_msg': msg}
                )
                seq_num = msg.header.sequence_number
                self._seq_mgr.add_received(seq_num)

                if msg.header.flags.need_ack:
                    self.ack(
                        [msg.header.sequence_number], [], ServiceChannel.Core
                    )

                self._on_message(msg, channel)
                self._seq_mgr.low_watermark = seq_num
            else:
                self._on_unk(msg)
        except Exception as e:
            log.exception("Exception in CoreProtocol datagram handler")

    def _await_ack(self, identifier, timeout=5):
        """
        Wait for acknowledgement of message

        Args:
            identifier (str): Identifier of ack
            timeout (int): Timeout in seconds

        Returns:
            :obj:`.Event`: Event
        """
        evnt = gevent.event.AsyncResult()
        self._pending[identifier] = evnt

        return evnt.wait(timeout)

    def _set_result(self, identifier, result):
        """
        Called when an acknowledgement comes in, unblocks `_await_ack`

        Args:
            identifier (str): Identifier of ack
            result (int): Ack status

        Returns: None
        """
        self._pending[identifier].set(result)
        del self._pending[identifier]

    def _heartbeat(self):
        """
        Greenlet checking for console activity, firing `on_timeout`-event on timeout.

        Heartbeats are empty "ack" messages that are to be ack'd by the console.

        Returns:
            None
        """
        while self.started:
            gevent.sleep(self.HEARTBEAT_INTERVAL)
            try:
                self.ack([], [], ServiceChannel.Core, need_ack=True)
            except ProtocolError:
                self.on_timeout()
                self.stop()
                break

    def _on_message(self, msg, channel):
        """
        Handle msg of type `Message`.

        Args:
            msg (:class:`.XStruct`): Message
            channel (:class:`ServiceChannel`): Channel the message was received on

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

    def _on_ack(self, msg):
        """
        Process acknowledgement message.

        Args:
            msg (:class:`.XStruct`): Message

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

    def _on_json(self, msg, channel):
        """
        Process json message.

        Args:
            msg (:class:`.XStruct`): Message
            channel (:class:`ServiceChannel`): Channel the message was received on

        Returns: None
        """
        text = msg.protected_payload.text

        if 'fragment_data' in text:
            text = self._frg_mgr.reassemble(text)
            if not text:
                # Input message is a fragment, but cannot assemble full msg yet
                return

        self.on_json(text, channel)

    def discover(self, addr=None, tries=5, blocking=True, timeout=5):
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

        greenlet = gevent.spawn(self._discover, msg, addr, tries)

        # Blocking for a discovery is different than connect or regular message
        if blocking:
            with gevent.Timeout(timeout, False):
                greenlet.join()

        return self.discovered

    def _discover(self, msg, addr, tries):
        for _ in range(tries):
            self.send_message(msg, addr=BROADCAST)
            self.send_message(msg, addr=MULTICAST)

            if addr:
                self.send_message(msg, addr=addr)

            gevent.sleep(0.5)

    @property
    def discovered(self):
        """
        Return discovered consoles

        Returns:
            dict: Discovered consoles
        """
        return self._discovered

    def connect(self, userhash, xsts_token, client_uuid=uuid.uuid4(),
                request_num=0, retries=3):
        """
        Connect to console

        Args:
            userhash (str): Userhash from Xbox Live Authentication
            xsts_token (str): XSTS Token from Xbox Live Authentication
            client_uuid (UUID): Client UUID (default: Generate random uuid)
            request_num (int): Request number
            retries (int): Max. connect attempts

        Returns:
            int: Pairing State

        Raises:
            ProtocolError: If connection fails
        """
        if not self.crypto:
            raise ProtocolError("No crypto")

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
                self.send_message(m)

            result = self._await_ack('connect')

        if not result:
            raise ProtocolError("Exceeded connect retries")

        connect_result = result.protected_payload.connect_result
        if connect_result != ConnectionResult.Success:
            raise ProtocolError(
                "Connecting failed! Result: %s" % connect_result
            )

        self.target_participant_id = 0
        self.source_participant_id = result.protected_payload.participant_id

        self.local_join()

        for channel, target_uuid in CHANNEL_MAP.items():
            self.start_channel(channel, target_uuid)

        gevent.spawn(self._heartbeat)
        return result.protected_payload.pairing_state

    def local_join(self, client_info=WindowsClientInfo, **kwargs):
        """
        Pair client with console.

        Args:
            client_info (`ClientInfo`): Either `WindowsClientInfo` or
                                        `AndroidClientInfo`
            **kwargs:

        Returns: None
        """
        msg = factory.local_join(client_info)
        return self.send_message(msg, **kwargs)

    def start_channel(self, channel, messagetarget_uuid, title_id=0, activity_id=0, **kwargs):
        """
        Request opening of specific ServiceChannel

        Args:
            channel (:class:`ServiceChannel`): Channel to start
            messagetarget_uuid (UUID): Message Target UUID
            title_id (int): Title ID, Only used for ServiceChannel.Title
            activity_id (int): Activity ID, unknown use-case
            **kwargs: KwArgs

        Returns: None
        """
        request_id = self._chl_mgr.get_next_request_id(channel)
        msg = factory.start_channel(request_id, title_id, messagetarget_uuid, activity_id)
        return self.send_message(msg, **kwargs)

    def ack(self, processed, rejected, channel, need_ack=False):
        """
        Acknowledge received messages that have `need_ack` flag set.

        Args:
            processed (list): Processed sequence numbers
            rejected (list): Rejected sequence numbers
            channel (:class:`ServiceChannel`): Channel to send the ack on
            need_ack (bool): Whether we want this ack to be ack'd. Will be blocking if set.
                             Required for heartbeat messages.

        Returns: None
        """
        low_watermark = self._seq_mgr.low_watermark
        msg = factory.acknowledge(
            low_watermark, processed, rejected, need_ack=need_ack
        )
        self.send_message(msg, channel=channel, blocking=need_ack)

    def json(self, data, channel):
        """
        Send json message

        Args:
            data (dict): JSON dict
            channel (:class:`ServiceChannel`): Channel to send the message to

        Returns: None
        """
        msg = factory.json(data)
        self.send_message(msg, channel=channel)

    def power_on(self, liveid, addr=None, tries=2):
        """
        Power on console.

        Args:
            liveid (str): Live ID of console
            addr (str): (optional) IP address of console
            tries (int): PowerOn attempts

        Returns: None
        """
        msg = factory.power_on(liveid)

        for i in range(tries):
            self.send_message(msg, addr=BROADCAST)
            self.send_message(msg, addr=MULTICAST)
            if addr:
                self.send_message(msg, addr=addr)

            gevent.sleep(0.1)

    def power_off(self, liveid):
        """
        Power off console

        Args:
            liveid (str): Live ID of console

        Returns: None
        """
        msg = factory.power_off(liveid)
        self.send_message(msg)

    def disconnect(self, reason=DisconnectReason.Unspecified, error=0):
        """
        Disconnect console session

        Args:
            reason (:class:`DisconnectReason`): Disconnect reason
            error (int): Error Code

        Returns: None
        """
        msg = factory.disconnect(reason, error)
        self.send_message(msg)

    def game_dvr_record(self, start_delta, end_delta):
        """
        Start Game DVR recording

        Args:
            start_delta (int): Start time
            end_delta (int): End time

        Returns:
            int: Member of :class:`AckStatus`
        """
        msg = factory.game_dvr_record(start_delta, end_delta)
        return self.send_message(msg)

    def launch_title(self, uri, location=ActiveTitleLocation.Full):
        """
        Launch title via URI

        Args:
            uri (str): Uri string
            location (:class:`ActiveTitleLocation`): Location

        Returns:
            int: Member of :class:`AckStatus`
        """
        msg = factory.title_launch(location, uri)
        return self.send_message(msg)


class SequenceManager(object):
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

    def add_received(self, num):
        """
        Add received sequence number

        Args:
            num (int): Sequence number

        Returns: None
        """
        if num not in self.received:
            self.received.append(num)

    def add_processed(self, num):
        """
        Add sequence number of message that was sent to console
        and succeeded in processing.

        Args:
            num (int): Sequence number

        Returns: None
        """
        if num not in self.processed:
            self.processed.append(num)

    def add_rejected(self, num):
        """
        Add sequence number of message that was sent to console
        and was rejected by it.

        Args:
            num (int): Sequence number

        Returns: None
        """
        if num not in self.rejected:
            self.rejected.append(num)

    def next_sequence_num(self):
        """
        Get next sequence number to use for outbound `Message`.

        Returns: None
        """
        self._sequence_num += 1
        return self._sequence_num

    @property
    def low_watermark(self):
        """
        Get current `Low Watermark`

        Returns:
            int: Low Watermark
        """
        return self._low_watermark

    @low_watermark.setter
    def low_watermark(self, value):
        """
        Set `Low Watermark`

        Args:
            value (int): Last received sequence number from console

        Returns: None
        """
        if value > self._low_watermark:
            self._low_watermark = value


class ChannelError(Exception):
    """
    Exception thrown by :class:`ChannelManager`.
    """
    pass


class ChannelManager(object):
    CHANNEL_CORE = 0
    CHANNEL_ACK = 0x1000000000000000

    def __init__(self):
        """
        Keep track of established ServiceChannels
        """
        self._channel_mapping = {}
        self._requests = {}
        self._request_id = 0

    def handle_channel_start_response(self, msg):
        """
        Handle message of type `StartChannelResponse`

        Args:
            msg (:class:`XStructObj`): Start Channel Response message

        Raises:
            :class:`ChannelError`: If channel acquire failed

        Returns:
            :class:`ServiceChannel`: Acquired ServiceChannel
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
        log.debug("Acquired ServiceChannel %s -> Channel: 0x%x", channel.name, channel_id)
        return channel

    def get_next_request_id(self, channel):
        """
        Get next Channel request id for ServiceChannel

        Incremented on each call.

        Args:
            channel (:class:`ServiceChannel`): Service channel

        Returns:
            int: Channel request id
        """
        # Clear old request for same ServiceChannel
        self._requests = {key: val for key, val in self._requests.items()
                          if val != channel}

        self._request_id += 1
        self._requests[self._request_id] = channel
        return self._request_id

    def get_channel(self, channel_id):
        """
        Get matching :class:`ServiceChannel` for provided Channel ID of `Message`

        Args:
            channel_id (int): Channel of Message

        Returns:
            :class:`ServiceChannel`: Service channel
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

    def get_channel_id(self, channel):
        """
        Get Channel ID for use in `Message` for provided :class:`ServiceChannel`

        Args:
            channel (:class:`ServiceChannel`): Service channel

        Returns:
            int: Channel ID for use in `Message`
        """

        # Core and Ack are fixed, don't need mapping
        if channel == ServiceChannel.Core:
            return self.CHANNEL_CORE
        elif channel == ServiceChannel.Ack:
            return self.CHANNEL_ACK

        if channel not in self._channel_mapping:
            raise ChannelError("Channel ID not found for ServiceChannel: %s" % channel)
        return self._channel_mapping[channel]

    def reset(self):
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


class FragmentManager(object):
    """
    Assembles fragmented messages
    """
    def __init__(self):
        self.queue = {}

    def reassemble(self, json_msg):
        """
        Reassemble fragmented json message

        Args:
            json_msg (dict): Fragmented json message

        Returns:
            str: Reassembled / Decoded string on success,
                 `None` if datagram is not ready or assembly failed
        """
        datagram_id, datagram_size = int(json_msg['datagram_id']), int(json_msg['datagram_size'])
        fragment_offset = int(json_msg['fragment_offset'])

        fragments = self.queue.get(datagram_id)

        if not fragments:
            # Just add initial fragment
            self.queue[datagram_id] = [json_msg]
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

            self.queue.pop(datagram_id)
            return self._decode(output)

        return None

    def _encode(self, obj):
        """
        Dump a dict as json string, then encode with base64

        Args:
            obj (dict): Dict to encode

        Returns:
            str: base64 encoded string
        """
        bytestr = json.dumps(obj, separators=(',', ':'), sort_keys=True).encode('utf-8')
        return base64.b64encode(bytestr).decode('utf-8')

    def _decode(self, data):
        """
        Decode a base64 encoded json object

        Args:
            data (str): Base64 string

        Returns:
            dict: Decoded json object
        """
        return json.loads(base64.b64decode(data).decode('utf-8'))


def _fragment_connect_request(crypto, client_uuid, pubkey_type, pubkey,
                              userhash, auth_token, request_num=0):
    """
    Internal method to fragment ConnectRequest.

    Args:
        crypto (Crypto): Instance of :class:`Crypto`
        client_uuid (UUID): Client UUID
        pubkey_type (:obj:`.PublicKeyType`): Public Key Type
        pubkey (bytes): Public Key
        userhash (str): Xbox Live Account userhash
        auth_token (str): Xbox Live Account authentication token (XSTS)
        request_num (int): Request Number

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

        iv = crypto.generate_iv()
        messages.append(
            factory.connect(
                client_uuid, pubkey_type, pubkey, iv,
                current_hash, current_auth, request_num + fragment_num,
                group_start, group_end)
        )

    return messages
