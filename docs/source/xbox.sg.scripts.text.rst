Basic text input client
=======================

Send text input to console when a textfield is opened.

Usage:
::

    usage: xbox-text [-h] [--tokens TOKENS] [--address ADDRESS] [--refresh]

    Basic smartglass client

    optional arguments:
      -h, --help            show this help message and exit
      --tokens TOKENS, -t TOKENS
                            Token file, created by xbox-authenticate script
      --address ADDRESS, -a ADDRESS
                            IP address of console
      --refresh, -r         Refresh xbox live tokens in provided token file

Example:
::

    xbox-text
