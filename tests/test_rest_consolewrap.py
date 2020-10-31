import pytest

from xbox.rest.consolewrap import ConsoleWrap
from xbox.sg import enum


def test_consolewrap_init(console):
    wrap = ConsoleWrap(console)

    assert wrap.console == console
    assert 'text' in wrap.console.managers
    assert 'input' in wrap.console.managers
    assert 'stump' in wrap.console.managers
    assert 'media' in wrap.console.managers

@pytest.mark.asyncio
async def test_discover():
    discovered = await ConsoleWrap.discover(tries=1, blocking=False, timeout=1)

    assert isinstance(discovered, list)


@pytest.mark.asyncio
async def test_poweron():
    await ConsoleWrap.power_on('FD0123456789', tries=1, iterations=1)


def test_media_commands(console):
    commands = ConsoleWrap(console).media_commands

    assert isinstance(commands, dict)
    assert 'play' in commands
    for k, v in commands.items():
        assert isinstance(k, str)
        assert isinstance(v, enum.MediaControlCommand)


def test_input_keys(console):
    keys = ConsoleWrap(console).input_keys

    assert isinstance(keys, dict)
    assert 'nexus' in keys
    for k, v in keys.items():
        assert isinstance(k, str)
        assert isinstance(v, enum.GamePadButton)


def test_liveid(console):
    assert ConsoleWrap(console).liveid == console.liveid


def test_available(console):
    console._device_status = enum.DeviceStatus.Unavailable
    assert ConsoleWrap(console).available is False

    console._device_status = enum.DeviceStatus.Available
    assert ConsoleWrap(console).available is True


def test_connected(console):
    console._connection_state = enum.ConnectionState.Disconnected
    assert ConsoleWrap(console).connected is False

    console._connection_state = enum.ConnectionState.Connected
    assert ConsoleWrap(console).connected is True

    console._connection_state = enum.ConnectionState.Connecting
    assert ConsoleWrap(console).connected is False


def test_usable(console):
    console._connection_state = enum.ConnectionState.Reconnecting
    assert ConsoleWrap(console).usable is False

    console._connection_state = enum.ConnectionState.Disconnecting
    assert ConsoleWrap(console).usable is False

    console._connection_state = enum.ConnectionState.Disconnected
    assert ConsoleWrap(console).usable is False

    console._connection_state = enum.ConnectionState.Error
    assert ConsoleWrap(console).usable is False

    console._connection_state = enum.ConnectionState.Connected
    assert ConsoleWrap(console).usable is True


def test_connection_state(console):
    console._connection_state = enum.ConnectionState.Reconnecting

    assert ConsoleWrap(console).connection_state == enum.ConnectionState.Reconnecting


def test_pairing_state(console):
    console._pairing_state = enum.PairedIdentityState.Paired

    assert ConsoleWrap(console).pairing_state == enum.PairedIdentityState.Paired


def test_device_status(console):
    console._device_status = enum.DeviceStatus.Available

    assert ConsoleWrap(console).device_status == enum.DeviceStatus.Available


def test_authenticated_users_allowed(console):
    console.flags = enum.PrimaryDeviceFlag.AllowAuthenticatedUsers
    assert ConsoleWrap(console).authenticated_users_allowed is True

    console.flags = enum.PrimaryDeviceFlag.AllowConsoleUsers
    assert ConsoleWrap(console).authenticated_users_allowed is False

    console.flags = enum.PrimaryDeviceFlag.CertificatePending | enum.PrimaryDeviceFlag.AllowConsoleUsers
    assert ConsoleWrap(console).authenticated_users_allowed is False


def test_console_users_allowed(console):
    console.flags = enum.PrimaryDeviceFlag.AllowAuthenticatedUsers
    assert ConsoleWrap(console).console_users_allowed is False

    console.flags = enum.PrimaryDeviceFlag.AllowConsoleUsers
    assert ConsoleWrap(console).console_users_allowed is True

    console.flags = enum.PrimaryDeviceFlag.CertificatePending | enum.PrimaryDeviceFlag.AllowConsoleUsers
    assert ConsoleWrap(console).console_users_allowed is True


def test_anonymous_connection_allowed(console):
    console.flags = enum.PrimaryDeviceFlag.AllowAuthenticatedUsers
    assert ConsoleWrap(console).anonymous_connection_allowed is False

    console.flags = enum.PrimaryDeviceFlag.AllowConsoleUsers
    assert ConsoleWrap(console).anonymous_connection_allowed is False

    console.flags = enum.PrimaryDeviceFlag.CertificatePending | enum.PrimaryDeviceFlag.AllowAnonymousUsers
    assert ConsoleWrap(console).anonymous_connection_allowed is True


def test_is_certificate_pending(console):
    console.flags = enum.PrimaryDeviceFlag.AllowAuthenticatedUsers
    assert ConsoleWrap(console).is_certificate_pending is False

    console.flags = enum.PrimaryDeviceFlag.AllowConsoleUsers
    assert ConsoleWrap(console).is_certificate_pending is False

    console.flags = enum.PrimaryDeviceFlag.CertificatePending | enum.PrimaryDeviceFlag.AllowConsoleUsers
    assert ConsoleWrap(console).is_certificate_pending is True


def test_console_status(console, console_status):
    console._console_status = None
    assert ConsoleWrap(console).console_status is None

    console._console_status = console_status
    status = ConsoleWrap(console).console_status
    assert status is not None


def test_media_status(console, media_state, console_status, console_status_with_media):
    console.media._media_state = None
    assert ConsoleWrap(console).media_status is None

    console.media._media_state = media_state
    console._console_status = console_status_with_media
    console._connection_state = enum.ConnectionState.Disconnecting
    assert ConsoleWrap(console).media_status is None

    console._console_status = console_status  # miss-matched apps
    console._connection_state = enum.ConnectionState.Connected
    state = ConsoleWrap(console).media_status
    assert ConsoleWrap(console).media_status is None

    console._console_status = console_status_with_media
    state = ConsoleWrap(console).media_status


def test_status(console):
    status = ConsoleWrap(console).status
    assert status is not None


@pytest.mark.asyncio
async def test_connect(console):
    console.flags = enum.PrimaryDeviceFlag.AllowAuthenticatedUsers
    console._device_status = enum.DeviceStatus.Available
    console._connection_state = enum.ConnectionState.Disconnected
    console._pairing_state = enum.PairedIdentityState.NotPaired

    with pytest.raises(Exception):
        await ConsoleWrap(console).connect()

    console._connection_state = enum.ConnectionState.Connected
    state = await ConsoleWrap(console).connect()
    assert state == enum.ConnectionState.Connected

    console._connection_state = enum.ConnectionState.Disconnected
    console.flags = enum.PrimaryDeviceFlag.AllowAnonymousUsers
    # blocks forever
    # state = ConsoleWrap(console).connect()
    # assert state == enum.ConnectionState.Disconnected
