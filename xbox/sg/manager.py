"""
Managers for handling different ServiceChannels.

If a manager for a specific :class:`ServiceChannel` is attached,
incoming messages get forwarded there, otherways they are discarded.

Managers can be attached by calling `add_manager()` on the :class:`Console` object (see example)
Methods of manager are available through console-context

Example:
    How to add a manager::

        discovered = Console.discover(timeout=1)
        if len(discovered):
            console = discovered[0]

            # Add manager, optionally passing initialization parameter
            some_arg_for_manager_init = 'example'
            console.add_manager(MediaManager, additional_arg=some_arg_for_manager_init)

            console.connect()
            if console.connection_state != ConnectionState.Connected:
                print("Connection failed")
                sys.exit(1)
            console.wait(1)

            # Call manager method
            console.media_command(0x54321, MediaControlCommand.PlayPauseToggle, 0)

            try:
                console.protocol.serve_forever()
            except KeyboardInterrupt:
                pass
        else:
            print("No consoles discovered")
            sys.exit(1)
"""
import time
import logging
from xbox.sg import factory
from xbox.sg.enum import MessageType, ServiceChannel, AckStatus, TextResult
from xbox.sg.utils.events import Event

log = logging.getLogger(__name__)


class Manager(object):
    __namespace__ = ''

    def __init__(self, console, channel):
        """
        Don't use directly!
        INTERNALLY called by the parent :class:`Console`!

        Args:
            console (:class:`Console`): Console object, internally passed
                by `Console.add_manager`
            channel (:class:`ServiceChannel`): Service channel
        """
        self.console = console
        self.console.protocol.on_message += self._pre_on_message
        self.console.protocol.on_json += self._pre_on_json
        self._channel = channel

    def _pre_on_message(self, msg, channel):
        if channel == self._channel:
            self._on_message(msg, channel)

    def _pre_on_json(self, data, channel):
        if channel == self._channel:
            self._on_json(data, channel)

    def _on_message(self, msg, channel):
        """
        Managers must implement this
        """
        pass

    def _on_json(self, data, channel):
        """
        Managers must implement this
        """
        pass

    def _send_message(self, msg):
        """
        Internal method to send messages to initialized Service Channel

        Args:
            msg (:class:`XStructObj`): Message
        """
        return self.console.protocol.send_message(msg, channel=self._channel)

    def _send_json(self, data):
        """
        Internal method to send JSON messages to initialized Service Channel

        Args:
            data (dict): JSON message
        """
        return self.console.protocol.json(data, channel=self._channel)


class InputManagerError(Exception):
    """
    Exception thrown by InputManager
    """
    pass


class InputManager(Manager):
    __namespace__ = 'input'

    def __init__(self, console):
        """
        Input Manager (ServiceChannel.SystemInput)

        Args:
             console (:class:`.Console`): Console object, internally passed
                                          by `Console.add_manager`

        """
        super(InputManager, self).__init__(console, ServiceChannel.SystemInput)

    def _on_message(self, msg, channel):
        """
        Internal handler method to receive messages from SystemInput Channel

        Args:
            msg (:class:`XStructObj`): Message
            channel (:class:`ServiceChannel`): Service channel
        """
        raise InputManagerError("Unexpected message received on InputManager")

    def gamepad_input(self, buttons, l_trigger=0, r_trigger=0, l_thumb_x=0,
                      l_thumb_y=0, r_thumb_x=0, r_thumb_y=0):
        """
        Send gamepad input

        Args:
            buttons (:class:`GamePadButton`): Gamepad buttons bits
            l_trigger (int): Left trigger value
            r_trigger (int): Right trigger value
            l_thumb_x (int): Left thumbstick X-axis value
            l_thumb_y (int): Left thumbstick Y-axis value
            r_thumb_x (int): Right thumbstick X-axis value
            r_thumb_y (int): Right thumbstick Y-axis value

        Returns: None
        """
        ts = int(time.time())
        msg = factory.gamepad(
            ts, buttons, l_trigger, r_trigger, l_thumb_x, l_thumb_y,
            r_thumb_x, r_thumb_y
        )
        return self._send_message(msg)


class MediaManagerError(Exception):
    """
    Exception thrown by MediaManager
    """
    pass


class MediaManager(Manager):
    __namespace__ = 'media'

    def __init__(self, console):
        """
        Media Manager (ServiceChannel.SystemMedia)

        Args:
             console (:class:`.Console`): Console object, internally passed
                                          by `Console.add_manager`

        """
        super(MediaManager, self).__init__(console, ServiceChannel.SystemMedia)
        self._media_state = None
        self.on_media_state = Event()
        self.on_media_command_result = Event()
        self.on_media_controller_removed = Event()

    def _on_message(self, msg, channel):
        """
        Internal handler method to receive messages from SystemMedia Channel

        Args:
            msg (:class:`XStructObj`): Message
            channel (:class:`ServiceChannel`): Service channel
        """
        msg_type = msg.header.flags.msg_type
        payload = msg.protected_payload
        if msg_type == MessageType.MediaState:
            log.debug('Received MediaState message')
            self._media_state = payload
            self.on_media_state(self.media_state)

        elif msg_type == MessageType.MediaCommandResult:
            log.debug('Received MediaCommandResult message')
            self.on_media_command_result(payload)

        elif msg_type == MessageType.MediaControllerRemoved:
            title_id = payload.title_id
            log.debug('Received MediaControllerRemoved message, title id: 0x%x', title_id)
            if self.title_id == title_id:
                log.debug('Clearing MediaState')
                self._media_state = None
            self.on_media_controller_removed(payload)

        else:
            raise MediaManagerError("Unexpected message received on MediaManager")

    @property
    def media_state(self):
        """
        Media state payload

        Returns:
            :class:`Container`: Media state payload
        """
        return self._media_state

    @property
    def active_media(self):
        """
        Check whether console has active media

        Returns:
            bool: `True` if media is active, `False` if not
        """
        return self.media_state is not None

    @property
    def title_id(self):
        """
        Title Id of active media

        Returns:
            int: Title Id
        """
        if self.media_state:
            return self.media_state.title_id

    @property
    def aum_id(self):
        """
        Application user model Id of active media

        Returns:
            str: Aum Id
        """
        if self.media_state:
            return self.media_state.aum_id

    @property
    def asset_id(self):
        """
        Asset Id of active media

        Returns:
            str: Asset Id
        """
        if self.media_state:
            return self.media_state.asset_id

    @property
    def media_type(self):
        """
        Media type of active media

        Returns:
            :class:`MediaType`: Media type
        """
        if self.media_state:
            return self.media_state.media_type

    @property
    def sound_level(self):
        """
        Sound level of active media

        Returns:
            :class:`SoundLevel`: Sound level
        """
        if self.media_state:
            return self.media_state.sound_level

    @property
    def enabled_commands(self):
        """
        Enabled MediaCommands bitmask

        Returns:
            :class:`MediaControlCommand`: Bitmask of enabled commands
        """
        if self.media_state:
            return self.media_state.enabled_commands

    @property
    def playback_status(self):
        """
        Title Id of active media

        Returns:
            :class:`MediaPlaybackStatus`: Playback status
        """
        if self.media_state:
            return self.media_state.playback_status

    @property
    def rate(self):
        """
        Playback rate of active media

        Returns:
            float: Playback rate
        """
        if self.media_state:
            return self.media_state.rate

    @property
    def position(self):
        """
        Playback position of active media

        Returns:
            int: Playback position in microseconds
        """
        if self.media_state:
            return self.media_state.position

    @property
    def media_start(self):
        """
        Media start position of active media

        Returns:
            int: Media start position in microseconds
        """
        if self.media_state:
            return self.media_state.media_start

    @property
    def media_end(self):
        """
        Media end position of active media

        Returns:
            int: Media end position in microseconds
        """
        if self.media_state:
            return self.media_state.media_end

    @property
    def min_seek(self):
        """
        Minimum seek position of active media

        Returns:
            int: Minimum position in microseconds
        """
        if self.media_state:
            return self.media_state.min_seek

    @property
    def max_seek(self):
        """
        Maximum seek position of active media

        Returns:
            int: Maximum position in microseconds
        """
        if self.media_state:
            return self.media_state.max_seek

    @property
    def metadata(self):
        """
        Media metadata of active media

        Returns:
            :class:`Container`: Media metadata
        """
        if self.media_state:
            return self.media_state.metadata

    def media_command(self, title_id, command, request_id=0,
                      seek_position=None):
        """
        Send media command

        Args:
            title_id (int): Title Id
            command (:class:`MediaControlCommand`): Media Command
            request_id (int): Incrementing Request Id
            seek_position (int): (optional) Seek position

        Returns: None
        """
        msg = factory.media_command(
            request_id, title_id, command, seek_position
        )
        return self._send_message(msg)


class TextManagerError(Exception):
    """
    Exception thrown by TextManager
    """
    pass


class TextManager(Manager):
    __namespace__ = 'text'

    def __init__(self, console):
        """
        Text Manager (ServiceChannel.SystemText)

        Args:
             console (:class:`.Console`): Console object, internally passed
                                          by `Console.add_manager`

        """
        super(TextManager, self).__init__(console, ServiceChannel.SystemText)

        self.session_config = None
        self.current_session_input = None
        self.last_session_ack = None
        self._current_text_version = 0

        self.on_systemtext_configuration = Event()
        self.on_systemtext_input = Event()
        self.on_systemtext_done = Event()

    def _on_message(self, msg, channel):
        """
        Internal handler method to receive messages from SystemText Channel

        Args:
            msg (:class:`XStructObj`): Message
            channel (:class:`ServiceChannel`): Service channel
        """
        msg_type = msg.header.flags.msg_type
        payload = msg.protected_payload
        session_id = payload.text_session_id

        if msg_type == MessageType.SystemTextConfiguration:
            self.reset_session()
            self.session_config = payload
            self.on_systemtext_configuration(payload)

        elif msg_type == MessageType.SystemTextInput:
            # Assign console input msg
            self.current_session_input = payload
            self.current_text_version = payload.submitted_version
            self.send_systemtext_ack(self.text_session_id,
                                     self.current_text_version)
            self.on_systemtext_input(payload)

        elif msg_type == MessageType.SystemTextAck:
            self.current_text_version = payload.text_version_ack

        elif msg_type == MessageType.SystemTextDone:
            if session_id == self.text_session_id:
                self.reset_session()
            elif session_id == 0:
                # SystemTextDone for session 0 is sent by console
                # No clue what it means, if anything
                pass
            else:
                pass
                # log.debug('Received DONE msg for inactive session %i' % session_id)

            self.on_systemtext_done(payload)

        elif msg_type in [MessageType.TitleTextConfiguration,
                          MessageType.TitleTextInput,
                          MessageType.TitleTextSelection]:
            raise TextManagerError('Received TitleTextConfiguration, unhandled')
        else:
            raise TextManagerError(
                "Unexpected message received on TextManager"
            )

    @property
    def got_active_session(self):
        """
        Check whether a text session is active
        
        Returns:
            bool: Returns `True` if any text session is active, `False` otherwise
        """
        return self.session_config is not None

    @property
    def current_text_version(self):
        """
        Current Text version
        
        Returns:
             int: Current Text Version
        """
        return self._current_text_version

    @current_text_version.setter
    def current_text_version(self, value):
        if value > self.current_text_version:
            self._current_text_version = value

    @property
    def text_session_id(self):
        """
        Current Text session id
        
        Returns:
            int: Text session id if existing, `None` otherwise
        """
        if self.session_config:
            return self.session_config.text_session_id

    @property
    def text_options(self):
        """
        Current Text options
        
        Returns:
            :class:`TextOption`: Text options if existing, `None` otherwise
        """
        if self.session_config:
            return self.session_config.text_options

    @property
    def text_input_scope(self):
        """
        Current Text input scope
        
        Returns:
            :class:`TextInputScope`: Text input scope if existing, `None` otherwise
        """
        if self.session_config:
            return self.session_config.input_scope

    @property
    def max_text_length(self):
        """
        Maximum Text length
        
        Returns:
            int: Max text length if existing, `None` otherwise
        """
        if self.session_config:
            return self.session_config.max_text_length

    @property
    def text_locale(self):
        """
        Test
        
        Returns:
            str: Text locale if existing, `None` otherwise
        """
        if self.session_config:
            return self.session_config.locale

    @property
    def text_prompt(self):
        """
        Test
        
        Returns:
            str: Text prompt if existing, `None` otherwise
        """
        if self.session_config:
            return self.session_config.prompt

    def reset_session(self):
        """
        Delete cached text-session config, -input and -ack messages

        Returns:
            None
        """
        self.session_config = None
        self.current_session_input = None
        self.last_session_ack = None
        self.current_text_version = 0

    def finish_text_input(self):
        """
        Finishes current text session.

        Returns:
            None
        """
        self.send_systemtext_done(
            session_id=self.text_session_id,
            version=self.current_session_input.submitted_version,
            flags=0,
            result=TextResult.Accept
        )

    def send_systemtext_input(self, text):
        """
        Sends text input

        Args:
            text (str): Text string to send

        Raises:
            TextManagerError: If message was not
            acknowledged via AckMsg or SystemTextAck

        Returns:
            int: Member of :class:`AckStatus`
        """
        new_version = self.current_text_version + 1
        msg = factory.systemtext_input(
            session_id=self.text_session_id,
            base_version=self.current_text_version,
            submitted_version=new_version,
            total_text_len=len(text),
            selection_start=-1,
            selection_length=-1,
            flags=0,
            text_chunk_byte_start=0,
            text_chunk=text,
            delta=None
        )

        ack_status = self._send_message(msg)
        if ack_status != AckStatus.Processed:
            raise TextManagerError('InputMsg was not acknowledged: %s' % msg)

        # Assign client system input msg
        self.current_session_input = msg.protected_payload
        return ack_status

    def send_systemtext_ack(self, session_id, version):
        """
        Acknowledges a SystemText message sent from the console

        Args:
            session_id (int): Current text session id
            version (int): Text version to ack

        Returns:
            int: Member of :class:`AckStatus`
        """
        msg = factory.systemtext_ack(session_id, version)
        return self._send_message(msg)

    def send_systemtext_done(self, session_id, version, flags, result):
        """
        Informs the console that a text session is done.

        Result field tells wether text input should be
        accepted or cancelled.

        Args:
            session_id (int): Current text session id
            version (id): Last acknowledged text version
            flags (int): Flags
            result (:class:`TextResult`): Member to :class:`TextResult`

        Returns:
            int: Member of :class:`AckStatus`
        """
        msg = factory.systemtext_done(session_id, version, flags, result)
        ack_status = self._send_message(msg)
        if ack_status != AckStatus.Processed:
            raise TextManagerError('DoneMsg was not acknowledged: %s' % msg)

        return ack_status
