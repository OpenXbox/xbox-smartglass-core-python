"""
Terminal UI Smartglass Client

Supported functions: Poweron/off, launch title, gamepad input and entering text.
Additional shows console status (active titles, OS version, locale) and media state.
"""
import json
import urwid
import logging
import asyncio
from typing import List, Optional
from binascii import hexlify

from ..scripts import ExitCodes
from ..sg.console import Console
from ..sg.enum import DeviceStatus, GamePadButton, MediaPlaybackStatus
from ..sg.manager import InputManager, TextManager, MediaManager

from xbox.webapi.authentication.manager import AuthenticationManager

from construct.lib import containers
containers.setGlobalPrintFullStrings(True)


class ControllerRemote(urwid.Filler):
    keymap = {
        'tab': GamePadButton.View,
        '<': GamePadButton.Menu,
        '#': GamePadButton.Nexu,
        'up': GamePadButton.DPadUp,
        'down': GamePadButton.DPadDown,
        'left': GamePadButton.DPadLeft,
        'right': GamePadButton.DPadRight,
        'a': GamePadButton.PadA,
        'b': GamePadButton.PadB,
        'x': GamePadButton.PadX,
        'y': GamePadButton.PadY
    }
    text = 'Use keyboard to send controller input'

    def __init__(self, app, console, original_widget):
        self.app = app
        self.console = console

        super(ControllerRemote, self).__init__(original_widget, 'top')

    def keypress(self, size, key):
        if key in self.keymap:
            button = self.keymap[key]
            asyncio.create_task(self.console.gamepad_input(button))
            asyncio.create_task(self.console.gamepad_input(GamePadButton.Clear))
        elif key in ('q', 'Q'):
            return key
        else:
            return super(ControllerRemote, self).keypress(size, key)


class QuestionBox(urwid.Filler):
    def __init__(self, edit_widget, callback, **kwargs):
        super(QuestionBox, self).__init__(edit_widget, **kwargs)
        self.callback = callback

    def keypress(self, size, key):
        if key != 'enter':
            return super(QuestionBox, self).keypress(size, key)
        else:
            self.callback(self.original_widget.edit_text)


class TextInput(urwid.Filler):
    def __init__(self, app, edit_widget, console, **kwargs):
        super(TextInput, self).__init__(edit_widget, **kwargs)
        self.app = app
        self.console = console

    def keypress(self, size, key):
        if key != 'enter':
            ret = super(TextInput, self).keypress(size, key)
            asyncio.create_task(self.console.send_systemtext_input(self.original_widget.edit_text))
            return ret
        else:
            asyncio.create_task(self.console.finish_text_input())
            self.app.return_to_details_menu()


class MediaProgressbar(urwid.ProgressBar):
    def __init__(self, normal, complete):
        super(MediaProgressbar, self).__init__(normal, complete)
        self._current_text = 'No media playing'

    def get_text(self):
        return self._current_text

    def update_from_state(self, state):
        if not state or state.playback_status in (MediaPlaybackStatus.Stopped, MediaPlaybackStatus.Closed):
            self._current_text = 'No media playing'
            self.set_completion(0.0)
        else:
            pos_seconds = state.position / 10000000
            total_seconds = state.media_end / 10000000
            self._current_text = '{pmin:02d}:{psec:02d} / {tmin:02d}:{tsec:02d}'.format(
                pmin=int(pos_seconds // 60),
                psec=int(pos_seconds % 60),
                tmin=int(total_seconds // 60),
                tsec=int(total_seconds % 60)
            )
            if state.media_end > 0:
                self.done = state.media_end
            self.set_completion(state.position)


class ConsoleView(urwid.Frame):
    def __init__(self, app, console, **kwargs):
        self.app = app
        self.console = console

        self.device_info = urwid.LineBox(urwid.Text('Not available'), 'Device info')
        self.status = urwid.LineBox(urwid.Text('Not available'), 'Console status')
        self.media_text = urwid.Text('Not available')
        self.media_progress = MediaProgressbar('pg normal', 'pg complete')
        media_state_pile = urwid.Pile([self.media_text, self.media_progress])
        self.media_state = urwid.LineBox(media_state_pile, 'Media State')

        self.pile = urwid.Pile([self.device_info, self.status, self.media_state])
        self.filler = urwid.Filler(self.pile, valign='top')

        self.update_device_info()
        self.console.on_timeout += self.update_device_info
        self.console.on_pairing_state += lambda _: self.update_device_info()
        self.console.on_connection_state += lambda _: self.update_device_info()
        self.console.on_active_surface += lambda _: self.update_device_info()
        self.console.on_console_status += self.on_console_status
        self.console.media.on_media_state += self.on_media_state
        self.console.text.on_systemtext_configuration += lambda _: self.app.view_text_input_overlay(self.console)
        self.console.text.on_systemtext_input += lambda _: None  # Update text overlay with input text
        self.console.text.on_systemtext_done += lambda _: self.app.return_to_details_menu()

        super(ConsoleView, self).__init__(self.filler, **kwargs)

    def update_device_info(self):
        text = 'Name: {c.name:<15}\nAddress: {c.address:<15}\nLiveID: {c.liveid:<15}\n' \
               'UUID: {c.uuid}\n\n'.format(c=self.console)

        text += 'Connection State: {:<15}\n'.format(self.console.connection_state.name)
        text += 'Pairing State: {:<15}\n'.format(self.console.pairing_state.name)
        # text += 'Active Surface: {}\n'.format(ActiveSurfaceType[self.console.active_surface.surface_type])
        text += 'Shared secret: {hex_secret}'.format(
            hex_secret=hexlify(self.console._crypto.shared_secret).decode('utf-8')
        )
        self.device_info.original_widget.set_text(text)

    def on_console_status(self, console_status):
        if not console_status:
            self.status.original_widget.set_text('Not available')
            return

        text = \
            'LiveTV Provider: {status.live_tv_provider:<10}' \
            'Locale: {status.locale:<10}' \
            'OS: {status.major_version}.{status.minor_version}.{status.build_number}\n'.format(
                status=console_status
            )
        for title in console_status.active_titles:
            text += '{focus} {title.aum} (0x{title.title_id:08x}) [{location}]\n'.format(
                focus='*' if title.disposition.has_focus else ' ',
                title=title, location=title.disposition.title_location.name
            )
        self.status.original_widget.set_text(text)

    def on_media_state(self, state):
        if not state:
            self.media_text.set_text('Not available')
            self.media_progress.update_from_state(state)
            return

        text = \
            'Title: {state.aum_id:<20} (0x{state.title_id:08x}) AssetId: {state.asset_id:<25}\n' \
            'MediaType: {media_type:<25} SoundLevel: {sound_level:<25}\n' \
            'Playback: {playback_status:<25}\n'.format(
                state=state, media_type=state.media_type.name, sound_level=state.sound_level.name,
                playback_status=state.playback_status.name
            )
        for metadata in state.metadata:
            text += '{metadata.name}: {metadata.value}\n'.format(metadata=metadata)
        if state.playback_status in (MediaPlaybackStatus.Stopped, MediaPlaybackStatus.Closed):
            self.media_text.set_text('Not available')
        else:
            self.media_text.set_text(text)
        self.media_progress.update_from_state(state)

    def keypress(self, size, key):
        if key in ('c', 'C'):
            self.app.view_commands_menu(self.console)
        else:
            return super(ConsoleView, self).keypress(size, key)


class ConsoleButton(urwid.Button):
    focus_map = {
        None: 'selected',
        'connected': 'connected selected'
    }

    def __init__(self, app, console):
        super(ConsoleButton, self).__init__('')
        self.app = app

        self.console = console
        self.console.add_manager(InputManager)
        self.console.add_manager(MediaManager)
        self.console.add_manager(TextManager)
        self.console.on_connection_state += lambda _: self.refresh()
        self.console.on_console_status += lambda _: self.refresh()
        self.console.on_device_status += lambda _: self.refresh()

        urwid.connect_signal(self, 'click', self.callback)
        self.textwidget = urwid.AttrWrap(urwid.SelectableIcon('', cursor_position=0), None)
        self._w = urwid.AttrMap(self.textwidget, None, self.focus_map)
        self.refresh()

    def callback(self, *args):
        asyncio.create_task(self.cb_connect())

    async def cb_connect(self):
        if await self.connect():
            self.app.view_details_menu(self.console)

    async def connect(self):
        if self.console.connected:
            return True

        if not self.console.available:
            self.app.view_msgbox('Console unavailable, try refreshing')
            return False

        userhash = ''
        xsts_token = ''

        if self.app.auth_mgr:
            userhash = self.app.auth_mgr.xsts_token.userhash
            xsts_token = self.app.auth_mgr.xsts_token.token

        state = await self.console.connect(
            userhash=userhash,
            xsts_token=xsts_token
        )

        if not self.console.connected:
            self.app.view_msgbox('Connection failed! State: {}'.format(state))
            return False

        return True

    async def disconnect(self):
        if self.console.connected:
            await self.console.disconnect()

    def refresh(self):
        text = ' {c.name:<20}{c.address:<20}{c.liveid:<20}{ds:<20}'.format(
            c=self.console,
            ds=f'{self.console.device_status.name}, {self.console.connection_state.name}'
        )
        self.textwidget.set_text(text)

        if self.console.connected:
            self.textwidget.set_attr('connected')
        else:
            self.textwidget.set_attr(None)

    def keypress(self, size, key):
        if key in ('p', 'P'):
            asyncio.create_task(self.console.power_on())
        elif key in ('c', 'C'):
            asyncio.create_task(self.connect())
        elif key in ('d', 'D'):
            asyncio.create_task(self.disconnect())
        else:
            return super(ConsoleButton, self).keypress(size, key)


class ConsoleList(urwid.Frame):
    def __init__(self, app, consoles, header, footer):
        walker = urwid.SimpleFocusListWalker([])
        listbox = urwid.ListBox(walker)

        frame = urwid.Frame(listbox, header=urwid.Text(' {0:<20}{1:<20}{2:<20}{3:<20}'.format(
            'Name', 'IP Address', 'Live ID', 'Status'
        )))
        view = urwid.LineBox(frame, 'Consoles')

        self.walker = walker
        self.app = app
        self.consoles = consoles
        super(ConsoleList, self).__init__(view, header=header, footer=footer)
        self.walker[:] = [ConsoleButton(self.app, c) for c in self.consoles]

    async def refresh(self):
        await self._refresh()

    async def _refresh(self):
        discovered = await Console.discover(blocking=True)

        liveids = [d.liveid for d in discovered]
        for i, c in enumerate(self.consoles):
            if c.liveid in liveids:
                # Refresh existing entries
                idx = liveids.index(c.liveid)
                if c.device_status != discovered[idx].device_status:
                    self.consoles[i] = discovered[idx]
                del discovered[idx]
                del liveids[idx]
            elif c.liveid not in liveids:
                # Set unresponsive consoles to Unavailable
                self.consoles[i].device_status = DeviceStatus.Unavailable

        # Add newly discovered consoles
        self.consoles.extend(discovered)

        # Update the consolelist view
        self.walker[:] = [ConsoleButton(self.app, c) for c in self.consoles]

    def keypress(self, size, key):
        if key in ('r', 'R'):
            asyncio.create_task(self.refresh())
        else:
            return super(ConsoleList, self).keypress(size, key)


class CommandList(urwid.SimpleFocusListWalker):
    def __init__(self, app, console):
        commands = [
            ('Launch title', self._launch_title),
            ('Controller remote', self._controller_remote),
            ('Disconnect', self._disconnect),
            ('Power off', self._power_off)
        ]
        self.app = app
        self.console = console
        super(CommandList, self).__init__([CommandButton(text, func) for text, func in commands])

    def _launch_title(self):
        self.app.view_launch_title_textbox(self.__launch_title)

    def __launch_title(self, uri):
        asyncio.create_task(self.console.launch_title(uri))
        self.app.return_to_details_menu()

    def _controller_remote(self):
        self.app.view_controller_remote_overlay(self.console)

    def _disconnect(self):
        asyncio.create_task(self.console.disconnect())
        self.app.return_to_main_menu()

    def _power_off(self):
        asyncio.create_task(self.console.power_off())
        self.app.return_to_main_menu()


class CommandButton(urwid.Button):
    focus_map = {
        None: 'selected',
    }

    def __init__(self, text, func):
        super(CommandButton, self).__init__('')
        urwid.connect_signal(self, 'click', self.callback)
        self.text = text
        self.func = func
        self.textwidget = urwid.AttrWrap(urwid.SelectableIcon(' {}'.format(self.text), cursor_position=0), None)
        self._w = urwid.AttrMap(self.textwidget, None, self.focus_map)

    def callback(self, *args):
        self.func()


class UrwidLogHandler(logging.Handler):
    def __init__(self, callback):
        super(UrwidLogHandler, self).__init__()
        self.callback = callback

    def emit(self, record):
        try:
            self.callback(record)
        except Exception:
            self.handleError(record)


class LogListBox(urwid.ListBox):
    def __init__(self, app, size=10000):
        self.app = app
        self.size = size
        self.entries = urwid.SimpleFocusListWalker([])

        self.handler = UrwidLogHandler(self._log_callback)
        self.handler.setFormatter(app.log_fmt)
        logging.root.addHandler(self.handler)
        logging.root.setLevel(app.log_level)
        super(LogListBox, self).__init__(self.entries)

    def _log_callback(self, record):
        self.entries.append(LogButton(self.app, self.handler.format(record), record))
        if self.focus_position == len(self.entries) - 2:
            self.focus_position += 1

        if len(self.entries) > self.size:
            self.entries[:] = self.entries[len(self.entries) - self.size:]

    def keypress(self, size, key):
        # Prevents opening the log window multiple times
        if key in ('l', 'L'):
            pass
        else:
            return super(LogListBox, self).keypress(size, key)


class LogButton(urwid.Button):
    focus_map = {
        None: 'selected',
    }

    def __init__(self, app, text, record):
        super(LogButton, self).__init__('')
        self.app = app
        self.text = text
        self.record = record

        urwid.connect_signal(self, 'click', self._click)
        self.textwidget = urwid.AttrWrap(urwid.SelectableIcon(' {}'.format(self.text), cursor_position=0), None)
        self._w = urwid.AttrMap(self.textwidget, None, self.focus_map)

    def _click(self, *args):
        if hasattr(self.record, '_msg'):
            self.app.view_scrollable_overlay(repr(self.record._msg), "Message details", width=80)


class SGDisplay(object):
    palette = [
        ('header', 'yellow', 'dark blue', 'standout'),
        ('listbar', 'light cyan,bold', 'default'),
        ('selected', 'black', 'light gray'),

        # footer
        ('foot', 'dark cyan', 'dark blue', 'bold'),
        ('key', 'light cyan', 'dark blue', 'underline'),

        # status
        ('connected', 'dark green', ''),
        ('connected selected', 'black', 'dark green'),

        # progressbar
        ('pg normal', 'white', 'black', 'standout'),
        ('pg complete', 'white', 'dark magenta'),
        ('pg smooth', 'dark magenta', 'black'),

        ('caption', 'yellow,bold', 'dark cyan'),
        ('prompt', 'white', 'dark cyan'),
        ('dialog', 'white', 'dark cyan'),
        ('button', 'white', 'dark cyan'),
        ('button selected', 'white', 'dark cyan'),
    ]

    header_text = ('header', [
        "Xbox Smartglass"
    ])

    footer_main_text = ('foot', [
        ('key', 'R:'), "reload  ",
        ('key', 'C:'), "connect ",
        ('key', 'D:'), "disconnect ",
        ('key', 'P:'), "poweron ",
        ('key', 'L:'), "view log ",
        ('key', 'Q:'), "quit  "
    ])

    footer_console_text = ('foot', [
        ('key', 'C:'), "commands ",
        ('key', 'L:'), "view log ",
        ('key', 'Q:'), "quit "
    ])

    footer_log_text = ('foot', [
        ('key', 'ENTER:'), "show details ",
        ('key', 'Q:'), "quit "
    ])

    log_fmt = logging.Formatter(logging.BASIC_FORMAT)
    log_level = logging.DEBUG

    def __init__(self, consoles: List[Console], auth_mgr: AuthenticationManager):
        self.header = urwid.AttrMap(urwid.Text(self.header_text), 'header')
        footer = urwid.AttrMap(urwid.Text(self.footer_main_text), 'foot')

        self.running = False
        self.loop = None
        self.consoles = ConsoleList(self, consoles, self.header, footer)
        self.auth_mgr = auth_mgr
        self.log = LogListBox(self)

        self.view_stack = []

    def push_view(self, sender, view):
        self.view_stack.append(view)
        self.loop.widget = view
        self.loop.draw_screen()

    def pop_view(self, sender):
        if len(self.view_stack) > 1:
            top_widget = self.view_stack.pop()
            if hasattr(top_widget, 'close_view'):
                top_widget.close_view(sender)

            self.loop.widget = self.view_stack[-1]
            self.loop.draw_screen()
        else:
            self.do_quit()

    def view_main_menu(self):
        self.push_view(self, self.consoles)

    def view_details_menu(self, console):
        footer = urwid.AttrMap(urwid.Text(self.footer_console_text), 'foot')
        frame = ConsoleView(self, console, header=self.header, footer=footer)
        self.push_view(self, frame)

    def view_commands_menu(self, console):
        bottom = self.view_stack[-1]
        commands = urwid.ListBox(CommandList(self, console))
        top = urwid.LineBox(commands, 'Commands')
        overlay = urwid.Overlay(top, bottom, 'center', ('relative', 25), 'middle', ('relative', 75))
        self.push_view(self, overlay)

    def view_controller_remote_overlay(self, console):
        self.return_to_details_menu()
        bottom = self.view_stack[-1]
        edit = urwid.Edit('Press Q to quit\n'
                          'View: <tab>, Menu: <, Nexus: #\n'
                          'DPad: <Arrow keys>, Button: A-B-X-Y\n')
        view = ControllerRemote(self, console, edit)
        top = urwid.LineBox(view, title='Controller Remote')
        overlay = urwid.Overlay(top, bottom,
                                'center', ('relative', 25), 'middle', ('relative', 25))
        self.push_view(self, overlay)

    def view_text_input_overlay(self, console):
        self.return_to_details_menu()
        bottom = self.view_stack[-1]
        edit = urwid.Edit('Enter text\n'
                          'Press ENTER to send\n')
        view = TextInput(self, edit, console)
        top = urwid.LineBox(view, title='SystemText Session')
        overlay = urwid.Overlay(top, bottom,
                                'center', ('relative', 25), 'middle', ('relative', 25))
        self.push_view(self, overlay)

    def view_launch_title_textbox(self, callback):
        self.return_to_details_menu()
        bottom = self.view_stack[-1]
        edit = urwid.Edit('Press ENTER to send uri\n')
        question_box = QuestionBox(edit, callback)

        top = urwid.LineBox(question_box, title='Enter launch uri')
        overlay = urwid.Overlay(top, bottom,
                                'center', ('relative', 25), 'middle', ('relative', 25))
        self.push_view(self, overlay)

    def view_msgbox(self, msg, title='Error', width=25, height=75):
        bottom = self.view_stack[-1]
        text = urwid.Text(msg)
        button = urwid.Button('OK')
        button._label.align = 'center'
        pad_button = urwid.Padding(button, 'center', ('relative', width * 2))
        pile = urwid.Pile([text, pad_button])
        box = urwid.LineBox(pile, title)
        top = urwid.Filler(box, 'top')
        overlay = urwid.Overlay(top, bottom, 'center', ('relative', width), 'middle', ('relative', height))
        urwid.connect_signal(button, 'click', lambda _: self.pop_view(self))
        self.push_view(self, overlay)

    def view_scrollable_overlay(self, msg, title='Error', width=25, height=75):
        bottom = self.view_stack[-1]
        walker = urwid.SimpleFocusListWalker([urwid.Text(l) for l in msg.split('\n')])
        text = urwid.ListBox(walker)
        line = urwid.LineBox(text, title)
        overlay = urwid.Overlay(line, bottom, 'center', ('relative', width), 'middle', ('relative', height))
        self.push_view(self, overlay)

    def view_log(self):
        header = urwid.AttrMap(urwid.Text(self.header_text), 'header')
        footer = urwid.AttrMap(urwid.Text(self.footer_log_text), 'foot')
        frame = urwid.Frame(self.log, header=header, footer=footer)
        self.push_view(self, frame)

    def return_to_main_menu(self):
        while len(self.view_stack) > 1:
            self.pop_view(self)

    def return_to_details_menu(self):
        while len(self.view_stack) > 2:
            self.pop_view(self)

    def do_quit(self):
        self.running = False
        self.loop.stop()

    async def run(self, loop):
        eventloop = urwid.AsyncioEventLoop(loop=loop)
        self.loop = urwid.MainLoop(
            urwid.SolidFill('xq'),
            handle_mouse=False,
            palette=self.palette,
            unhandled_input=self.unhandled_input,
            event_loop=eventloop
        )
        self.loop.set_alarm_in(0.0001, lambda *args: self.view_main_menu())

        self.loop.start()
        self.running = True
        await self.consoles.refresh()

        while self.running:
            await asyncio.sleep(1000)

    def unhandled_input(self, input):
        if input in ('q', 'Q', 'esc'):
            self.pop_view(self)
        elif input in ('l', 'L'):
            self.view_log()

def load_consoles(filepath: str) -> List[Console]:
    try:
        with open(filepath, 'r') as fh:
            consoles = json.load(fh)
        return [Console.from_dict(c) for c in consoles]
    except FileNotFoundError:
        return []


def save_consoles(filepath: str, consoles: List[Console]) -> None:
    consoles = [c.to_dict() for c in consoles]
    with open(filepath, 'w') as fh:
        json.dump(consoles, fh, indent=2)


async def run_tui(
    loop: asyncio.AbstractEventLoop,
    consoles_filepath: str,
    auth_mgr: Optional[AuthenticationManager] = None
) -> int:
    """
    Main entrypoint for TUI

    Args:
        loop: Eventloop
        consoles_filepath: Console json filepath
        auth_mgr: Authentication manager

    Returns: Exit code
    """
    consoles = load_consoles(consoles_filepath) if consoles_filepath else []

    app = SGDisplay(consoles, auth_mgr)
    await app.run(loop)

    if consoles_filepath:
        save_consoles(consoles_filepath, app.consoles.consoles)

    return ExitCodes.OK