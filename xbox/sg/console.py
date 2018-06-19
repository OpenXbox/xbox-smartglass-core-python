"""
Console

Console class is a wrapper around the protocol, can be used to
`discover`, `poweron` and `connect`.
Also stores various device status informations.

It can be either created manually or instantiated via `DiscoveryResponse`
message. However, calling static method `discover` does all that for you
automatically.

Example:
    Discovery and connecting::

        import sys
        from xbox.sg.console import Console
        from xbox.sg.enum import ConnectionState

        discovered = Console.discover(timeout=1)
        if len(discovered):
            console = discovered[0]
            console.connect()
            if console.connection_state != ConnectionState.Connected:
                print("Connection failed")
                sys.exit(1)
            console.wait(1)

            try:
                console.protocol.serve_forever()
            except KeyboardInterrupt:
                pass
        else:
            print("No consoles discovered")
            sys.exit(1)
"""

import gevent
from uuid import UUID

from xbox.sg.crypto import Crypto
from xbox.sg.manager import Manager
from xbox.sg.enum import PairedIdentityState, DeviceStatus, ConnectionState,\
    MessageType, PrimaryDeviceFlag, ActiveTitleLocation
from xbox.sg.protocol import CoreProtocol, ProtocolError
from xbox.sg.utils.events import Event


class Console(object):
    __protocol__ = CoreProtocol()

    def __init__(self, address, name, uuid, liveid, flags=PrimaryDeviceFlag.Null, public_key=None):
        """
        Initialize an instance of Console

        Args:
            address (str): IP address of console.
            flags (:class:`PrimaryDeviceFlag`): Primary device flags
            name (str): Name of console.
            uuid (:obj:`UUID`): UUID of console.
            liveid (str): Live ID of console.
            public_key (:obj:`ec.EllipticCurvePrivateKey`):
                Console's Public Key.
        """
        self.address = address
        self.name = name
        self.uuid = uuid
        self.liveid = liveid
        self.flags = flags
        self._public_key = None
        self._crypto = None

        if public_key:
            # This sets up the crypto context
            self.public_key = public_key

        self._device_status = DeviceStatus.Unavailable
        self._connection_state = ConnectionState.Disconnected
        self._pairing_state = PairedIdentityState.NotPaired
        self._console_status = None
        self._active_surface = None

        self.on_device_status = Event()
        self.on_connection_state = Event()
        self.on_pairing_state = Event()
        self.on_console_status = Event()
        self.on_active_surface = Event()
        self.on_timeout = Event()

        self.managers = {}
        self._functions = {}

        self.power_on = self._power_on  # Dirty hack

        self._init_protocol()

    def __repr__(self):
        return '<Console addr={} name={} uuid={} liveid={} flags={}>'.format(
            self.address, self.name, self.uuid, self.liveid, self.flags
        )

    def __enter__(self):
        return self

    def __exit__(self):
        self.disconnect()

    @staticmethod
    def wait(seconds):
        """
        Wrapper around `gevent.sleep`

        Args:
            seconds (int): Seconds to wait.

        Returns: None
        """
        gevent.sleep(seconds)

    def _init_protocol(self):
        self.protocol = CoreProtocol(self.address, self._crypto)
        # Proxy protocol event into console
        self.protocol.on_timeout += self._on_timeout
        self.protocol.on_message += self._on_message

    @classmethod
    def __start_cls_protocol(cls):
        """
        Start the protocol internally, if not running

        Returns: None
        """
        if not cls.__protocol__.started:
            cls.__protocol__.start()

    @classmethod
    def from_message(cls, address, msg):
        """
        Initialize the class with a `DiscoveryResponse`.

        Args:
            address (str): IP address of the console
            msg (:obj:`.StructObj`): Discovery Response struct

        Returns: :class:`Console`.

        """
        payload = msg.unprotected_payload
        console = cls(
            address, payload.name, payload.uuid, payload.cert.liveid,
            payload.flags, payload.cert.pubkey
        )
        console.device_status = DeviceStatus.Available
        return console

    @classmethod
    def from_dict(cls, d):
        return cls(d['address'], d['name'], UUID(d['uuid']), d['liveid'])

    def to_dict(self):
        return dict(address=self.address, name=self.name, uuid=str(self.uuid), liveid=self.liveid)

    def add_manager(self, manager, *args, **kwargs):
        """
        Add a manager to the console instance.

        This will inherit all public methods of the manager class.

        Args:
            manager (:class:`.Manager`):
            *args: Arguments
            **kwargs: KwArguments

        Returns:
            None
        """
        if not issubclass(manager, Manager):
            raise ValueError("Manager needs to subclass {}.{}".format(
                Manager.__module__, Manager.__name__)
            )

        namespace = getattr(manager, '__namespace__', manager.__name__.lower())
        manager_inst = manager(self, *args, **kwargs)
        self.managers[namespace] = manager_inst

        for item in dir(manager):
            if item.startswith('_'):
                continue

            if item in self.__dict__:
                raise ValueError("Attribute already exists: %s" % item)

            self._functions[item] = getattr(manager_inst, item)

    def __getattr__(self, k):
        if k in self.managers:
            return self.managers[k]
        elif k in self._functions:
            return self._functions[k]
        return object.__getattribute__(self, k)

    @classmethod
    def discover(cls, *args, **kwargs):
        """
        Discover consoles on the network.

        Args:
            *args:
            **kwargs:

        Returns:
            list: List of discovered consoles.

        """
        cls.__start_cls_protocol()
        discovered = cls.__protocol__.discover(*args, **kwargs)
        return [cls.from_message(a, m) for a, m in discovered.items()]

    @classmethod
    def discovered(cls):
        """
        Get list of already discovered consoles.

        Returns:
            list: List of discovered consoles.

        """
        discovered = cls.__protocol__.discovered
        return [cls.from_message(a, m) for a, m in discovered.items()]

    @classmethod
    def power_on(cls, liveid, addr=None, tries=2):
        """
        Power On console with given Live ID.

        Optionally the IP address of the console can be supplied,
        this is useful if the console is stubborn and does not react
        to broadcast / multicast packets (due to routing issues).

        Args:
            liveid (str): Live ID of console.
            addr (str): IP address of console.
            tries (int): Poweron attempts, default: 2.

        Returns: None

        """
        cls.__start_cls_protocol()
        cls.__protocol__.power_on(liveid, addr, tries)

    def _power_on(self, tries=2):
        Console.power_on(self.liveid, self.address, tries)

    def connect(self, userhash='', xsts_token=''):
        """
        Connect to the console

        If the connection fails, error will be stored in
        `self.connection_state`

        Raises:
            ConnectionException: If no authentication data is supplied and
                console disallows anonymous connection.

        Returns:
            :class:`ConnectionState`: Connection state
        """
        if self.connected:
            raise ConnectionError("Already connected")

        if not self.anonymous_connection_allowed and \
           not userhash and not xsts_token:
            raise ConnectionError("Anonymous connection not allowed, please"
                                  " supply userhash and auth-token")

        if not self.protocol.started:
            self.protocol.start()

        self.pairing_state = PairedIdentityState.NotPaired
        self.connection_state = ConnectionState.Connecting

        try:
            self.pairing_state = self.protocol.connect(userhash=userhash,
                                                       xsts_token=xsts_token)
        except ProtocolError as e:
            self.connection_state = ConnectionState.Error
            raise e

        self.connection_state = ConnectionState.Connected
        return self.connection_state

    def launch_title(self, uri, location=ActiveTitleLocation.Full):
        """
        Launch a title by URI

        Args:
            uri (str): Launch uri
            location (:class:`ActiveTitleLocation`): Target title location

        Returns:
            int: Member of :class:`AckStatus`
        """
        return self.protocol.launch_title(uri, location)

    def disconnect(self):
        """
        Disconnect from console.

        This will reset connection-, pairing-state,
        ActiveSurface and ConsoleStatus.

        Returns: None
        """
        if self.connection_state == ConnectionState.Connected:
            self.connection_state = ConnectionState.Disconnecting
            self.protocol.stop()  # Stop also sends SG disconnect message
            self._reset_state()

    def power_off(self):
        """
        Power off the console.

        No need to disconnect after.

        Returns: None
        """
        self.protocol.power_off(self.liveid)
        self._reset_state()
        self.device_status = DeviceStatus.Unavailable

    def _on_message(self, msg, channel):
        """
        Internal handler for console specific messages aka.
        `PairedIdentityStateChange`, `ConsoleStatus` and
        `ActiveSurfaceChange`.

        Args:
            msg (:obj:`XStruct`): Message data
            channel (:class:`ServiceChannel`): Service channel

        Returns:
            None
        """
        msg_type = msg.header.flags.msg_type

        if msg_type == MessageType.PairedIdentityStateChanged:
            self.pairing_state = msg.protected_payload.state

        elif msg_type == MessageType.ConsoleStatus:
            self.console_status = msg.protected_payload

        elif msg_type == MessageType.ActiveSurfaceChange:
            self.active_surface = msg.protected_payload

    def _on_timeout(self):
        """
        Internal handler for console connection timeout.

        Returns: None
        """
        self._reset_state()
        self.device_status = DeviceStatus.Unavailable
        self.on_timeout()

    def _reset_state(self):
        """
        Internal handler to reset the inital state of the console instance.

        Returns: None
        """
        if self.protocol and self.protocol.started:
            self.protocol.stop()
        self._init_protocol()

        self.connection_state = ConnectionState.Disconnected
        self.pairing_state = PairedIdentityState.NotPaired
        self.active_surface = None
        self.console_status = None

    @property
    def public_key(self):
        """
        Console's public key.

        Returns:
            :obj:`ec.EllipticCurvePrivateKey`: Foreign public key
        """
        return self._public_key

    @public_key.setter
    def public_key(self, key):
        if isinstance(key, bytes):
            self._crypto = Crypto.from_bytes(key)
        else:
            self._crypto = Crypto(key)

        self._public_key = self._crypto.foreign_pubkey

    @property
    def device_status(self):
        """
        Current availability status

        Returns:
            :obj:`DeviceStatus`
        """
        return self._device_status

    @device_status.setter
    def device_status(self, status):
        self._device_status = status
        self.on_device_status(status)

    @property
    def connection_state(self):
        """
        Current connection state

        Returns:
            :obj:`ConnectionState`
        """
        return self._connection_state

    @connection_state.setter
    def connection_state(self, state):
        self._connection_state = state
        self.on_connection_state(state)

    @property
    def pairing_state(self):
        """
        Current pairing state

        Returns:
            :obj:`PairedIdentityState`
        """
        return self._pairing_state

    @pairing_state.setter
    def pairing_state(self, state):
        self._pairing_state = state
        self.on_pairing_state(state)

    @property
    def console_status(self):
        """
        Console status aka. kernel version, active titles etc.

        Returns:
            :obj:`XStruct`
        """
        return self._console_status

    @console_status.setter
    def console_status(self, status):
        self._console_status = status
        self.on_console_status(status)

    @property
    def active_surface(self):
        """
        Currently active surface

        Returns:
            :obj:`XStruct`
        """
        return self._active_surface

    @active_surface.setter
    def active_surface(self, active_surface):
        self._active_surface = active_surface
        self.on_active_surface(active_surface)

    @property
    def available(self):
        """
        Check whether console is available aka. discoverable

        Returns:
            bool: `True` if console is available, `False` otherwise
        """
        return self.device_status == DeviceStatus.Available

    @property
    def paired(self):
        """
        Check whether client is paired to console

        Returns:
            bool: `True` if console is paired, `False` otherwise
        """
        return self.pairing_state == PairedIdentityState.Paired

    @property
    def connected(self):
        """
        Check whether client is successfully connected to console

        Returns:
            bool: `True` if connected, `False` otherwise
        """
        return self.connection_state == ConnectionState.Connected

    @property
    def authenticated_users_allowed(self):
        """
        Check whether authenticated users are allowed to connect

        Returns:
            bool: `True` if authenticated users are allowed, `False` otherwise
        """
        return bool(self.flags & PrimaryDeviceFlag.AllowAuthenticatedUsers)

    @property
    def console_users_allowed(self):
        """
        Check whether console users are allowed to connect

        Returns:
            bool: `True` if console users are allowed, `False` otherwise
        """
        return bool(self.flags & PrimaryDeviceFlag.AllowConsoleUsers)

    @property
    def anonymous_connection_allowed(self):
        """
        Check whether anonymous connection is allowed

        Returns:
            bool: `True` if anonymous connection is allowed, `False` otherwise
        """
        return bool(self.flags & PrimaryDeviceFlag.AllowAnonymousUsers)

    @property
    def is_certificate_pending(self):
        """
        Check whether certificate is pending

        Returns:
            bool: `True` if certificate is pending, `False` otherwise
        """
        return bool(self.flags & PrimaryDeviceFlag.CertificatePending)
