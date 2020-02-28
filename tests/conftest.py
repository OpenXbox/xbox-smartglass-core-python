import os
import pytest
import uuid
import json

from binascii import unhexlify
from xbox.sg import enum, packer

from xbox.sg.console import Console
from xbox.sg.crypto import Crypto

from xbox.auxiliary.crypto import AuxiliaryStreamCrypto


@pytest.fixture(scope='session')
def crypto():
    secret = unhexlify(
        '82bba514e6d19521114940bd65121af234c53654a8e67add7710b3725db44f77'
        '30ed8e3da7015a09fe0f08e9bef3853c0506327eb77c9951769d923d863a2f5e'
    )
    return Crypto.from_shared_secret(secret)

@pytest.fixture(scope='session')
def console():
    pkey = unhexlify(
        b'041815d5382df79bd792a8d8342fbc717eacef6a258f779279e5463573e06b'
        b'f84c6a88fac904870bf3a26f856e65f483195c4323eef47a048f23a031da6bd0929d'
    )

    c = Crypto.from_bytes(pkey)
    return Console(
        '10.0.0.23', 'XboxOne', uuid.UUID('de305d54-75b4-431b-adb2-eb6b9e546014'),
        'FFFFFFFFFFF', enum.PrimaryDeviceFlag.AllowConsoleUsers, c.foreign_pubkey
    )


@pytest.fixture(scope='session')
def public_key():
    public_key = unhexlify(
        b'041815d5382df79bd792a8d8342fbc717eacef6a258f779279e5463573e06b'
        b'f84c6a88fac904870bf3a26f856e65f483195c4323eef47a048f23a031da6bd0929d'
    )

    c = Crypto.from_bytes(public_key)
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
def decrypted_packets(packets, crypto):
    return {k:packer.unpack(v, crypto) for k,v in packets.items()}

@pytest.fixture(scope='session')
def pcap_filepath():
    return os.path.join(os.path.dirname(__file__), 'data', 'sg_capture.pcap')


@pytest.fixture(scope='session')
def uuid_dummy():
    return uuid.UUID('de305d54-75b4-431b-adb2-eb6b9e546014')


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

