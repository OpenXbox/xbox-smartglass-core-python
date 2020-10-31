from typing import Dict, Optional
import logging

from xbox.sg import enum
from xbox.sg.console import Console
from xbox.sg.manager import InputManager, TextManager, MediaManager
from xbox.stump.manager import StumpManager
from xbox.stump import json_model as stump_schemas

from . import schemas

log = logging.getLogger()


class ConsoleWrap(object):
    def __init__(self, console: Console):
        self.console = console

        if 'input' not in self.console.managers:
            self.console.add_manager(InputManager)
        if 'text' not in self.console.managers:
            self.console.add_manager(TextManager)
        if 'media' not in self.console.managers:
            self.console.add_manager(MediaManager)
        if 'stump' not in self.console.managers:
            self.console.add_manager(StumpManager)

    @staticmethod
    async def discover(*args, **kwargs):
        return await Console.discover(*args, **kwargs)

    @staticmethod
    async def power_on(
        liveid: str, addr: str = None, iterations: int = 3, tries: int = 10
    ) -> None:
        for i in range(iterations):
            await Console.power_on(liveid, addr=addr, tries=tries)
            await Console.wait(1)

    @property
    def media_commands(self) -> Dict[str, enum.MediaControlCommand]:
        return {
            'play': enum.MediaControlCommand.Play,
            'pause': enum.MediaControlCommand.Pause,
            'play_pause': enum.MediaControlCommand.PlayPauseToggle,
            'stop': enum.MediaControlCommand.Stop,
            'record': enum.MediaControlCommand.Record,
            'next_track': enum.MediaControlCommand.NextTrack,
            'prev_track': enum.MediaControlCommand.PreviousTrack,
            'fast_forward': enum.MediaControlCommand.FastForward,
            'rewind': enum.MediaControlCommand.Rewind,
            'channel_up': enum.MediaControlCommand.ChannelUp,
            'channel_down': enum.MediaControlCommand.ChannelDown,
            'back': enum.MediaControlCommand.Back,
            'view': enum.MediaControlCommand.View,
            'menu': enum.MediaControlCommand.Menu,
            'seek': enum.MediaControlCommand.Seek
        }

    @property
    def input_keys(self) -> Dict[str, enum.GamePadButton]:
        return {
            'clear': enum.GamePadButton.Clear,
            'enroll': enum.GamePadButton.Enroll,
            'nexus': enum.GamePadButton.Nexu,
            'menu': enum.GamePadButton.Menu,
            'view': enum.GamePadButton.View,
            'a': enum.GamePadButton.PadA,
            'b': enum.GamePadButton.PadB,
            'x': enum.GamePadButton.PadX,
            'y': enum.GamePadButton.PadY,
            'dpad_up': enum.GamePadButton.DPadUp,
            'dpad_down': enum.GamePadButton.DPadDown,
            'dpad_left': enum.GamePadButton.DPadLeft,
            'dpad_right': enum.GamePadButton.DPadRight,
            'left_shoulder': enum.GamePadButton.LeftShoulder,
            'right_shoulder': enum.GamePadButton.RightShoulder,
            'left_thumbstick': enum.GamePadButton.LeftThumbStick,
            'right_thumbstick': enum.GamePadButton.RightThumbStick
        }

    @property
    def liveid(self) -> str:
        return self.console.liveid

    @property
    def last_error(self) -> int:
        return self.console.last_error

    @property
    def available(self) -> bool:
        return bool(self.console and self.console.available)

    @property
    def connected(self) -> bool:
        return bool(self.console and self.console.connected)

    @property
    def usable(self) -> bool:
        return bool(self.console and self.connected)

    @property
    def connection_state(self) -> enum.ConnectionState:
        if not self.console:
            return enum.ConnectionState.Disconnected

        return self.console.connection_state

    @property
    def pairing_state(self) -> enum.PairedIdentityState:
        if not self.console:
            return enum.PairedIdentityState.NotPaired

        return self.console.pairing_state

    @property
    def device_status(self) -> enum.DeviceStatus:
        if not self.console:
            return enum.DeviceStatus.Unavailable

        return self.console.device_status

    @property
    def authenticated_users_allowed(self) -> bool:
        return bool(self.console and self.console.authenticated_users_allowed)

    @property
    def console_users_allowed(self) -> bool:
        return bool(self.console and self.console.console_users_allowed)

    @property
    def anonymous_connection_allowed(self) -> bool:
        return bool(self.console and self.console.anonymous_connection_allowed)

    @property
    def is_certificate_pending(self) -> bool:
        return bool(self.console and self.console.is_certificate_pending)

    @property
    def console_status(self) -> Optional[schemas.ConsoleStatusResponse]:
        status_json = {}

        if not self.console or not self.console.console_status:
            return None

        status = self.console.console_status
        kernel_version = '{0}.{1}.{2}'.format(status.major_version, status.minor_version, status.build_number)

        status_json.update({
            'live_tv_provider': status.live_tv_provider,
            'kernel_version': kernel_version,
            'locale': status.locale
        })

        active_titles = []
        for at in status.active_titles:
            title = {
                'title_id': at.title_id,
                'aum': at.aum,
                'name': at.aum,
                'image': None,
                'type': None,
                'has_focus': at.disposition.has_focus,
                'title_location': at.disposition.title_location.name,
                'product_id': str(at.product_id),
                'sandbox_id': str(at.sandbox_id)
            }
            active_titles.append(title)

        status_json.update({'active_titles': active_titles})
        return schemas.ConsoleStatusResponse(**status_json)

    @property
    def media_status(self) -> Optional[schemas.MediaStateResponse]:
        if not self.usable or not self.console.media or not self.console.media.media_state:
            return None

        media_state = self.console.media.media_state

        # Ensure we are in the same app, otherwise this is useless
        if media_state.aum_id not in [t.aum for t in self.console.console_status.active_titles]:
            return None

        media_state_json = {
            'title_id': media_state.title_id,
            'aum_id': media_state.aum_id,
            'asset_id': media_state.asset_id,
            'media_type': media_state.media_type.name,
            'sound_level': media_state.sound_level.name,
            'enabled_commands': media_state.enabled_commands.value,
            'playback_status': media_state.playback_status.name,
            'rate': media_state.rate,
            'position': media_state.position,
            'media_start': media_state.media_start,
            'media_end': media_state.media_end,
            'min_seek': media_state.min_seek,
            'max_seek': media_state.max_seek,
            'metadata': None
        }

        metadata = {}
        for meta in media_state.metadata:
            metadata[meta.name] = meta.value

        media_state_json['metadata'] = metadata
        return schemas.MediaStateResponse(**media_state_json)

    @property
    def status(self) -> schemas.DeviceStatusResponse:
        data = self.console.to_dict()
        data.update({
            'liveid': self.console.liveid,
            'ip_address': self.console.address,
            'connection_state': self.connection_state.name,
            'pairing_state': self.pairing_state.name,
            'device_status': self.device_status.name,
            'last_error': self.last_error,
            'authenticated_users_allowed': self.authenticated_users_allowed,
            'console_users_allowed': self.console_users_allowed,
            'anonymous_connection_allowed': self.anonymous_connection_allowed,
            'is_certificate_pending': self.is_certificate_pending
        })

        return schemas.DeviceStatusResponse(**data)

    @property
    def text_active(self) -> bool:
        if self.usable:
            return self.console.text.got_active_session

    async def get_stump_config(self) -> stump_schemas.Configuration:
        if self.usable:
            return await self.console.stump.request_stump_configuration()

    async def get_headend_info(self) -> stump_schemas.HeadendInfo:
        if self.usable:
            return await self.console.stump.request_headend_info()

    async def get_livetv_info(self) -> stump_schemas.LiveTvInfo:
        if self.usable:
            return await self.console.stump.request_live_tv_info()

    async def get_tuner_lineups(self) -> stump_schemas.TunerLineups:
        if self.usable:
            return await self.console.stump.request_tuner_lineups()

    async def connect(
        self,
        userhash: Optional[str] = None,
        xtoken: Optional[str] = None
    ) -> enum.ConnectionState:
        if not self.console:
            return enum.ConnectionState.Disconnected
        elif self.console.connected:
            return enum.ConnectionState.Connected
        elif not self.anonymous_connection_allowed and (not userhash or not xtoken):
            raise Exception('Requested anonymous connection is not allowed by console')

        state = await self.console.connect(userhash=userhash,
                                           xsts_token=xtoken)

        if state == enum.ConnectionState.Connected:
            await self.console.wait(0.5)
            await self.console.stump.request_stump_configuration()

        return state

    async def disconnect(self) -> bool:
        await self.console.disconnect()
        return True

    async def power_off(self) -> bool:
        await self.console.power_off()
        return True

    async def launch_title(self, app_id: str) -> None:
        return await self.console.launch_title(app_id)

    async def send_stump_key(self, device_id: str, button: str) -> bool:
        result = await self.console.send_stump_key(button, device_id)
        print(result)
        return True

    async def send_media_command(self, command: enum.MediaControlCommand, seek_position: Optional[int] = None) -> bool:
        title_id = 0
        request_id = 0
        await self.console.media_command(title_id, command, request_id, seek_position)
        return True

    async def send_gamepad_button(self, btn: enum.GamePadButton) -> bool:
        await self.console.gamepad_input(btn)
        # Its important to clear button-press afterwards
        await self.console.wait(0.1)
        await self.console.gamepad_input(enum.GamePadButton.Clear)
        return True

    async def send_text(self, text: str) -> bool:
        if not self.text_active:
            return False

        await self.console.send_systemtext_input(text)
        await self.console.finish_text_input()
        return True

    async def dvr_record(self, start_delta, end_delta) -> bool:
        await self.console.game_dvr_record(start_delta, end_delta)
        return True
