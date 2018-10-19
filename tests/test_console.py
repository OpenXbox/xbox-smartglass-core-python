from xbox.sg import console
from xbox.sg import enum
from xbox.sg import packer


def test_init(public_key, uuid_dummy):
    c = console.Console(
        '10.0.0.23', 'XboxOne', uuid_dummy, 'FFFFFFFFFFF',
        enum.PrimaryDeviceFlag.AllowConsoleUsers, 0, public_key
    )

    assert c.address == '10.0.0.23'
    assert c.flags == enum.PrimaryDeviceFlag.AllowConsoleUsers
    assert c.name == 'XboxOne'
    assert c.uuid == uuid_dummy
    assert c.liveid == 'FFFFFFFFFFF'
    assert c._public_key is not None
    assert c._crypto is not None
    assert c.device_status == enum.DeviceStatus.Unavailable
    assert c.connection_state == enum.ConnectionState.Disconnected
    assert c.pairing_state == enum.PairedIdentityState.NotPaired
    assert c.paired is False
    assert c.available is False
    assert c.connected is False

    assert c.authenticated_users_allowed is False
    assert c.anonymous_connection_allowed is False
    assert c.console_users_allowed is True
    assert c.is_certificate_pending is False


def test_init_from_message(packets, crypto, uuid_dummy):
    msg = packer.unpack(packets['discovery_response'], crypto)

    c = console.Console.from_message('10.0.0.23', msg)

    assert c.address == '10.0.0.23'
    assert c.flags == enum.PrimaryDeviceFlag.AllowAuthenticatedUsers
    assert c.name == 'XboxOne'
    assert c.uuid == uuid_dummy
    assert c.liveid == 'FFFFFFFFFFF'
    assert c._public_key is not None
    assert c._crypto is not None
    assert c.device_status == enum.DeviceStatus.Available
    assert c.connection_state == enum.ConnectionState.Disconnected
    assert c.pairing_state == enum.PairedIdentityState.NotPaired
    assert c.paired is False
    assert c.available is True
    assert c.connected is False

    assert c.authenticated_users_allowed is True
    assert c.anonymous_connection_allowed is False
    assert c.console_users_allowed is False
    assert c.is_certificate_pending is False
