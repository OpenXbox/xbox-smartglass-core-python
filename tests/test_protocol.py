import pytest
from xbox.sg.protocol import _fragment_connect_request, FragmentError
from xbox.sg.protocol import ChannelManager, ChannelError
from xbox.sg.protocol import SequenceManager
from xbox.sg.protocol import FragmentManager


def test_fragment_connect_request(crypto):
    from uuid import UUID
    from xbox.sg.enum import PublicKeyType

    uuid = UUID('de305d54-75b4-431b-adb2-eb6b9e546014')
    pubkey = 64 * b'\xFF'
    userhash = '0123456789'
    auth_token = (898 * 'A') + (500 * 'B')

    fragments = _fragment_connect_request(crypto, uuid, PublicKeyType.EC_DH_P256,
                                          pubkey, userhash, auth_token)
    # request_num != 0
    fragments_dup = _fragment_connect_request(crypto, uuid, PublicKeyType.EC_DH_P256,
                                              pubkey, userhash, auth_token,
                                              request_num=3)

    # Total length (userhash + token) is too small for fragmentation
    with pytest.raises(FragmentError):
        _fragment_connect_request(crypto, uuid, PublicKeyType.EC_DH_P256,
                                  pubkey, userhash, 898 * 'A')

    assert len(fragments) == 2
    assert fragments[0].unprotected_payload.sg_uuid == uuid
    assert fragments[0].unprotected_payload.public_key == pubkey
    assert isinstance(fragments[0].unprotected_payload.iv, bytes) is True
    assert fragments[0].protected_payload.userhash == userhash
    assert fragments[0].protected_payload.jwt == 898 * 'A'
    assert fragments[0].protected_payload.connect_request_num == 0
    assert fragments[0].protected_payload.connect_request_group_start == 0
    assert fragments[0].protected_payload.connect_request_group_end == 2

    assert fragments[1].unprotected_payload.sg_uuid == uuid
    assert fragments[1].unprotected_payload.public_key == pubkey
    assert isinstance(fragments[1].unprotected_payload.iv, bytes) is True
    assert fragments[1].protected_payload.userhash == ''
    assert fragments[1].protected_payload.jwt == 500 * 'B'
    assert fragments[1].protected_payload.connect_request_num == 1
    assert fragments[1].protected_payload.connect_request_group_start == 0
    assert fragments[1].protected_payload.connect_request_group_end == 2

    assert fragments_dup[0].protected_payload.connect_request_num == 3
    assert fragments_dup[0].protected_payload.connect_request_group_start == 3
    assert fragments_dup[0].protected_payload.connect_request_group_end == 5

    assert fragments_dup[1].protected_payload.connect_request_num == 4
    assert fragments_dup[1].protected_payload.connect_request_group_start == 3
    assert fragments_dup[1].protected_payload.connect_request_group_end == 5


def test_sequence_manager():
    mgr = SequenceManager()

    seq_num = 0
    for i in range(5):
        seq_num = mgr.next_sequence_num()

    for i in range(1, 23):
        mgr.add_received(i)

    for i in range(1, 12):
        mgr.add_processed(i)

    for i in range(1, 7):
        mgr.add_rejected(i)

    # Trying to set already existing values
    mgr.add_received(4)
    mgr.add_processed(5)
    mgr.add_rejected(6)

    mgr.low_watermark = 89
    # Setting smaller sequence than already set
    mgr.low_watermark = 12

    assert mgr.received == list(range(1, 23))
    assert mgr.processed == list(range(1, 12))
    assert mgr.rejected == list(range(1, 7))

    assert mgr.low_watermark == 89
    assert seq_num == 5


def test_channel_manager(packets, crypto):
    from xbox.sg.enum import ServiceChannel
    from xbox.sg.packer import unpack

    start_channel_resp = unpack(packets['start_channel_response'], crypto)
    mgr = ChannelManager()

    request_id = 0
    while request_id != start_channel_resp.protected_payload.channel_request_id:
        request_id = mgr.get_next_request_id(ServiceChannel.SystemInputTVRemote)

    service_channel = mgr.handle_channel_start_response(start_channel_resp)

    assert service_channel == ServiceChannel.SystemInputTVRemote

    # Deleting channel references
    mgr.reset()

    with pytest.raises(ChannelError):
        mgr.get_channel(123)

    with pytest.raises(ChannelError):
        mgr.get_channel_id(ServiceChannel.SystemInputTVRemote)

    with pytest.raises(ChannelError):
        mgr.handle_channel_start_response(start_channel_resp)

    assert mgr.get_channel(0) == ServiceChannel.Core
    assert mgr.get_channel(0x1000000000000000) == ServiceChannel.Ack

    assert mgr.get_channel_id(ServiceChannel.Core) == 0
    assert mgr.get_channel_id(ServiceChannel.Ack) == 0x1000000000000000


def test_fragment_manager_json(json_fragments):
    expected_result = {'response': 'GetConfiguration',
                       'msgid': 'xV5X1YCB.13',
                       'params': [
                           {'device_id': '0',
                            'device_type': 'tv',
                            'buttons': {
                                'btn.back': 'Back',
                                'btn.up': 'Up',
                                'btn.red': 'Red',
                                'btn.page_down': 'Page Down',
                                'btn.ch_down': 'Channel Down',
                                'btn.func_c': 'Label C',
                                'btn.format': 'Format',
                                'btn.digit_2': '2',
                                'btn.func_a': 'Label A',
                                'btn.digit_7': '7',
                                'btn.last': 'Last',
                                'btn.input': 'Input',
                                'btn.fast_fwd': 'FFWD',
                                'btn.menu': 'Menu',
                                'btn.replay': 'Skip REV',
                                'btn.power': 'Power',
                                'btn.left': 'Left',
                                'btn.blue': 'Blue',
                                'btn.vol_down': 'Volume Down',
                                'btn.green': 'Green',
                                'btn.digit_4': '4',
                                'btn.digit_9': '9',
                                'btn.play': 'Play',
                                'btn.page_up': 'Page Up',
                                'btn.func_b': 'Label B',
                                'btn.power_off': 'Off',
                                'btn.vol_mute': 'Mute',
                                'btn.record': 'Record',
                                'btn.subtitle': 'Subtitle',
                                'btn.rewind': 'Rewind',
                                'btn.exit': 'Exit',
                                'btn.down': 'Down',
                                'btn.sap': 'Sap',
                                'btn.yellow': 'Yellow',
                                'btn.func_d': 'Label D',
                                'btn.info': 'Info',
                                'btn.digit_5': '5',
                                'btn.digit_3': '3',
                                'btn.digit_0': '0',
                                'btn.skip_fwd': 'Skip FWD',
                                'btn.delimiter': 'Delimiter',
                                'btn.right': 'Right',
                                'btn.vol_up': 'Volume Up',
                                'btn.ch_up': 'Channel Up',
                                'btn.digit_8': '8',
                                'btn.digit_6': '6',
                                'btn.guide': 'Guide',
                                'btn.stop': 'Stop',
                                'btn.select': 'Select',
                                'btn.power_on': 'On',
                                'btn.ch_enter': 'Enter',
                                'btn.digit_1': '1',
                                'btn.pause': 'Pause',
                                'btn.dvr': 'Recordings'
                            }},
                           {'device_id': '1',
                            'device_brand': 'Sky Deutschland',
                            'device_type': 'stb',
                            'buttons': {
                                'btn.back': 'Back',
                                'btn.red': 'Red',
                                'btn.up': 'Up',
                                'btn.ch_down': 'Channel Down',
                                'btn.format': 'Format',
                                'btn.digit_2': '2',
                                'btn.digit_7': '7',
                                'btn.last': 'Last',
                                'btn.fast_fwd': 'FFWD',
                                'btn.menu': 'Menu',
                                'btn.power': 'Power',
                                'btn.left': 'Left',
                                'btn.blue': 'Blue',
                                'btn.vol_down': 'Volume Down',
                                'btn.green': 'Green',
                                'btn.digit_4': '4',
                                'btn.digit_9': '9',
                                'btn.play': 'Play',
                                'btn.vol_mute': 'Mute',
                                'btn.record': 'Record',
                                'btn.rewind': 'Rewind',
                                'btn.exit': 'Exit',
                                'btn.down': 'Down',
                                'btn.yellow': 'Yellow',
                                'btn.info': 'Info',
                                'btn.digit_5': '5',
                                'btn.digit_3': '3',
                                'btn.digit_0': '0',
                                'btn.live': 'Live',
                                'btn.vol_up': 'Volume Up',
                                'btn.right': 'Right',
                                'btn.ch_up': 'Channel Up',
                                'btn.digit_8': '8',
                                'btn.digit_6': '6',
                                'btn.guide': 'Guide',
                                'btn.stop': 'Stop',
                                'btn.select': 'Select',
                                'btn.digit_1': '1',
                                'btn.pause': 'Pause',
                                'btn.dvr': 'Recordings'}
                            },
                           {'device_id': 'tuner',
                            'device_type': 'tuner',
                            'buttons': {
                                'btn.play': 'PLAY',
                                'btn.pause': 'PAUSE',
                                'btn.seek': 'SEEK'
                            }
                            }
                       ]}

    mgr = FragmentManager()

    for msg in json_fragments:
        msg1 = mgr.reassemble_json(msg)

    for msg in reversed(json_fragments):
        msg2 = mgr.reassemble_json(msg)

    # Deliver a fragment twice
    mgr.reassemble_json(json_fragments[0])
    mgr.reassemble_json(json_fragments[1])
    mgr.reassemble_json(json_fragments[2])
    mgr.reassemble_json(json_fragments[2])
    msg3 = mgr.reassemble_json(json_fragments[3])

    # Incomplete fragments
    for msg in reversed(json_fragments[:-1]):
        msg4 = mgr.reassemble_json(msg)

    with pytest.raises(KeyError):
        mgr.reassemble_json({'not': 'all', 'required': 'fields'})

    assert msg1 == expected_result
    assert msg2 == expected_result
    assert msg3 == expected_result
    assert msg4 is None


def test_fragment_manager_fragment_messages(packets, crypto):
    from xbox.sg.packer import unpack

    fragments = [
        unpack(packets['fragment_media_state_0'], crypto),
        unpack(packets['fragment_media_state_1'], crypto),
        unpack(packets['fragment_media_state_2'], crypto)
    ]

    mgr = FragmentManager()
    assert mgr.reassemble_message(fragments.pop()) is None
    assert mgr.reassemble_message(fragments.pop()) is None
    msg = mgr.reassemble_message(fragments.pop())
    assert msg is not None

    assert msg.aum_id == 'Microsoft.BlurayPlayer_8wekyb3d8bbwe!Xbox.BlurayPlayer.Application'
    assert msg.max_seek == 50460000
    assert len(msg.asset_id) == 2184
