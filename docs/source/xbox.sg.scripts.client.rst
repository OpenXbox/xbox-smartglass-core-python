Example Smartglass client
=========================

Bare client example. It just connects to the console, shows sent/received
packets and keeps the connection alive.

NOTE: It connects to the first console that's found!

Usage:
::

    usage: xbox-client [-h] [--tokens TOKENS] [--address ADDRESS] [--refresh]
                       [--verbose]

    Basic smartglass client

    optional arguments:
      -h, --help            show this help message and exit
      --tokens TOKENS, -t TOKENS
                            Token file, created by xbox-authenticate script
      --address ADDRESS, -a ADDRESS
                            IP address of console
      --refresh, -r         Refresh xbox live tokens in provided token file
      --verbose, -v         Verbose flag, also log message content

Example:
::

    xbox-client -v


Output:
::

    INFO:authentication:Loaded token <class 'xbox.webapi.authentication.token.AccessToken'> from file
    INFO:authentication:Loaded token <class 'xbox.webapi.authentication.token.RefreshToken'> from file
    INFO:authentication:Loaded token <class 'xbox.webapi.authentication.token.UserToken'> from file
    INFO:authentication:Loaded token <class 'xbox.webapi.authentication.token.XSTSToken'> from file
    DEBUG:xbox.sg.protocol:Received DiscoverResponse from 10.0.0.241
    DEBUG:xbox.sg.protocol:Received DiscoverResponse from 10.0.0.241
    DEBUG:xbox.sg.protocol:Sending ConnectRequest to 10.0.0.241
    DEBUG:xbox.sg.protocol:Sending ConnectRequest to 10.0.0.241
    DEBUG:xbox.sg.protocol:Sending ConnectRequest to 10.0.0.241
    DEBUG:xbox.sg.protocol:Received DiscoverResponse from 10.0.0.241
    DEBUG:xbox.sg.protocol:Received ConnectResponse from 10.0.0.241
    DEBUG:xbox.sg.protocol:Sending LocalJoin message on ServiceChannel Core to 10.0.0.241
    DEBUG:xbox.sg.protocol:Received Ack message on ServiceChannel Ack from 10.0.0.241
    DEBUG:xbox.sg.protocol:Sending StartChannelRequest message on ServiceChannel Core to 10.0.0.241
    DEBUG:xbox.sg.protocol:Received ConsoleStatus message on ServiceChannel Core from 10.0.0.241
    DEBUG:xbox.sg.protocol:Received Ack message on ServiceChannel Ack from 10.0.0.241
    DEBUG:xbox.sg.protocol:Sending StartChannelRequest message on ServiceChannel Core to 10.0.0.241
    DEBUG:xbox.sg.protocol:Received Ack message on ServiceChannel Ack from 10.0.0.241
    DEBUG:xbox.sg.protocol:Sending StartChannelRequest message on ServiceChannel Core to 10.0.0.241
    DEBUG:xbox.sg.protocol:Received Ack message on ServiceChannel Ack from 10.0.0.241
    DEBUG:xbox.sg.protocol:Sending StartChannelRequest message on ServiceChannel Core to 10.0.0.241
    DEBUG:xbox.sg.protocol:Received Ack message on ServiceChannel Ack from 10.0.0.241
    DEBUG:xbox.sg.protocol:Sending StartChannelRequest message on ServiceChannel Core to 10.0.0.241
    DEBUG:xbox.sg.protocol:Received Ack message on ServiceChannel Ack from 10.0.0.241
    DEBUG:xbox.sg.protocol:Received StartChannelResponse message on ServiceChannel Core from 10.0.0.241
    DEBUG:xbox.sg.protocol:Acquired ServiceChannel SystemInput -> Channel: 0x6
    DEBUG:xbox.sg.protocol:Received StartChannelResponse message on ServiceChannel Core from 10.0.0.241
    DEBUG:xbox.sg.protocol:Acquired ServiceChannel SystemInputTVRemote -> Channel: 0x7
    DEBUG:xbox.sg.protocol:Received StartChannelResponse message on ServiceChannel Core from 10.0.0.241
    DEBUG:xbox.sg.protocol:Acquired ServiceChannel SystemMedia -> Channel: 0x8
    DEBUG:xbox.sg.protocol:Received StartChannelResponse message on ServiceChannel Core from 10.0.0.241
    DEBUG:xbox.sg.protocol:Acquired ServiceChannel SystemText -> Channel: 0x9
    DEBUG:xbox.sg.protocol:Received StartChannelResponse message on ServiceChannel Core from 10.0.0.241
    DEBUG:xbox.sg.protocol:Acquired ServiceChannel SystemBroadcast -> Channel: 0xa
    DEBUG:xbox.sg.protocol:Received Json message on ServiceChannel SystemBroadcast from 10.0.0.241
    DEBUG:xbox.sg.protocol:Received Json message on ServiceChannel SystemBroadcast from 10.0.0.241
