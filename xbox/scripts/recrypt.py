"""
Encrypt smartglass messages (type 0xD00D) with a new key

Example:
    usage: xbox_recrypt [-h] src_path src_secret dst_path dst_secret

    Re-Encrypt raw smartglass packets from a given filepath

    positional arguments:
      src_path    Path to sourcefiles
      src_secret  Source shared secret in hex-format
      dst_path    Path to destination
      dst_secret  Target shared secret in hex-format

    optional arguments:
      -h, --help  show this help message and exit
"""
import os
import sys
import argparse
from binascii import unhexlify

from construct import Int16ub

from xbox.sg.crypto import Crypto
from xbox.sg.enum import PacketType


def main():
    parser = argparse.ArgumentParser(
        description='Re-Encrypt raw smartglass packets from a given filepath'
    )
    parser.add_argument('src_path', type=str, help='Path to sourcefiles')
    parser.add_argument('src_secret', type=str, help='Source shared secret in hex-format')
    parser.add_argument('dst_path', type=str, help='Path to destination')
    parser.add_argument('dst_secret', type=str, help='Target shared secret in hex-format')
    args = parser.parse_args()

    src_secret = unhexlify(args.src_secret)
    dst_secret = unhexlify(args.dst_secret)

    src_path = args.src_path
    dst_path = args.dst_path

    if len(src_secret) != 64:
        print('Source key of invalid length supplied!')
        sys.exit(1)
    elif len(dst_secret) != 64:
        print('Destination key of invalid length supplied!')
        sys.exit(1)

    source_crypto = Crypto.from_shared_secret(src_secret)
    dest_crypto = Crypto.from_shared_secret(dst_secret)

    source_path = os.path.dirname(src_path)
    dest_path = os.path.dirname(dst_path)

    for f in os.listdir(source_path):
        src_filepath = os.path.join(source_path, f)
        with open(src_filepath, 'rb') as sfh:
            encrypted = sfh.read()
            if Int16ub.parse(encrypted[:2]) != PacketType.Message.value:
                print('Invalid magic, %s not a smartglass message, ignoring'
                      % src_filepath)
                continue

            # Slice the encrypted data manually
            header = encrypted[:26]
            payload = encrypted[26:-32]
            hash = encrypted[-32:]

            if not source_crypto.verify(encrypted[:-32], hash):
                print('Hash mismatch, ignoring')
                continue

            # Decrypt with source shared secret
            iv = source_crypto.generate_iv(header[:16])
            decrypted_payload = source_crypto.decrypt(iv, payload)

            # Encrypt with destination parameters
            new_iv = dest_crypto.generate_iv(header[:16])
            recrypted = dest_crypto.encrypt(new_iv, decrypted_payload)
            new_hash = dest_crypto.hash(header + recrypted)
            new_packet = header + recrypted + new_hash

            with open(os.path.join(dest_path, f), 'wb') as dfh:
                dfh.write(new_packet)


if __name__ == '__main__':
    main()
