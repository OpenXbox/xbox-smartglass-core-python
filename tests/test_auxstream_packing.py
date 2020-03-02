import io

from xbox.sg.crypto import PKCS7Padding
from xbox.auxiliary import packer
from xbox.auxiliary import packet


def _read_aux_packets(data):
    with io.BytesIO(data) as stream:
        while stream.tell() < len(data):
            header_data = stream.read(4)
            header = packet.aux_header_struct.parse(header_data)

            if header.magic != packet.AUX_PACKET_MAGIC:
                raise Exception('Invalid packet magic received from console')

            padded_payload_sz = header.payload_size + PKCS7Padding.size(header.payload_size, 16)

            payload_data = stream.read(padded_payload_sz)
            hmac = stream.read(32)
            yield header_data + payload_data + hmac


def test_client_unpack(aux_streams, aux_crypto):
    data = aux_streams['fo4_client_to_console']
    for msg in _read_aux_packets(data):
        packer.unpack(msg, aux_crypto, client_data=True)


def test_server_unpack(aux_streams, aux_crypto):
    data = aux_streams['fo4_console_to_client']
    for msg in _read_aux_packets(data):
        packer.unpack(msg, aux_crypto)


def test_decryption(aux_streams, aux_crypto):
    data = aux_streams['fo4_console_to_client']
    messages = list(_read_aux_packets(data))
    # Need to unpack messages in order, starting with the first one
    # -> Gets IV from previous decryption
    packer.unpack(messages[0], aux_crypto)
    json_msg = packer.unpack(messages[1], aux_crypto)
    assert json_msg == b'{"lang":"de","version":"1.10.52.0"}\n'
