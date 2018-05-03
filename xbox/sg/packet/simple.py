# flake8: noqa
"""
Construct containers for simple-message header and payloads
"""
from construct import *
from xbox.sg import enum
from xbox.sg.enum import PacketType
from xbox.sg.utils.struct import XStruct
from xbox.sg.utils.adapters import CryptoTunnel, XSwitch, XEnum, CertificateAdapter, UUIDAdapter, SGString, FieldIn


pkt_types = [
    PacketType.PowerOnRequest,
    PacketType.DiscoveryRequest, PacketType.DiscoveryResponse,
    PacketType.ConnectRequest, PacketType.ConnectResponse
]


header = XStruct(
    'pkt_type' / XEnum(Int16ub, PacketType),
    'unprotected_payload_length' / Default(Int16ub, 0),
    'protected_payload_length' / If(
        FieldIn('pkt_type', [PacketType.ConnectRequest, PacketType.ConnectResponse]),
        Default(Int16ub, 0)
    ),
    'version' / Default(Int16ub, 2)
)


power_on_request = XStruct(
    'liveid' / SGString()
)


discovery_request = XStruct(
    'flags' / Int32ub,
    'client_type' / XEnum(Int16ub, enum.ClientType),
    'minimum_version' / Int16ub,
    'maximum_version' / Int16ub
)


discovery_response = XStruct(
    'flags' / XEnum(Int32ub, enum.PrimaryDeviceFlag),
    'type' / XEnum(Int16ub, enum.ClientType),
    'name' / SGString(),
    'uuid' / UUIDAdapter('utf8'),
    'last_error' / Int32ub,
    'cert' / CertificateAdapter()
)


connect_request_unprotected = XStruct(
    'sg_uuid' / UUIDAdapter(),
    'public_key_type' / XEnum(Int16ub, enum.PublicKeyType),
    'public_key' / XSwitch(this.public_key_type, {
        enum.PublicKeyType.EC_DH_P256: Bytes(0x40),
        enum.PublicKeyType.EC_DH_P384: Bytes(0x60),
        enum.PublicKeyType.EC_DH_P521: Bytes(0x84)
    }),
    'iv' / Bytes(0x10)
)


connect_request_protected = XStruct(
    'userhash' / SGString(),
    'jwt' / SGString(),
    'connect_request_num' / Int32ub,
    'connect_request_group_start' / Int32ub,
    'connect_request_group_end' / Int32ub
)


connect_response_unprotected = XStruct(
    'iv' / Bytes(0x10)
)


connect_response_protected = XStruct(
    'connect_result' / XEnum(Int16ub, enum.ConnectionResult),
    'pairing_state' / XEnum(Int16ub, enum.PairedIdentityState),
    'participant_id' / Int32ub
)


struct = XStruct(
    'header' / header,
    'unprotected_payload' / XSwitch(
        this.header.pkt_type, {
            PacketType.PowerOnRequest: power_on_request,
            PacketType.DiscoveryRequest: discovery_request,
            PacketType.DiscoveryResponse: discovery_response,
            PacketType.ConnectRequest: connect_request_unprotected,
            PacketType.ConnectResponse: connect_response_unprotected
        }
    ),
    'protected_payload' / CryptoTunnel(
        XSwitch(
            this.header.pkt_type, {
                PacketType.ConnectRequest: connect_request_protected,
                PacketType.ConnectResponse: connect_response_protected
            },
            Pass
        )
    )
)
