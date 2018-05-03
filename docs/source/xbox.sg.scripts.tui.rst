Basic text user interface
=========================

Text user interface, based on curses / urwid.
Allows discovery, power-on, power-off, connecting and disconnecting of console.

It also supports entering Text when console requests it from client.
Gamepad input can be sent via keyboard.
Titles can be launched via URI.

Usage:
::

    usage: xbox-tui [-h] [--tokens TOKENS] [--consoles CONSOLES]

    Basic text user interface

    optional arguments:
      -h, --help            show this help message and exit
      --tokens TOKENS, -t TOKENS
                            Token file, created by xbox-authenticate script
      --consoles CONSOLES, -c CONSOLES
                            Previously discovered consoles

Example:
::

    xbox-tui
