import os
import pytest
import uuid
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

from binascii import unhexlify
from construct import Container

from xbox.sg import enum, packer, packet

from xbox.sg.console import Console
from xbox.sg.crypto import Crypto
from xbox.sg.manager import MediaManager, TextManager, InputManager

from xbox.auxiliary.crypto import AuxiliaryStreamCrypto

from xbox.stump.manager import StumpManager

from xbox.rest.app import app as rest_app
from xbox.rest.consolewrap import ConsoleWrap


@pytest.fixture(scope='session')
def uuid_dummy():
    return uuid.UUID('de305d54-75b4-431b-adb2-eb6b9e546014')


@pytest.fixture(scope='session')
def console_address():
    return '10.11.12.12'


@pytest.fixture(scope='session')
def console_name():
    return 'TestConsole'


@pytest.fixture(scope='session')
def console_liveid():
    return 'FD0000123456789'


@pytest.fixture(scope='session')
def console_flags():
    return enum.PrimaryDeviceFlag.AllowAnonymousUsers | enum.PrimaryDeviceFlag.AllowAuthenticatedUsers


@pytest.fixture(scope='session')
def public_key_bytes():
    return unhexlify(
        b'041815d5382df79bd792a8d8342fbc717eacef6a258f779279e5463573e06b'
        b'f84c6a88fac904870bf3a26f856e65f483195c4323eef47a048f23a031da6bd0929d'
    )


@pytest.fixture(scope='session')
def shared_secret_bytes():
    return unhexlify(
        '82bba514e6d19521114940bd65121af234c53654a8e67add7710b3725db44f77'
        '30ed8e3da7015a09fe0f08e9bef3853c0506327eb77c9951769d923d863a2f5e'
    )


@pytest.fixture(scope='session')
def crypto(shared_secret_bytes):
    return Crypto.from_shared_secret(shared_secret_bytes)


@pytest.fixture(scope='session')
def console(console_address, console_name, uuid_dummy, console_liveid, console_flags, public_key_bytes):
    c = Crypto.from_bytes(public_key_bytes)
    console = Console(
        console_address, console_name, uuid_dummy,
        console_liveid, console_flags, 0, c.foreign_pubkey
    )
    console.add_manager(StumpManager)
    console.add_manager(MediaManager)
    console.add_manager(TextManager)
    console.add_manager(InputManager)
    return console


@pytest.fixture(scope='session')
def public_key(public_key_bytes):
    c = Crypto.from_bytes(public_key_bytes)
    return c.foreign_pubkey


@pytest.fixture(scope='session')
def packets():
    # Who cares about RAM anyway?
    data = {}
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'packets')
    for f in os.listdir(data_path):
        with open(os.path.join(data_path, f), 'rb') as fh:
            data[f] = fh.read()

    return data


@pytest.fixture(scope='session')
def stump_json():
    # Who cares about RAM anyway?
    data = {}
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'stump_json')
    for f in os.listdir(data_path):
        with open(os.path.join(data_path, f), 'rt') as fh:
            data[f] = json.load(fh)

    return data


@pytest.fixture(scope='session')
def decrypted_packets(packets, crypto):
    return {k: packer.unpack(v, crypto) for k, v in packets.items()}


@pytest.fixture(scope='session')
def pcap_filepath():
    return os.path.join(os.path.dirname(__file__), 'data', 'sg_capture.pcap')


@pytest.fixture(scope='session')
def certificate_data():
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'selfsigned_cert.bin')
    with open(filepath, 'rb') as f:
        data = f.read()
    return data


@pytest.fixture(scope='session')
def json_fragments():
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'json_fragments.json')
    with open(filepath, 'rt') as f:
        data = json.load(f)
    return data['fragments']


@pytest.fixture(scope='session')
def aux_streams():
    data = {}
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'aux_streams')
    for f in os.listdir(data_path):
        with open(os.path.join(data_path, f), 'rb') as fh:
            data[f] = fh.read()

    return data


@pytest.fixture(scope='session')
def aux_crypto(decrypted_packets):
    connection_info = decrypted_packets['auxiliary_stream_connection_info'].protected_payload.connection_info
    return AuxiliaryStreamCrypto.from_connection_info(connection_info)


@pytest.fixture
def rest_client():
    app = FastAPI()
    client = TestClient(app)
    yield client


@pytest.fixture(scope='session')
def media_state():
    return packet.message.media_state(
        title_id=274278798,
        aum_id='AIVDE_s9eep9cpjhg6g!App',
        asset_id='',
        media_type=enum.MediaType.Video,
        sound_level=enum.SoundLevel.Full,
        enabled_commands=enum.MediaControlCommand.Play | enum.MediaControlCommand.Pause,
        playback_status=enum.MediaPlaybackStatus.Playing,
        rate=1.00,
        position=0,
        media_start=0,
        media_end=0,
        min_seek=0,
        max_seek=0,
        metadata=[
            Container(name='title', value='Some Movietitle'),
            Container(name='subtitle', value='')
        ]
    )


@pytest.fixture(scope='session')
def active_title():
    struct = packet.message._active_title(
        title_id=714681658,
        product_id=uuid.UUID('00000000-0000-0000-0000-000000000000'),
        sandbox_id=uuid.UUID('00000000-0000-0000-0000-000000000000'),
        aum='Xbox.Home_8wekyb3d8bbwe!Xbox.Home.Application',
        disposition=Container(
            has_focus=True,
            title_location=enum.ActiveTitleLocation.StartView
        )
    )
    return struct


@pytest.fixture(scope='session')
def active_media_title():
    struct = packet.message._active_title(
        title_id=714681658,
        product_id=uuid.UUID('00000000-0000-0000-0000-000000000000'),
        sandbox_id=uuid.UUID('00000000-0000-0000-0000-000000000000'),
        aum='AIVDE_s9eep9cpjhg6g!App',
        disposition=Container(
            has_focus=True,
            title_location=enum.ActiveTitleLocation.StartView
        )
    )
    return struct


@pytest.fixture(scope='session')
def console_status(active_title):
    return packet.message.console_status(
        live_tv_provider=0,
        major_version=10,
        minor_version=0,
        build_number=14393,
        locale='en-US',
        active_titles=[
            active_title
        ]
    )


@pytest.fixture(scope='session')
def console_status_with_media(active_media_title):
    return packet.message.console_status(
        live_tv_provider=0,
        major_version=10,
        minor_version=0,
        build_number=14393,
        locale='en-US',
        active_titles=[
            active_media_title
        ]
    )
