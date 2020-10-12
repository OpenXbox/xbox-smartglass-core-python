from typing import List

from xbox.auxiliary.crypto import AuxiliaryStreamCrypto
from xbox.sg.crypto import PKCS7Padding
from xbox.auxiliary.packet import aux_header_struct, AUX_PACKET_MAGIC


class AuxiliaryPackerException(Exception):
    pass


def pack(
    data: bytes,
    crypto: AuxiliaryStreamCrypto,
    server_data: bool = False
) -> List[bytes]:
    """
    Encrypt auxiliary data blob

    Args:
        data: Data
        crypto: Crypto context
        server_data: Whether to encrypt with `server IV`

    Returns:
        bytes: Encrypted message
    """
    # Store payload size without padding
    payload_size = len(data)

    # Pad data
    padded = PKCS7Padding.pad(data, 16)

    if not server_data:
        ciphertext = crypto.encrypt(padded)
    else:
        ciphertext = crypto.encrypt_server(padded)

    header = aux_header_struct.build(dict(
        magic=AUX_PACKET_MAGIC,
        payload_size=payload_size)
    )

    msg = header + ciphertext
    hmac = crypto.hash(msg)
    msg += hmac

    messages = list()
    while len(msg) > 1448:
        fragment, msg = msg[:1448], msg[1448:]
        messages.append(fragment)

    messages.append(msg)

    return messages


def unpack(
    data: bytes,
    crypto: AuxiliaryStreamCrypto,
    client_data: bool = False
) -> bytes:
    """
    Split and decrypt auxiliary data blob

    Args:
        data: Data blob
        crypto: Crypto context
        client_data: Whether to decrypt with 'client IV'

    Returns:
        bytes: Decrypted message
    """
    # Split header from rest of data
    header, payload, hmac = data[:4], data[4:-32], data[-32:]

    parsed = aux_header_struct.parse(header)

    if not crypto.verify(header + payload, hmac):
        raise AuxiliaryPackerException('Hash verification failed')

    if not client_data:
        plaintext = crypto.decrypt(payload)
    else:
        plaintext = crypto.decrypt_client(payload)

    # Cut off padding, before returning
    return plaintext[:parsed.payload_size]
