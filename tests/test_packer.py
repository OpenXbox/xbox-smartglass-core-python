from binascii import hexlify, unhexlify

from xbox.sg import packer, enum
from xbox.sg.constants import MessageTarget


def _unpack(data, crypto):
    return packer.unpack(data, crypto)


def _pack(msg, crypto):
    return packer.pack(msg, crypto)


def test_poweron_request(packets, crypto):
    unpacked = _unpack(packets['poweron_request'], crypto)

    assert unpacked.header.pkt_type == enum.PacketType.PowerOnRequest
    assert unpacked.header.unprotected_payload_length == 19
    assert unpacked.header.version == 0

    assert unpacked.unprotected_payload.liveid == 'FD00112233FFEE66'


def test_discovery_request(packets, crypto):
    unpacked = _unpack(packets['discovery_request'], crypto)

    assert unpacked.header.pkt_type == enum.PacketType.DiscoveryRequest
    assert unpacked.header.unprotected_payload_length == 10
    assert unpacked.header.version == 0

    assert unpacked.unprotected_payload.flags == 0
    assert unpacked.unprotected_payload.client_type == enum.ClientType.Android
    assert unpacked.unprotected_payload.minimum_version == 0
    assert unpacked.unprotected_payload.maximum_version == 2


def test_discovery_response(packets, crypto, public_key):
    unpacked = _unpack(packets['discovery_response'], crypto)

    assert unpacked.header.pkt_type == enum.PacketType.DiscoveryResponse
    assert unpacked.header.unprotected_payload_length == 580
    assert unpacked.header.version == 2
    assert unpacked.unprotected_payload.name == 'XboxOne'
    assert str(unpacked.unprotected_payload.uuid) == 'DE305D54-75B4-431B-ADB2-EB6B9E546014'.lower()
    assert unpacked.unprotected_payload.last_error == 0
    assert unpacked.unprotected_payload.cert.liveid == 'FFFFFFFFFFF'
    assert unpacked.unprotected_payload.cert.pubkey.public_numbers() == public_key.public_numbers()


def test_connect_request(packets, crypto):
    unpacked = _unpack(packets['connect_request'], crypto)
    assert unpacked.header.pkt_type == enum.PacketType.ConnectRequest
    assert unpacked.header.unprotected_payload_length == 98
    assert unpacked.header.protected_payload_length == 47
    assert unpacked.header.version == 2
    assert str(unpacked.unprotected_payload.sg_uuid) == 'de305d54-75b4-431b-adb2-eb6b9e546014'
    assert unpacked.unprotected_payload.public_key == b'\xff' * 64
    assert unpacked.unprotected_payload.iv == unhexlify('2979d25ea03d97f58f46930a288bf5d2')
    assert unpacked.protected_payload.userhash == 'deadbeefdeadbeefde'
    assert unpacked.protected_payload.jwt == 'dummy_token'
    assert unpacked.protected_payload.connect_request_num == 0
    assert unpacked.protected_payload.connect_request_group_start == 0
    assert unpacked.protected_payload.connect_request_group_end == 2


def test_connect_response(packets, crypto):
    unpacked = _unpack(packets['connect_response'], crypto)

    assert unpacked.header.pkt_type == enum.PacketType.ConnectResponse
    assert unpacked.header.unprotected_payload_length == 16
    assert unpacked.header.protected_payload_length == 8
    assert unpacked.header.version == 2
    assert unpacked.unprotected_payload.iv == unhexlify('c6373202bdfd1167cf9693491d22322a')
    assert unpacked.protected_payload.connect_result == enum.ConnectionResult.Success
    assert unpacked.protected_payload.pairing_state == enum.PairedIdentityState.NotPaired
    assert unpacked.protected_payload.participant_id == 31


def test_local_join(packets, crypto):
    unpacked = _unpack(packets['local_join'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.LocalJoin
    assert payload.device_type == enum.ClientType.Android
    assert payload.native_width == 600
    assert payload.native_height == 1024
    assert payload.dpi_x == 160
    assert payload.dpi_y == 160
    assert payload.device_capabilities == enum.DeviceCapabilities.All
    assert payload.client_version == 133713371
    assert payload.os_major_version == 42
    assert payload.os_minor_version == 0
    assert payload.display_name == 'package.name.here'


def test_acknowledge(packets, crypto):
    unpacked = _unpack(packets['acknowledge'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.Ack
    assert payload.low_watermark == 0
    assert payload.processed_list == [1]
    assert payload.rejected_list == []


def test_paired_identity_state_changed(packets, crypto):
    unpacked = _unpack(packets['paired_identity_state_changed'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.PairedIdentityStateChanged
    assert payload.state == enum.PairedIdentityState.Paired


def test_fragmented_message(packets, crypto):
    data = unhexlify(
        b'6a5297cd00424d6963726f736f66742e426c75726179506c617965725f3877656b79623364386262'
        b'77652158626f782e426c75726179506c617965722e4170706c69636174696f6e0008883438303036'
        b'31303036433030364630303230303035343030363830303635303032303030343630303631303036'
        b'43303036433030323030303646303036363030323030303532303036353030363130303633303036'
        b'38303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'30303030303030303030303030303030303030303030303030303030303030303030303030303030'
        b'303030303030303030303030303030303030303030303030'
    )

    unpacked = _unpack(packets['fragment_media_state_0'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.MediaState
    assert payload.sequence_begin == 22
    assert payload.sequence_end == 25
    assert payload.data == data


def test_gamedvr_record(packets, crypto):
    unpacked = _unpack(packets['gamedvr_record'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.GameDvrRecord
    assert payload.start_time_delta == -60
    assert payload.end_time_delta == 0


def test_title_launch(packets, crypto):
    unpacked = _unpack(packets['title_launch'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.TitleLaunch
    assert payload.location == enum.ActiveTitleLocation.Fill
    assert payload.uri == 'ms-xbl-0D174C79://default/'


def test_start_channel_request(packets, crypto):
    unpacked = _unpack(packets['start_channel_request'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.StartChannelRequest
    assert payload.channel_request_id == 1
    assert payload.title_id == 0
    assert payload.service == MessageTarget.SystemInputUUID
    assert payload.activity_id == 0


def test_start_channel_request_title(packets, crypto):
    unpacked = _unpack(packets['start_channel_request_title_channel'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.StartChannelRequest
    assert payload.channel_request_id == 16
    assert payload.title_id == 1256782258
    assert payload.service == MessageTarget.TitleUUID
    assert payload.activity_id == 0


def test_start_channel_response(packets, crypto):
    unpacked = _unpack(packets['start_channel_response'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.StartChannelResponse
    assert payload.channel_request_id == 1
    assert payload.target_channel_id == 148
    assert payload.result == enum.SGResultCode.SG_E_SUCCESS


def test_console_status(packets, crypto):
    unpacked = _unpack(packets['console_status'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.ConsoleStatus
    assert payload.live_tv_provider == 0
    assert payload.major_version == 10
    assert payload.minor_version == 0
    assert payload.build_number == 14393
    assert payload.locale == 'en-US'
    assert len(payload.active_titles) == 1
    assert payload.active_titles[0].title_id == 714681658
    assert payload.active_titles[0].disposition.has_focus is True
    assert payload.active_titles[0].disposition.title_location == enum.ActiveTitleLocation.StartView
    assert str(payload.active_titles[0].product_id) == '00000000-0000-0000-0000-000000000000'
    assert str(payload.active_titles[0].sandbox_id) == '00000000-0000-0000-0000-000000000000'
    assert payload.active_titles[0].aum == 'Xbox.Home_8wekyb3d8bbwe!Xbox.Home.Application'


def test_active_surface_change(packets, crypto):
    unpacked = _unpack(packets['active_surface_change'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.ActiveSurfaceChange
    assert payload.surface_type == enum.ActiveSurfaceType.HTML
    assert payload.server_tcp_port == 0
    assert payload.server_udp_port == 0
    assert str(payload.session_id) == '00000000-0000-0000-0000-000000000000'
    assert payload.render_width == 0
    assert payload.render_height == 0
    assert hexlify(payload.master_session_key) == b'0000000000000000000000000000000000000000000000000000000000000000'


def test_auxiliary_stream_hello(packets, crypto):
    unpacked = _unpack(packets['auxiliary_stream_hello'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.AuxilaryStream
    assert payload.connection_info_flag == 0


def test_auxiliary_stream_connection_info(packets, crypto):
    unpacked = _unpack(packets['auxiliary_stream_connection_info'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.AuxilaryStream
    assert payload.connection_info_flag == 1
    assert hexlify(payload.connection_info.crypto_key) == b'14188d32cca3564a6d53f34ad8d21728'
    assert hexlify(payload.connection_info.server_iv) == b'09dcb570c9715cf01e0dfaf5ac718445'
    assert hexlify(payload.connection_info.client_iv) == b'9fa17a415b1bab5ae320cdceb5e37297'
    assert hexlify(payload.connection_info.sign_hash) == b'473f076d2fee90b27821fcad9d0ae7efdfd08f250823db95b90f90cac95784f9'
    assert len(payload.connection_info.endpoints) == 1
    assert payload.connection_info.endpoints[0].ip == '192.168.8.104'
    assert payload.connection_info.endpoints[0].port == '57344'


def test_disconnect(packets, crypto):
    unpacked = _unpack(packets['disconnect'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.Disconnect
    assert payload.reason == enum.DisconnectReason.Unspecified
    assert payload.error_code == 0


def test_poweroff(packets, crypto):
    unpacked = _unpack(packets['power_off'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.PowerOff
    assert payload.liveid == 'FD00112233FFEE66'


def test_json(packets, crypto):
    unpacked = _unpack(packets['json'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.Json
    assert payload.text == {'request': 'GetConfiguration', 'msgid': '2ed6c0fd.2'}


def test_gamepad(packets, crypto):
    unpacked = _unpack(packets['gamepad'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.Gamepad
    assert payload.timestamp == 0
    assert payload.buttons == enum.GamePadButton.PadB
    assert payload.left_trigger == 0.0
    assert payload.right_trigger == 0.0
    assert payload.left_thumbstick_x == 0.0
    assert payload.left_thumbstick_y == 0.0
    assert payload.right_thumbstick_x == 0.0
    assert payload.right_thumbstick_y == 0.0


def test_media_command(packets, crypto):
    unpacked = _unpack(packets['media_command'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.MediaCommand
    assert payload.request_id == 0
    assert payload.title_id == 274278798
    assert payload.command == enum.MediaControlCommand.FastForward
    assert payload.seek_position is None


def test_media_state(packets, crypto):
    unpacked = _unpack(packets['media_state'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.MediaState
    assert payload.title_id == 274278798
    assert payload.aum_id == 'AIVDE_s9eep9cpjhg6g!App'
    assert payload.asset_id == ''
    assert payload.media_type == enum.MediaType.NoMedia
    assert payload.sound_level == enum.SoundLevel.Full
    assert payload.enabled_commands == enum.MediaControlCommand(33758)
    assert payload.playback_status == enum.MediaPlaybackStatus.Stopped
    assert payload.rate == 0.0
    assert payload.position == 0
    assert payload.media_start == 0
    assert payload.media_end == 0
    assert payload.min_seek == 0
    assert payload.max_seek == 0
    assert len(payload.metadata) == 1
    assert payload.metadata[0].name == 'title'
    assert payload.metadata[0].value == ''


def test_text_acknowledge(packets, crypto):
    unpacked = _unpack(packets['system_text_acknowledge'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.SystemTextAck
    assert payload.text_session_id == 8
    assert payload.text_version_ack == 2


def test_text_configuration(packets, crypto):
    unpacked = _unpack(packets['system_text_configuration'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.SystemTextConfiguration
    assert payload.text_session_id == 9
    assert payload.text_buffer_version == 0
    assert payload.text_options == enum.TextOption.AcceptsReturn | enum.TextOption.MultiLine
    assert payload.input_scope == enum.TextInputScope.Unknown
    assert payload.max_text_length == 0
    assert payload.locale == 'de-DE'
    assert payload.prompt == ''


def test_system_text_done(packets, crypto):
    unpacked = _unpack(packets['system_text_done'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.SystemTextDone
    assert payload.text_session_id == 0
    assert payload.text_version == 0
    assert payload.flags == 0
    assert payload.result == enum.TextResult.Cancel


def test_system_text_input(packets, crypto):
    unpacked = _unpack(packets['system_text_input'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.SystemTextInput
    assert payload.text_session_id == 8
    assert payload.base_version == 1
    assert payload.submitted_version == 2
    assert payload.total_text_byte_len == 1
    assert payload.selection_start == -1
    assert payload.selection_length == -1
    assert payload.flags == 0
    assert payload.text_chunk_byte_start == 0
    assert payload.delta is None
    assert payload.text_chunk == 'h'


def test_system_touch(packets, crypto):
    unpacked = _unpack(packets['system_touch'], crypto)
    payload = unpacked.protected_payload

    assert unpacked.header.flags.msg_type == enum.MessageType.SystemTouch
    assert payload.touch_msg_timestamp == 182459592
    assert len(payload.touchpoints) == 1
    assert payload.touchpoints[0].touchpoint_id == 1
    assert payload.touchpoints[0].touchpoint_action == enum.TouchAction.Down
    assert payload.touchpoints[0].touchpoint_x == 244
    assert payload.touchpoints[0].touchpoint_y == 255


def test_repack_all(packets, crypto):
    for f in packets:
        unpacked = _unpack(packets[f], crypto)

        # if unpacked.header.pkt_type in simple.pkt_types:
        #     msg = simple.struct(**unpacked)
        # elif unpacked.header.pkt_type == enum.PacketType.Message and unpacked.header.flags.msg_type == enum.MessageType.Json:
        #     continue  # The key order is not preserved when parsing JSON so the parsed message will always differ
        # else:
        #     msg = message.struct(**unpacked)

        repacked = _pack(unpacked, crypto)

        assert repacked == packets[f], \
            '%s was not repacked correctly:\n(repacked)%s\n!=\n(original)%s'\
            % (f, hexlify(repacked), hexlify(packets[f]))
