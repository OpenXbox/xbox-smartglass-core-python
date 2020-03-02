import uuid
from binascii import unhexlify

from xbox.sg import enum, constants
from xbox.sg import packer
from xbox.sg import factory


def _pack(msg, crypto):
    return packer.pack(msg, crypto)


def test_message_header():
    msg = factory._message_header(
        msg_type=enum.MessageType.Ack,
        target_participant_id=2,
        source_participant_id=3,
        need_ack=False,
        is_fragment=False,
        channel_id=0xFFFF
    )
    packed = msg.build()

    assert msg.flags.msg_type == enum.MessageType.Ack
    assert msg.sequence_number == 0
    assert msg.target_participant_id == 2
    assert msg.source_participant_id == 3
    assert msg.channel_id == 0xFFFF
    assert msg.flags.need_ack is False
    assert msg.flags.is_fragment is False

    assert len(packed) == 26
    assert packed == unhexlify(
        b'd00d00000000000000000002000000038001000000000000ffff'
    )


def test_power_on(packets, crypto):
    bin_name = 'poweron_request'
    msg = factory.power_on(liveid='FD00112233FFEE66')
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.PowerOnRequest
    assert msg.header.version == 0
    assert msg.unprotected_payload.liveid == 'FD00112233FFEE66'

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_discovery_request(packets, crypto):
    bin_name = 'discovery_request'
    msg = factory.discovery(client_type=enum.ClientType.Android)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.DiscoveryRequest
    assert msg.header.version == 0

    assert msg.unprotected_payload.flags == 0
    assert msg.unprotected_payload.client_type == enum.ClientType.Android
    assert msg.unprotected_payload.minimum_version == 0
    assert msg.unprotected_payload.maximum_version == 2

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_connect_request(packets, crypto):
    bin_name = 'connect_request'
    msg = factory.connect(
        sg_uuid=uuid.UUID('{de305d54-75b4-431b-adb2-eb6b9e546014}'),
        public_key_type=enum.PublicKeyType.EC_DH_P256,
        public_key=b'\xFF' * 64,
        iv=unhexlify('2979d25ea03d97f58f46930a288bf5d2'),
        userhash='deadbeefdeadbeefde',
        jwt='dummy_token',
        msg_num=0,
        num_start=0,
        num_end=2
    )
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.ConnectRequest

    assert str(msg.unprotected_payload.sg_uuid) == 'de305d54-75b4-431b-adb2-eb6b9e546014'
    assert msg.unprotected_payload.public_key_type == enum.PublicKeyType.EC_DH_P256
    assert msg.unprotected_payload.public_key == b'\xFF' * 64
    assert msg.unprotected_payload.iv == unhexlify(
        '2979d25ea03d97f58f46930a288bf5d2'
    )

    assert msg.protected_payload.userhash == 'deadbeefdeadbeefde'
    assert msg.protected_payload.jwt == 'dummy_token'
    assert msg.protected_payload.connect_request_num == 0
    assert msg.protected_payload.connect_request_group_start == 0
    assert msg.protected_payload.connect_request_group_end == 2

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_message_fragment(packets, crypto):
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

    msg = factory.message_fragment(
        msg_type=enum.MessageType.MediaState,
        sequence_begin=22,
        sequence_end=25,
        data=data,
        need_ack=True,
        source_participant_id=0,
        target_participant_id=31,
        channel_id=148
    )

    msg.header(sequence_number=22)

    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.MediaState

    assert msg.protected_payload.sequence_begin == 22
    assert msg.protected_payload.sequence_end == 25
    assert msg.protected_payload.data == data

    assert isinstance(packed, bytes) is True
    assert len(packed) == 1098

    assert packed == packets['fragment_media_state_0']


def test_acknowledge(packets, crypto):
    bin_name = 'acknowledge'
    msg = factory.acknowledge(
        low_watermark=0,
        processed_list=[1],
        rejected_list=[]
    )
    msg.header(
        sequence_number=1,
        target_participant_id=31,
        channel_id=1152921504606846976
    )
    msg.header.flags(version=2, need_ack=False)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.Ack

    assert msg.protected_payload.low_watermark == 0
    assert msg.protected_payload.processed_list == [1]
    assert msg.protected_payload.rejected_list == []

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_json(packets, crypto):
    bin_name = 'json'
    msg = factory.json(
        text={'request': 'GetConfiguration', 'msgid': '2ed6c0fd.2'}
    )
    msg.header(
        sequence_number=11,
        source_participant_id=31,
        channel_id=151
    )
    msg.header.flags(need_ack=True)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.Json

    assert msg.protected_payload.text == {
        'request': 'GetConfiguration', 'msgid': '2ed6c0fd.2'
    }

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_disconnect(packets, crypto):
    bin_name = 'disconnect'
    msg = factory.disconnect(
        reason=enum.DisconnectReason.Unspecified,
        error_code=0
    )
    msg.header(
        sequence_number=57,
        source_participant_id=31
    )
    msg.header.flags(need_ack=False)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.Disconnect

    assert msg.protected_payload.reason == enum.DisconnectReason.Unspecified
    assert msg.protected_payload.error_code == 0

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_power_off(packets, crypto):
    bin_name = 'power_off'
    msg = factory.power_off(liveid='FD00112233FFEE66')
    msg.header(
        sequence_number=1882,
        source_participant_id=2
    )
    msg.header.flags(need_ack=True)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.PowerOff

    assert msg.protected_payload.liveid == 'FD00112233FFEE66'

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_local_join(packets, crypto):
    class TestClientInfo(object):
        DeviceType = enum.ClientType.Android
        NativeWidth = 600
        NativeHeight = 1024
        DpiX = 160
        DpiY = 160
        DeviceCapabilities = constants.DeviceCapabilities.All
        ClientVersion = 133713371
        OSMajor = 42
        OSMinor = 0
        DisplayName = 'package.name.here'

    bin_name = 'local_join'
    msg = factory.local_join(client_info=TestClientInfo)
    msg.header(
        sequence_number=1,
        source_participant_id=31
    )
    msg.header.flags(version=0)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.LocalJoin

    assert msg.protected_payload.device_type == enum.ClientType.Android
    assert msg.protected_payload.native_width == 600
    assert msg.protected_payload.native_height == 1024
    assert msg.protected_payload.dpi_x == 160
    assert msg.protected_payload.dpi_y == 160
    assert msg.protected_payload.device_capabilities == constants.DeviceCapabilities.All
    assert msg.protected_payload.client_version == 133713371
    assert msg.protected_payload.os_major_version == 42
    assert msg.protected_payload.os_minor_version == 0
    assert msg.protected_payload.display_name == 'package.name.here'

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_title_launch(packets, crypto):
    bin_name = 'title_launch'
    msg = factory.title_launch(
        location=enum.ActiveTitleLocation.Fill,
        uri='ms-xbl-0D174C79://default/'
    )
    msg.header(
        sequence_number=685,
        source_participant_id=32
    )
    msg.header.flags(need_ack=True)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.TitleLaunch

    assert msg.protected_payload.location == enum.ActiveTitleLocation.Fill
    assert msg.protected_payload.uri == 'ms-xbl-0D174C79://default/'

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_start_channel(packets, crypto):
    bin_name = 'start_channel_request'
    msg = factory.start_channel(
        channel_request_id=1,
        title_id=0,
        service=constants.MessageTarget.SystemInputUUID,
        activity_id=0
    )
    msg.header(
        sequence_number=2,
        source_participant_id=31
    )
    msg.header.flags(need_ack=True)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.StartChannelRequest

    assert msg.protected_payload.channel_request_id == 1
    assert msg.protected_payload.title_id == 0
    assert msg.protected_payload.service == constants.MessageTarget.SystemInputUUID
    assert msg.protected_payload.activity_id == 0

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_stop_channel(packets, crypto):
    msg = factory.stop_channel(channel_id=2)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.StopChannel

    assert msg.protected_payload.target_channel_id == 2

    assert len(packed) == 74
    assert packed == unhexlify(
        b'd00d0008000000000000000000000000802800000000000000001b0783367a4426'
        b'c2e0775916685c072df0380ee320925842716d595ced4b68f8a9bad01a5301be7e'
        b'd7d3b4e25a03b728'
    )


def test_gamepad(packets, crypto):
    bin_name = 'gamepad'
    msg = factory.gamepad(
        timestamp=0,
        buttons=enum.GamePadButton.PadB,
        l_trigger=0.0,
        r_trigger=0.0,
        l_thumb_x=0.0,
        r_thumb_x=0.0,
        l_thumb_y=0.0,
        r_thumb_y=0.0
    )

    msg.header(
        sequence_number=79,
        source_participant_id=41,
        channel_id=180
    )
    msg.header.flags(need_ack=False)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.Gamepad

    assert msg.protected_payload.timestamp == 0
    assert msg.protected_payload.buttons == enum.GamePadButton.PadB
    assert msg.protected_payload.left_trigger == 0.0
    assert msg.protected_payload.right_trigger == 0.0
    assert msg.protected_payload.left_thumbstick_x == 0.0
    assert msg.protected_payload.right_thumbstick_x == 0.0
    assert msg.protected_payload.left_thumbstick_y == 0.0
    assert msg.protected_payload.right_thumbstick_y == 0.0

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_unsnap(packets, crypto):
    msg = factory.unsnap(unknown=1)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.Unsnap

    assert msg.protected_payload.unk == 1

    assert len(packed) == 74
    assert packed == unhexlify(
        b'd00d000100000000000000000000000080370000000000000000738d3b76a69a34'
        b'bbf732755035fe77672e5ea1432f3e278189d7756f62254ebe790dfe084ba43067'
        b'bf3f4b2546c1f882'
    )


def test_gamedvr_record(packets, crypto):
    bin_name = 'gamedvr_record'
    msg = factory.game_dvr_record(
        start_time_delta=-60,
        end_time_delta=0
    )
    msg.header(
        sequence_number=70,
        source_participant_id=1
    )
    msg.header.flags(need_ack=True)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.GameDvrRecord

    assert msg.protected_payload.start_time_delta == -60
    assert msg.protected_payload.end_time_delta == 0

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]


def test_media_command(packets, crypto):
    bin_name = 'media_command'
    msg = factory.media_command(
        request_id=0,
        title_id=274278798,
        command=enum.MediaControlCommand.FastForward,
        seek_position=0
    )
    msg.header(
        sequence_number=597,
        source_participant_id=32,
        channel_id=153
    )
    msg.header.flags(need_ack=True)
    packed = _pack(msg, crypto)

    assert msg.header.pkt_type == enum.PacketType.Message
    assert msg.header.flags.msg_type == enum.MessageType.MediaCommand

    assert msg.protected_payload.request_id == 0
    assert msg.protected_payload.title_id == 274278798
    assert msg.protected_payload.command == enum.MediaControlCommand.FastForward

    assert len(packed) == len(packets[bin_name])
    assert packed == packets[bin_name]
