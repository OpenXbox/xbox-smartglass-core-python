Power off console
=================

Power off either a specific, active console or every console that can be found

Usage:
::

    usage: xbox-poweroff [-h] [--tokens TOKENS] [--liveid LIVEID]
                         [--address ADDRESS] [--all] [--refresh]

    Power off xbox one console

    optional arguments:
      -h, --help            show this help message and exit
      --tokens TOKENS, -t TOKENS
                            Token file, created by xbox-authenticate script
      --liveid LIVEID, -l LIVEID
                            Console Live ID
      --address ADDRESS, -a ADDRESS
                            IP address of console
      --all                 Power off all consoles
      --refresh, -r         Refresh xbox live tokens in provided token file

Example:
::

    # By Live ID
    xbox-poweroff --liveid FD00231241353532

    # By IP Address
    xbox-poweroff --address 10.0.0.241

    # Every console that can be found
    xbox-poweroff --all
