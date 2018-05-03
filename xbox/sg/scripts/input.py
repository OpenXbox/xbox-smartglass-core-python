"""
Input smartglass client

Send controller input via stdin (terminal) to the console
"""
import sys
import logging
import argparse

import gevent.socket
from gevent import signal

from xbox.webapi.authentication.manager import AuthenticationManager

from xbox.sg.console import Console
from xbox.sg.enum import ConnectionState, GamePadButton
from xbox.sg.manager import InputManager
from xbox.sg.scripts import TOKENS_FILE

input_map = {
    "i": GamePadButton.DPadUp,
    "k": GamePadButton.DPadDown,
    "j": GamePadButton.DPadLeft,
    "l": GamePadButton.DPadRight,

    "a": GamePadButton.PadA,
    "b": GamePadButton.PadB,
    "x": GamePadButton.PadX,
    "y": GamePadButton.PadY,

    "t": GamePadButton.View,
    "z": GamePadButton.Nexu,
    "u": GamePadButton.Menu
}


def get_getch_func():
    """
    Source: https://code.activestate.com/recipes/577977-get-single-keypress/
    """
    try:
        import tty
        import termios
    except ImportError:
        # Probably Windows.
        try:
            import msvcrt
        except ImportError:
            # Just give up here.
            raise ImportError('getch not available')
        else:
            return msvcrt.getch
    else:
        def getch():
            """
            getch() -> key character

            Read a single keypress from stdin and return the resulting character.
            Nothing is echoed to the console. This call will block if a keypress
            is not already available, but will not wait for Enter to be pressed.

            If the pressed key was a modifier key, nothing will be detected; if
            it were a special function key, it may return the first character of
            of an escape sequence, leaving additional characters in the buffer.
            """
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                gevent.socket.wait_read(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
        return getch


def on_timeout():
    print('Connection Timeout')
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Basic smartglass client")
    parser.add_argument('--tokens', '-t', default=TOKENS_FILE,
                        help="Token file, created by xbox-authenticate script")
    parser.add_argument('--address', '-a',
                        help="IP address of console")
    parser.add_argument('--refresh', '-r', action='store_true',
                        help="Refresh xbox live tokens in provided token file")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    try:
        auth_mgr = AuthenticationManager.from_file(args.tokens)
        auth_mgr.authenticate(do_refresh=args.refresh)
        auth_mgr.dump(args.tokens)
    except Exception as e:
        print("Failed to authenticate with provided tokens, Error: %s" % e)
        print("Please re-run xbox-authenticate to get a fresh set")
        sys.exit(1)

    userhash = auth_mgr.userinfo.userhash
    token = auth_mgr.xsts_token.jwt
    discovered = Console.discover(timeout=1, addr=args.address)
    if len(discovered):
        console = discovered[0]
        console.on_timeout += on_timeout
        console.add_manager(InputManager)
        state = console.connect(userhash, token)
        if state != ConnectionState.Connected:
            print("Connection failed")
            sys.exit(1)
        console.wait(1)

        getch = get_getch_func()
        while True:
            ch = getch()
            print(ch)
            if ord(ch) == 3:  # CTRL-C
                sys.exit(1)

            elif ch not in input_map:
                continue

            button = input_map[ch]
            console.gamepad_input(button)
            console.wait(0.1)
            console.gamepad_input(GamePadButton.Clear)

        signal.signal(signal.SIGINT, lambda *args: console.protocol.stop())
        console.protocol.serve_forever()
    else:
        print("No consoles discovered")
        sys.exit(1)


if __name__ == '__main__':
    main()
