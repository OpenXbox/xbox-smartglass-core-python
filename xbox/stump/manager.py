"""
StumpManager - Handling TV Streaming / IR control commands
"""
import random
import logging
import requests

from xbox.sg.utils.events import Event
from xbox.sg.enum import ServiceChannel
from xbox.sg.manager import Manager

from xbox.stump.enum import Message, Notification, Source, SourceHttpQuery, Quality
from xbox.stump import json_model


log = logging.getLogger(__name__)


class StumpException(Exception):
    """
    Exception thrown by StumpManager
    """
    pass


class StumpManager(Manager):
    __namespace__ = 'stump'

    def __init__(self, console):
        """
        Title Manager (ServiceChannel.SystemInputTVRemote)

        Args:
             console (:class:`.Console`): Console object, internally passed
                                          by `Console.add_manager`
        """
        super(StumpManager, self).__init__(
            console, ServiceChannel.SystemInputTVRemote
        )

        self._msg_id_idx = 0
        self._msg_id_prefix = random.randint(0, 0x7FFFFFFF)

        self._appchannel_lineups = None
        self._appchannel_data = None
        self._appchannel_program_data = None
        self._stump_config = None
        self._stump_headend_info = None
        self._stump_livetv_info = None
        self._stump_program_info = None
        self._stump_recent_channels = None
        self._stump_tuner_lineups = None

        self.on_response = Event()
        self.on_notification = Event()
        self.on_error = Event()

    @property
    def msg_id(self):
        """
        Internal method for generating message IDs.

        Returns:
            str: A new message ID.
        """
        self._msg_id_idx += 1
        return '{:08x}.{:d}'.format(self._msg_id_prefix, self._msg_id_idx)

    def generate_stream_url(self, source, xuid=None, quality=Quality.BEST):
        """
        Generate TV Streaming URL (Dvb-USB tuner, not hdmi-in)

        Args:
            source (:class:`Source`): Streaming source
            xuid (str): optional, XUID
            quality (:class:`Quality`): Streaming quality

        Returns:
             str: HTTP URL
        """
        src_map = {
            Source.HDMI: SourceHttpQuery.HDMI,
            Source.TUNER: SourceHttpQuery.TUNER
        }

        if isinstance(quality, str):
            quality = Quality(quality)
        if isinstance(source, str):
            source = Source(source)

        if not self.streaming_port:
            raise StumpException('No streaming port available to generate URL')
        elif source not in (Source.TUNER, Source.HDMI):
            raise StumpException('Invalid source parameter to generate URL')

        url = 'http://{address}:{port}/{url_src}'.format(
            address=self.console.address,
            port=self.streaming_port,
            url_src=src_map.get(source).value
        )

        params = {
            'xuid': xuid,
            'quality': quality.value
        }

        r = requests.Request(method='GET', url=url, params=params).prepare()
        return r.url

    def _on_json(self, data, channel):
        """
        Internal handler for JSON messages received by the core protocol.

        Args:
            data (dict): The JSON object that was received.
            channel (int): The channel this message was received on.

        Returns:
            None.
        """
        msg = json_model.deserialize_stump_message(data)

        if msg.msgid:
            self.console.protocol._set_result(msg.msgid, msg)

        if isinstance(msg, json_model.StumpError):
            log.debug("Error msg: {}".format(msg))
            self._on_error(msg)

        elif isinstance(msg, json_model.StumpResponse):
            log.debug("Response msg: {}".format(msg))
            self._on_response(msg.response, msg)

        elif isinstance(msg, json_model.StumpNotification):
            log.debug("Notification msg: {}".format(msg))
            self._on_notification(msg.notification, msg)

        else:
            log.warning("Unknown stump message: {}".format(data))

    def _on_response(self, message_type, data):
        """
        Internal response handler. For logging purposes.

        Args:
            message_type (str/Message): The message type.
            data (`StumpResponse`): The raw message.
        """
        if isinstance(message_type, str):
            message_type = Message(message_type)

        params = data.params

        if Message.CONFIGURATION == message_type:
            self._stump_config = params
        elif Message.HEADEND_INFO == message_type:
            self._stump_headend_info = params
        elif Message.LIVETV_INFO == message_type:
            self._stump_livetv_info = params
        elif Message.TUNER_LINEUPS == message_type:
            self._stump_tuner_lineups = params
        elif Message.RECENT_CHANNELS:
            self._stump_recent_channels = params
        elif Message.PROGRAMM_INFO:
            self._stump_program_info = params
        elif Message.APPCHANNEL_LINEUPS:
            self._appchannel_lineups = params
        elif Message.APPCHANNEL_DATA:
            self._appchannel_data = params
        elif Message.APPCHANNEL_PROGRAM_DATA:
            self._appchannel_program_data = params
        elif Message.SEND_KEY or \
                Message.ENSURE_STREAMING_STARTED or \
                Message.SET_CHANNEL:
            # Refer to returned data from request_* methods
            pass
        log.info("Received {} response".format(message_type))
        self.on_response(message_type, data)

    def _on_notification(self, notification, data):
        """
        Internal notification handler. For logging purposes.

        Args:
            notification (str/Notification): The notification type.
            data (`StumpNotification`): The raw message.
        """
        if isinstance(notification, str):
            notification = Notification(notification)

        log.info("Received {} notification: {}".format(notification, data))
        self.on_notification(notification, data)

    def _on_error(self, data):
        """
        Internal error handler.

        Args:
            data (`StumpError`): The error dictionary from the Message.

        Returns:
            None.
        """
        log.error("Error: {}".format(data))
        self.on_error(data)

    def _send_stump_message(self, name, params=None, msgid=None, timeout=3):
        """
        Internal method for sending JSON messages over the core protocol.

        Handles message IDs as well as waiting for results.

        Args:
            name (Enum): Request name
            params (dict): The message parameters to send.
            msgid (str): Message identifier
            timeout (int): Timeout in seconds

        Returns:
            dict: The received result.
        """
        if not msgid:
            msgid = self.msg_id

        msg = dict(msgid=msgid, request=name.value, params=params)
        self._send_json(msg)

        result = self.console.protocol._await_ack(msgid, timeout)
        if not result:
            raise StumpException("Message \'{}\': \'{}\' got no response!".format(msgid, name))

        return result

    def request_stump_configuration(self):
        """
        Request device configuration from console.

        The configuration holds info about configured, by Xbox controlable \
        devices (TV, AV, STB).

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(Message.CONFIGURATION)

    def request_headend_info(self):
        """
        Request available headend information from console.

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(Message.HEADEND_INFO)

    def request_live_tv_info(self):
        """
        Request LiveTV information from console.

        Holds information about currently tuned channel, streaming-port etc.

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(Message.LIVETV_INFO)

    def request_program_info(self):
        """
        Request program information.

        NOTE: Not working?!

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(Message.PROGRAMM_INFO)

    def request_tuner_lineups(self):
        """
        Request Tuner Lineups from console.

        Tuner lineups hold information about scanned / found channels.

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(Message.TUNER_LINEUPS)

    def request_app_channel_lineups(self):
        """
        Request AppChannel Lineups.

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(Message.APPCHANNEL_LINEUPS)

    def request_app_channel_data(self, provider_id, channel_id):
        """
        Request AppChannel Data.

        Args:
            provider_id (str): Provider ID.
            channel_id (str): Channel ID.

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(
            Message.APPCHANNEL_DATA,
            params={
                'providerId': provider_id,
                'channelId': channel_id,
                'id': channel_id
            }
        )

    def request_app_channel_program_data(self, provider_id, program_id):
        """
        Request AppChannel Program Data.

        Args:
            provider_id (str): Provider ID.
            program_id (str): Program Id.

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(
            Message.APPCHANNEL_PROGRAM_DATA,
            params={
                'providerId': provider_id,
                'programId': program_id
            }
        )

    def set_stump_channel_by_id(self, channel_id, lineup_id):
        """
        Switch to channel by providing channel ID and lineup ID.

        Args:
            channel_id (str): Channel ID.
            lineup_id (str): Lineup ID.

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(
            Message.SET_CHANNEL,
            params={
                'channelId': channel_id,
                'lineupInstanceId': lineup_id
            }
        )

    def set_stump_channel_by_name(self, channel_name):
        """
        Switch to channel by providing channel name.

        Args:
            channel_name (str): Channel name to switch to.

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(
            Message.SET_CHANNEL,
            params={
                'channel_name': channel_name
            }
        )

    def request_recent_channels(self, first, count):
        """
        Request a list of recently watched channels.

        Args:
            first (int): Where to start enumeration.
            count (int): Number of channels to request.

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(
            Message.RECENT_CHANNELS,
            params={
                'startindex': first,
                'count': count
            }
        )

    def send_stump_key(self, button, device_id=None, **kwargs):
        """
        Send a remote control button to configured device via \
        Xbox's IR Blaster / Kinect / whatev.

        Args:
            button (str): Button to send.
            device_id (str, int): Device ID of device to control.

        Returns:
            dict: The received result.
        """
        params = dict(button_id=button)

        if device_id:
            params['device_id'] = device_id

        if kwargs:
            params.update(**kwargs)

        return self._send_stump_message(
            Message.SEND_KEY,
            params=params
        )

    def request_ensure_stump_streaming_started(self, source):
        """
        Ensure that streaming started on desired tuner type

        Args:
            source (str): Tuner Source to check for.
                          Member of :class:`Source`

        Returns:
            dict: The received result.
        """
        return self._send_stump_message(
            Message.ENSURE_STREAMING_STARTED,
            params={
                'source': source
            }
        )

    @property
    def headend_locale(self):
        if self._stump_headend_info:
            return self._stump_headend_info.headendLocale

    @property
    def streaming_port(self):
        if self._stump_livetv_info:
            return self._stump_livetv_info.streamingPort

    @property
    def is_hdmi_mode(self):
        if self._stump_livetv_info:
            return self._stump_livetv_info.inHdmiMode

    @property
    def current_tunerchannel_type(self):
        if self._stump_livetv_info:
            return self._stump_livetv_info.tunerChannelType
