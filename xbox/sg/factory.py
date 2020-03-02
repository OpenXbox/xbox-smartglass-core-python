"""
Smartglass packet factory
"""
from construct import Container
from xbox.sg.enum import PacketType, MessageType, ClientType
from xbox.sg.packet import simple, message

CHANNEL_CORE = 0


def _message_header(msg_type, channel_id=0, target_participant_id=0,
                    source_participant_id=0, is_fragment=False,
                    need_ack=False):
    """
    Helper method for creating a message header.

    Args:
        msg_type (int): The message type.
        channel_id (int): The target channel of the message.
        target_participant_id (int): The target participant Id.
        source_participant_id (int): The source participant Id.
        is_fragment (bool): Whether the message is a fragment.
        need_ack (bool): Whether the message needs an acknowledge.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.header(
        sequence_number=0,
        target_participant_id=target_participant_id,
        source_participant_id=source_participant_id,
        flags=Container(
            need_ack=need_ack,
            is_fragment=is_fragment,
            msg_type=msg_type
        ),
        channel_id=channel_id,
        pkt_type=PacketType.Message
    )


def power_on(liveid):
    """
    Assemble PowerOn Request message.

    Args:
        liveid (str): The console LiveId (extracted from the
                      :class:`DiscoveryResponse` Certificate).

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return simple.struct(
        header=simple.header(pkt_type=PacketType.PowerOnRequest, version=0),
        unprotected_payload=simple.power_on_request(liveid=liveid)
    )


def discovery(client_type=ClientType.Android):
    """
    Assemble DiscoveryRequest SimpleMessage.

    Args:
        client_type (:class:`ClientType`): Member of :class:`ClientType`, defaults to
                           `ClientType.Android`.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return simple.struct(
        header=simple.header(pkt_type=PacketType.DiscoveryRequest, version=0),
        unprotected_payload=simple.discovery_request(
            flags=0, client_type=client_type,
            minimum_version=0, maximum_version=2
        )
    )


def connect(sg_uuid, public_key_type, public_key, iv, userhash, jwt,
            msg_num, num_start, num_end):
    """
    Assemble ConnectRequest SimpleMessage.

    Args:
        sg_uuid (UUID): Client Uuid, randomly generated.
        public_key_type (:class:`PublicKeyType`): Public Key Type.
        public_key (bytes): Calculated Public Key, from :class:`Crypto`.
        iv (bytes): Initialization Vector for this encrypted message.
        userhash (str): Xbox Live Account userhash.
        jwt (str): Xbox Live Account JWT / Auth-token.
        msg_num (int): Current message number (important for fragmentation).
        num_start (int): Base number start of ConnectRequest fragments.
        num_end (int): Base number end of ConnectRequest fragments
                       (base number start + total fragments + 1).

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return simple.struct(
        header=simple.header(pkt_type=PacketType.ConnectRequest),
        unprotected_payload=simple.connect_request_unprotected(
            sg_uuid=sg_uuid, public_key_type=public_key_type,
            public_key=public_key, iv=iv
        ),
        protected_payload=simple.connect_request_protected(
            userhash=userhash, jwt=jwt, connect_request_num=msg_num,
            connect_request_group_start=num_start,
            connect_request_group_end=num_end
        )
    )


def message_fragment(msg_type, sequence_begin, sequence_end, data, **kwargs):
    """
    Assemble fragmented message.

    Args:
        msg_type (int): Base Message Type.
        sequence_begin (int): Sequence number with first fragment.
        sequence_end (int): Last sequence number (+1) containing fragment.
        data (bytes): Plaintext MessagePacket payload fragment.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            msg_type, is_fragment=True, **kwargs
        ),
        protected_payload=message.fragment(
            sequence_begin=sequence_begin,
            sequence_end=sequence_end,
            data=data
        )
    )


def acknowledge(low_watermark, processed_list, rejected_list, **kwargs):
    """
    Assemble acknowledgement message.

    Args:
        low_watermark (int): Low Watermark.
        processed_list (list): List of processed message sequence numbers.
        rejected_list (list): List of rejected message sequence numbers.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.Ack, **kwargs
        ),
        protected_payload=message.acknowledge(
            low_watermark=low_watermark,
            processed_list=processed_list,
            rejected_list=rejected_list
        )
    )


def json(text, **kwargs):
    """
    Assemble JSON message.

    Args:
        text (str): Text string.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.Json,
            need_ack=True, **kwargs
        ),
        protected_payload=message.json(
            text=text
        )
    )


def disconnect(reason, error_code, **kwargs):
    """
    Assemble Disconnect message.

    Args:
        reason (:class:`xbox.sg.enum.DisconnectReason`): Disconnect reason.
        error_code (int): Error code.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.Disconnect, CHANNEL_CORE, **kwargs
        ),
        protected_payload=message.disconnect(
            reason=reason,
            error_code=error_code
        )
    )


def power_off(liveid, **kwargs):
    """
    Assemble PowerOff message.

    Args:
        liveid (str): Live ID of console.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.PowerOff, CHANNEL_CORE, **kwargs
        ),
        protected_payload=message.power_off(
            liveid=liveid
        )
    )


def local_join(client_info, **kwargs):
    """
    Assemble LocalJoin message.

    Args:
        client_info (object): Instance of :class:`WindowsClientInfo`
                              or :class:`AndroidClientInfo`.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.LocalJoin, CHANNEL_CORE, need_ack=True, **kwargs
        ),
        protected_payload=message.local_join(
            device_type=client_info.DeviceType,
            native_width=client_info.NativeWidth,
            native_height=client_info.NativeHeight,
            dpi_x=client_info.DpiX, dpi_y=client_info.DpiY,
            device_capabilities=client_info.DeviceCapabilities,
            client_version=client_info.ClientVersion,
            os_major_version=client_info.OSMajor,
            os_minor_version=client_info.OSMinor,
            display_name=client_info.DisplayName
        )
    )


def title_launch(location, uri, **kwargs):
    """
    Assemble TitleLaunch message.

    Args:
        location (:class:`ActiveTitleLocation`): Location.
        uri (str): Uri string for title to launch.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.TitleLaunch, CHANNEL_CORE, **kwargs
        ),
        protected_payload=message.title_launch(
            location=location,
            uri=uri
        )
    )


def start_channel(channel_request_id, title_id, service, activity_id,
                  **kwargs):
    """
    Assemble StartChannelRequest message.

    Args:
        channel_request_id (int): Incrementing Channel Request Id.
        title_id (int): Title Id, usually 0.
        service (:class:`MessageTarget`): Member of :class:`MessageTarget`.
        activity_id (int): Activity Id, usually 0.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.StartChannelRequest, CHANNEL_CORE,
            need_ack=True, **kwargs
        ),
        protected_payload=message.start_channel_request(
            channel_request_id=channel_request_id,
            title_id=title_id,
            service=service,
            activity_id=activity_id
        )
    )


def stop_channel(channel_id, **kwargs):
    """
    Assemble StopChannel message.

    Args:
        channel_id (int): Channel Id to stop.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.StopChannel, CHANNEL_CORE, **kwargs
        ),
        protected_payload=message.stop_channel(
            target_channel_id=channel_id
        )
    )


def gamepad(timestamp, buttons, l_trigger, r_trigger, l_thumb_x, l_thumb_y,
            r_thumb_x, r_thumb_y, **kwargs):
    """
    Assemble gamepad input message.

    Args:
        timestamp (longlong): Timestamp.
        buttons (:class:`GamePadButton`): Bitmask of pressed gamepad buttons.
        l_trigger (float): LT.
        r_trigger (float): RT.
        l_thumb_x (float): Position of left thumbstick, X-Axis.
        l_thumb_y (float): Position of left thumbstick, Y-Axis.
        r_thumb_x (float): Position of right thumbstick, X-Axis.
        r_thumb_y (float): Position of right thumbstick, Y-Axis.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.Gamepad, **kwargs
        ),
        protected_payload=message.gamepad(
            timestamp=timestamp, buttons=buttons,
            left_trigger=l_trigger, right_trigger=r_trigger,
            left_thumbstick_x=l_thumb_x, left_thumbstick_y=l_thumb_y,
            right_thumbstick_x=r_thumb_x, right_thumbstick_y=r_thumb_y
        )
    )


def unsnap(unknown, **kwargs):
    """
    Assemble unsnap message.

    Args:
        unknown (int): Unknown value.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.Unsnap, CHANNEL_CORE, **kwargs
        ),
        protected_payload=message.unsnap(
            unk=unknown
        )
    )


def game_dvr_record(start_time_delta, end_time_delta, **kwargs):
    """
    Assemble Game DVR record message.

    Args:
        start_time_delta (int): Start Time delta.
        end_time_delta (int): End Time delta.

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.GameDvrRecord, CHANNEL_CORE,
            need_ack=True, **kwargs
        ),
        protected_payload=message.game_dvr_record(
            start_time_delta=start_time_delta,
            end_time_delta=end_time_delta
        )
    )


def media_command(request_id, title_id, command, seek_position, **kwargs):
    """
    Assemble Media Command message.

    Args:
        request_id (int): Request Id of MediaCommand.
        title_id (int): Title Id of Application to control.
        command (:class:`MediaControlCommand`): Media Command.
        seek_position (ulonglong): Seek position.

     Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.MediaCommand,
            need_ack=True, **kwargs
        ),
        protected_payload=message.media_command(
            request_id=request_id,
            title_id=title_id,
            command=command,
            seek_position=seek_position
        )
    )


def systemtext_input(session_id, base_version, submitted_version, total_text_len,
                     selection_start, selection_length, flags, text_chunk_byte_start,
                     text_chunk, delta=None, **kwargs):
    """
    Assemble SystemText Input message

    Args:
        session_id (int): Textt session Id
        base_version (int): Base version
        submitted_version (int): Submitted Version
        total_text_len (int): Total text length
        selection_start (int): Selection start
        selection_length (int): Selection length
        flags (int): Input flags
        text_chunk_byte_start (int): Start byte of text chunk
        text_chunk (str): Actual text to send
        delta (NoneType): Unknown

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.SystemTextInput,
            need_ack=True, **kwargs
        ),
        protected_payload=message.system_text_input(
            text_session_id=session_id,
            base_version=base_version,
            submitted_version=submitted_version,
            total_text_byte_len=total_text_len,
            selection_start=selection_start,
            selection_length=selection_length,
            flags=flags,
            text_chunk_byte_start=text_chunk_byte_start,
            text_chunk=text_chunk
            # delta=delta
        )
    )


def systemtext_ack(session_id, text_version, **kwargs):
    """
    Assemble SystemText Acknowledge message

    Args:
        session_id (int): Text session Id
        text_version (int): Text version to acknowledge

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.SystemTextAck,
            need_ack=True, **kwargs
        ),
        protected_payload=message.system_text_acknowledge(
            text_session_id=session_id,
            text_version_ack=text_version
        )
    )


def systemtext_done(session_id, text_version, flags, result, **kwargs):
    """
    Assemble SystemText Done message

    Args:
        session_id (int): Text session Id
        text_version (int): Text version
        flags (int): Flags
        result (:class:`TextResult`): Text result

    Returns:
        :class:`XStructObj`: Instance of :class:`:class:`XStructObj``.
    """
    return message.struct(
        header=_message_header(
            MessageType.SystemTextDone,
            need_ack=True, **kwargs
        ),
        protected_payload=message.system_text_done(
            text_session_id=session_id,
            text_version=text_version,
            flags=flags,
            result=result
        )
    )


def title_auxiliary_stream(**kwargs):
    """
    Assemble Auxiliary Stream message

    Returns:
         :class:`XStructObj`: Instance of :class:`XStructObj`
    """
    return message.struct(
        header=_message_header(
            MessageType.AuxilaryStream,
            need_ack=True, **kwargs
        ),
        protected_payload=message.auxiliary_stream(
            connection_info_flag=0
        )
    )
