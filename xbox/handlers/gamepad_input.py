"""
Input smartglass client

Send controller input via stdin (terminal) to the console
"""
import sys
import logging

from xbox.sg.enum import GamePadButton

LOGGER = logging.getLogger(__name__)

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
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
        return getch


async def input_loop(console):
    getch = get_getch_func()
    while True:
        ch = getch()
        print(ch)
        if ord(ch) == 3:  # CTRL-C
            sys.exit(1)

        elif ch not in input_map:
            continue

        button = input_map[ch]
        await console.gamepad_input(button)
        await console.wait(0.1)
        await console.gamepad_input(GamePadButton.Clear)
