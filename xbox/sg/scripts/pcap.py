"""
Parse a pcap packet capture and show decrypted
packets in a human-readable ways.

Requires the shared secret for that smartglass-session.
"""
import os
import shutil
import string
import textwrap
import argparse
from binascii import unhexlify

import dpkt

from xbox.sg import packer
from xbox.sg.crypto import Crypto
from xbox.sg.enum import PacketType

from construct.lib import containers
containers.setGlobalPrintFullStrings(True)


def packet_filter(filepath):
    with open(filepath, 'rb') as fh:
        for ts, buf in dpkt.pcap.Reader(fh):
            eth = dpkt.ethernet.Ethernet(buf)

            # Make sure the Ethernet data contains an IP packet
            if not isinstance(eth.data, dpkt.ip.IP):
                continue

            ip = eth.data
            if not isinstance(ip.data, dpkt.udp.UDP):
                continue

            udp = ip.data
            if udp.sport != 5050 and udp.dport != 5050:
                continue

            is_client = udp.dport == 5050

            yield(udp.data, is_client, ts)


def parse(pcap_filepath, crypto):
    width = shutil.get_terminal_size().columns
    col_width = width // 2 - 3
    wrapper = textwrap.TextWrapper(col_width, replace_whitespace=False)

    for packet, is_client, ts in packet_filter(pcap_filepath):
        try:
            msg = packer.unpack(packet, crypto)
        except Exception as e:
            print("Error: {}".format(e))
            continue

        msg_type = msg.header.pkt_type
        type_str = msg_type.name

        if msg_type == PacketType.Message:
            type_str = msg.header.flags.msg_type.name

        direction = '>' if is_client else '<'
        print(' {} '.format(type_str).center(width, direction))

        lines = str(msg).split('\n')
        for line in lines:
            line = wrapper.wrap(line)
            for i in line:
                if is_client:
                    print('{0: <{1}}'.format(i, col_width), '│')
                else:
                    print(' ' * col_width, '│', '{0}'.format(i, col_width))


def main():
    parser = argparse.ArgumentParser(
        description='Parse PCAP files and show SG sessions'
    )
    parser.add_argument('file', help='Path to PCAP')
    parser.add_argument('secret', help='Expanded secret for this session.')
    args = parser.parse_args()

    secret = args.secret
    if os.path.exists(secret):
        # Assume a file containing the secret
        with open(secret, 'rb') as fh:
            secret = fh.read()

        if all(chr(c) in string.hexdigits for c in secret):
            secret = unhexlify(secret)
    else:
        secret = unhexlify(secret)

    crypto = Crypto.from_shared_secret(secret)
    parse(args.file, crypto)


if __name__ == '__main__':
    main()
