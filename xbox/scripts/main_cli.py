"""
Main smartglass client

Common script that handles several subcommands
See `Commands`
"""
import sys
import logging
import argparse
import functools

from logging.handlers import RotatingFileHandler
from code import InteractiveConsole

from gevent import signal, backdoor

from xbox.scripts import TOKENS_FILE, CONSOLES_FILE, LOG_FMT, \
    LOG_LEVEL_DEBUG_INCL_PACKETS, VerboseFormatter, ExitCodes

from xbox.handlers import tui, gamepad_input, text_input, fallout4_relay
from xbox.auxiliary.manager import TitleManager

from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.common.exceptions import AuthenticationException

from xbox.sg import manager
from xbox.sg.console import Console
from xbox.sg.enum import ConnectionState

# REST server imports
from gevent import pywsgi as rest_pywsgi
from xbox.rest.app import app as flask_app


LOGGER = logging.getLogger(__name__)

REST_DEFAULT_SERVER_PORT = 5557
REPL_DEFAULT_SERVER_PORT = 5558


class Commands(object):
    """
    Available commands for CLI
    """
    Discover = 'discover'
    PowerOn = 'poweron'
    PowerOff = 'poweroff'
    REPL = 'repl'
    REPLServer = 'replserver'
    FalloutRelay = 'forelay'
    GamepadInput = 'gamepadinput'
    TextInput = 'textinput'
    TUI = 'tui'
    RESTServer = 'rest'


def parse_arguments(args=None):
    """
    Parse arguments with argparse.ArgumentParser

    Returns:
        Namespace: Parsed arguments

    Raises:
        Exception: On generic failure
    """

    parser = argparse.ArgumentParser(description='Xbox SmartGlass client')

    """Common arguments for logging"""
    logging_args = argparse.ArgumentParser(add_help=False)
    logging_args.add_argument(
        '--logfile',
        help="Path for logfile")
    logging_args.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Set logging level\n'
             '(  -v: INFO,\n'
             ' -vv: DEBUG,\n'
             '-vvv: DEBUG_INCL_PACKETS)')

    """Common arguments for authenticated console connection"""
    xbl_token_args = argparse.ArgumentParser(add_help=False)
    xbl_token_args.add_argument(
        '--tokens', '-t', type=str, default=TOKENS_FILE,
        help='Tokenfile to load')
    xbl_token_args.add_argument(
        '--refresh', '-r', action='store_true',
        help="Refresh xbox live tokens in provided token file")

    """Common argument for console connection"""
    connection_arg = argparse.ArgumentParser(add_help=False)
    connection_arg.add_argument(
        '--address', '-a', type=str, default=None,
        help="IP address of console")
    connection_arg.add_argument(
        '--liveid', '-l',
        help='LiveID to poweron')

    server_args = argparse.ArgumentParser(add_help=False)
    server_args.add_argument(
        '--bind', '-b', default='127.0.0.1',
        help='Interface address to bind the server')
    server_args.add_argument(
        '--port', '-p', type=int, default=0,
        help='Port to bind to, defaults: (REST: 5557, REPL: 5558)')

    """Common argument for interactively choosing console to handle"""
    interactive_arg = argparse.ArgumentParser(add_help=False)
    interactive_arg.add_argument(
        '--interactive', '-i', action='store_true',
        help="Interactively choose console to connect to")

    """
    Define commands
    """
    subparsers = parser.add_subparsers(
        help='Available commands', dest='command', required=True)
    """Discover"""
    subparsers.add_parser(Commands.Discover,
                          help='Discover console',
                          parents=[logging_args,
                                   connection_arg])

    """Power on"""
    subparsers.add_parser(
        Commands.PowerOn,
        help='Power on console',
        parents=[logging_args, connection_arg])

    """Power off"""
    poweroff_cmd = subparsers.add_parser(
        Commands.PowerOff,
        help='Power off console',
        parents=[logging_args, xbl_token_args,
                 interactive_arg, connection_arg])
    poweroff_cmd.add_argument(
        '--all', action='store_true',
        help="Power off all consoles")

    """Local REPL"""
    subparsers.add_parser(
        Commands.REPL,
        help='Local REPL (interactive console)',
        parents=[logging_args, xbl_token_args,
                 interactive_arg, connection_arg])

    """REPL server"""
    subparsers.add_parser(
        Commands.REPLServer,
        help='REPL server (interactive console)',
        parents=[logging_args, xbl_token_args,
                 interactive_arg, connection_arg,
                 server_args])

    """Fallout relay"""
    subparsers.add_parser(
        Commands.FalloutRelay,
        help='Fallout 4 Pip boy relay',
        parents=[logging_args, xbl_token_args,
                 interactive_arg, connection_arg])

    """Controller input"""
    subparsers.add_parser(
        Commands.GamepadInput,
        help='Send controller input to dashboard / apps',
        parents=[logging_args, xbl_token_args,
                 interactive_arg, connection_arg])

    """Text input"""
    subparsers.add_parser(
        Commands.TextInput,
        help='Client to use Text input functionality',
        parents=[logging_args, xbl_token_args,
                 interactive_arg, connection_arg])

    tui_cmd = subparsers.add_parser(
        Commands.TUI,
        help='TUI client - fancy :)',
        parents=[logging_args, xbl_token_args,
                 connection_arg])
    tui_cmd.add_argument(
        '--consoles', '-c', default=CONSOLES_FILE,
        help="Previously discovered consoles (json)")

    # FIXME: If possible include startup for REST server here too
    """
    REST server
    NOTE: Only argument parsing is handled in here,
          The actual start code is in a dedicated script.

          This is required due to gevent monkey patching for
          the FLASK web-framework to work.
    """
    subparsers.add_parser(
        Commands.RESTServer,
        help='REST server',
        parents=[logging_args, xbl_token_args, server_args])

    return parser.parse_args(args)


def handle_logging_setup(args):
    """
    Determine log level, logfile and special DEBUG_INCL_PACKETS
    via cmdline arguments.

    Args:
        args: ArgumentParser `Namespace`

    Returns:
         None
    """
    levels = [logging.WARNING, logging.INFO, logging.DEBUG, LOG_LEVEL_DEBUG_INCL_PACKETS]
    # Output level capped to number of levels
    log_level = levels[min(len(levels) - 1, args.verbose)]
    logging.basicConfig(level=log_level, format=LOG_FMT)
    logging.root.info('Set Loglevel: {0}'
                      .format(logging.getLevelName(log_level)))

    if log_level == LOG_LEVEL_DEBUG_INCL_PACKETS:
        logging.root.info('Removing previous logging StreamHandlers')
        while len(logging.root.handlers):
            del logging.root.handlers[0]

        logging.root.info('Using DEBUG_INCL_PACKETS logging')
        debugext_handler = logging.StreamHandler()
        debugext_handler.setFormatter(VerboseFormatter(LOG_FMT))
        logging.root.addHandler(debugext_handler)

    if args.logfile:
        logging.root.info('Set Logfile path: {0}'.format(args.logfile))
        file_handler = RotatingFileHandler(args.logfile, backupCount=2)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FMT))
        logging.root.addHandler(file_handler)


def do_authentication(token_filepath, do_refresh):
    """
    Shortcut for doing xbox live authentication (uses xbox-webapi-python lib).

    Args:
        token_filepath (str): Token filepath
        do_refresh (bool): Whether to refresh tokens

    Returns:
        AuthenticationManager: An authenticated instance

    Raises:
        AuthenticationException: If authentication failed
    """
    auth_mgr = AuthenticationManager.from_file(token_filepath)
    auth_mgr.authenticate(do_refresh=do_refresh)
    if do_refresh:
        auth_mgr.dump(token_filepath)

    return auth_mgr


def choose_console_interactively(console_list):
    """
    Choose a console to use via user-input

    Args:
        console_list (list): List of consoles to choose from

    Returns:
        None if choice was aborted, a desired console object otherwise
    """
    entry_count = len(console_list)
    LOGGER.debug('Offering console choices: {0}'.format(entry_count))

    print('Discovered consoles:')
    for idx, console in enumerate(console_list):
        print('  {0}: {1} {2} {3}'
              .format(idx, console.name, console.liveid, console.address))

    print('Enter \'x\' to abort')

    choices = [str(i) for i in range(entry_count)]
    choices.append('e')

    response = ''
    while response not in choices:
        response = input('Make your choice: ')
        if response == 'e':
            return None

    return console_list[int(response)]


def cli_discover_consoles(args):
    """
    Discover consoles
    """
    LOGGER.info('Sending discovery packets to IP: {0}'
                .format('IP: ' + args.address if args.address else '<MULTICAST>'))
    discovered = Console.discover(addr=args.address, timeout=1)

    if not len(discovered):
        LOGGER.error('No consoles discovered')
        sys.exit(ExitCodes.DiscoveryError)

    LOGGER.info('Discovered consoles ({0}): {1}'
                .format(len(discovered), ', '.join([str(c) for c in discovered])))

    if args.liveid:
        LOGGER.info('Filtering discovered consoles for LIVEID: {0}'
                    .format(args.liveid))
        discovered = [c for c in discovered if c.liveid == args.liveid]
    if args.address:
        LOGGER.info('Filtering discovered consoles for IP address: {0}'
                    .format(args.address))
        discovered = [c for c in discovered if c.address == args.address]

    return discovered


def main(command=None):
    """
    Main entrypoint
    """
    auth_manager = None
    repl_server_handle = None  # Used for Command.REPLServer

    if command:
        # Take passed command and append actual cmdline
        cmdline_arguments = sys.argv[1:]
        cmdline_arguments.insert(0, command)
    else:
        cmdline_arguments = None

    args = parse_arguments(cmdline_arguments)
    handle_logging_setup(args)

    LOGGER.debug('Parsed arguments: {0}'.format(args))

    command = args.command
    LOGGER.debug('Chosen command: {0}'.format(command))

    if command == Commands.RESTServer:
        LOGGER.info('Make sure you used the dedicated \'xbox-rest-server\' script'
                    ' to start the REST server!')

    elif 'interactive' in args and args.interactive and \
         (args.address or args.liveid):
        LOGGER.error('Flag \'--interactive\' is incompatible with'
                     ' providing an IP address (--address) or LiveID (--liveid) explicitly')
        sys.exit(ExitCodes.ArgParsingError)
    elif args.liveid and args.address:
        LOGGER.warning('You passed --address AND --liveid: Will only use that specific'
                       'combination!')
    elif command == Commands.PowerOff and args.all and (args.liveid or args.address):
        LOGGER.error('Poweroff with --all flag + explicitly provided LiveID / IP address makes no sense')
        sys.exit(ExitCodes.ArgParsingError)
    elif command == Commands.PowerOff and args.interactive and args.all:
        LOGGER.error('Combining args --all and --interactive not supported')
        sys.exit(ExitCodes.ArgParsingError)

    print('Xbox SmartGlass main client started')

    if command == Commands.RESTServer:
        """
        REST Server
        """

        if args.port == 0:
            LOGGER.info('No defaults provided, '
                        'Setting REST server port to {0}'.format(REST_DEFAULT_SERVER_PORT))
            args.port = REST_DEFAULT_SERVER_PORT

        print('Xbox Smartglass REST server started on {0}:{1}'.format(
            args.bind, args.port
        ))

        server = rest_pywsgi.WSGIServer((args.bind, args.port), flask_app)
        server.serve_forever()
        sys.exit(ExitCodes.OK)
    elif command == Commands.TUI:
        """
        Text user interface (powered by urwid)
        """
        # Removing stream handlers to not pollute TUI
        for h in [sh for sh in logging.root.handlers
                  if isinstance(sh, logging.StreamHandler)]:
            LOGGER.debug('Removing StreamHandler {0} from root logger'.format(h))
            logging.root.removeHandler(h)

        sys.exit(tui.run_tui(args.consoles, args.address,
                             args.liveid, args.tokens, args.refresh))

    elif 'tokens' in args:
        """
        Do Xbox live authentication
        """
        LOGGER.debug('Command {0} supports authenticated connection'.format(command))
        try:
            auth_manager = do_authentication(args.tokens, args.refresh)
        except AuthenticationException:
            LOGGER.exception('Authentication failed!')
            LOGGER.error("Please re-run xbox-authenticate to get a fresh set")
            sys.exit(ExitCodes.AuthenticationError)

    elif command == Commands.PowerOn:
        """
        Powering up console
        """
        if not args.liveid:
            LOGGER.error('No LiveID (--liveid) provided for power on!')
            sys.exit(ExitCodes.ArgParsingError)

        LOGGER.info('Sending poweron packet for LiveId: {0} to {1}'
                    .format(args.liveid,
                            'IP: ' + args.address if args.address else '<MULTICAST>'))
        Console.power_on(args.liveid, args.address, tries=10)
        sys.exit(0)

    """
    Discovery
    """
    discovered = cli_discover_consoles(args)

    if command == Commands.Discover:
        """
        Simply print discovered consoles
        """
        print("Discovered %d consoles: " % len(discovered))
        for console in discovered:
            print("  %s" % console)
        sys.exit(ExitCodes.OK)

    elif command == Commands.PowerOff and args.all:
        """
        Early call for poweroff --all
        """
        """Powering off all discovered consoles"""
        for c in discovered:
            print('Powering off console {0}'.format(c))
            c.power_off()
        sys.exit(ExitCodes.OK)

    """
    Choosing/filtering a console from the discovered ones
    """
    console = None
    if args.interactive:
        LOGGER.debug('Starting interactive console choice')
        console = choose_console_interactively(discovered)
    elif len(discovered) == 1:
        LOGGER.debug('Choosing sole console, no user interaction required')
        console = discovered[0]
    elif len(discovered) > 1:
        LOGGER.error(
            'More than one console was discovered and no exact'
            ' connection parameters were provided')

    if not console:
        LOGGER.error('Choosing a console failed!')
        sys.exit(ExitCodes.ConsoleChoice)

    LOGGER.info('Choosen target console: {0}'.format(console))

    LOGGER.debug('Setting console callbacks')
    console.on_device_status += \
        lambda x: LOGGER.info('Device status: {0}'.format(x))
    console.on_connection_state += \
        lambda x: LOGGER.info('Connection state: {0}'.format(x))
    console.on_pairing_state += \
        lambda x: LOGGER.info('Pairing state: {0}'.format(x))
    console.on_console_status += \
        lambda x: LOGGER.info('Console status: {0}'.format(x))
    console.on_timeout += \
        lambda x: LOGGER.error('Timeout occured!') or sys.exit(1)

    userhash = auth_manager.userinfo.userhash
    xtoken = auth_manager.xsts_token

    LOGGER.debug('Authentication info:')
    LOGGER.debug('Userhash: {0}'.format(userhash))
    LOGGER.debug('XToken: {0}'.format(xtoken))

    LOGGER.info('Attempting connection...')
    state = console.connect(userhash, xtoken.jwt)
    if state != ConnectionState.Connected:
        LOGGER.error('Connection failed! Console: {0}'.format(console))
        sys.exit(1)

    # FIXME: Waiting explicitly
    LOGGER.info('Connected to console: {0}'.format(console))
    LOGGER.debug('Waiting a second before proceeding...')
    console.wait(1)

    if command == Commands.PowerOff:
        """
        Power off (single console)
        """
        print('Powering off console {0}'.format(console))
        console.power_off()
        sys.exit(ExitCodes.OK)

    elif command == Commands.REPL or \
            command == Commands.REPLServer:

        banner = 'You are connected to the console @ {0}\n'\
                 .format(console.address)
        banner += 'Type in \'console\' to acccess the object\n'
        banner += 'Type in \'exit()\' to quit the application'

        scope_vars = {'console': console}

        if command == Commands.REPL:
            LOGGER.info('Starting up local REPL console')
            repl_local = InteractiveConsole(locals=scope_vars)
            repl_local.interact(banner)
        else:

            if args.port == 0:
                LOGGER.info('No defaults provided, '
                            'Setting REPL server port to {0}'.format(REPL_DEFAULT_SERVER_PORT))
                args.port = REPL_DEFAULT_SERVER_PORT

            startinfo = 'Starting up REPL server @ {0}:{1}'.format(args.bind, args.port)
            print(startinfo)
            LOGGER.info(startinfo)

            repl_server_handle = backdoor.BackdoorServer(
                listener=(args.bind, args.port),
                banner=banner,
                locals=scope_vars)

    elif command == Commands.FalloutRelay:
        """
        Fallout 4 relay
        """
        print('Starting Fallout 4 relay service...')
        console.add_manager(TitleManager)
        console.title.on_connection_info += fallout4_relay.on_connection_info
        console.start_title_channel(title_id=fallout4_relay.FALLOUT_TITLE_ID)
        print('Fallout 4 relay started')
    elif command == Commands.GamepadInput:
        """
        Gamepad input
        """
        print('Starting gamepad input handler...')
        console.add_manager(manager.InputManager)
        gamepad_input.input_loop(console)
    elif command == Commands.TextInput:
        """
        Text input
        """
        print('Starting text input handler...')
        console.add_manager(manager.TextManager)
        console.text.on_systemtext_configuration += text_input.on_text_config
        console.text.on_systemtext_input += functools.partial(text_input.on_text_input, console)
        console.text.on_systemtext_done += text_input.on_text_done

    LOGGER.debug('Installing gevent SIGINT handler')
    signal.signal(signal.SIGINT, lambda *a: console.protocol.stop())

    if repl_server_handle:
        LOGGER.debug('Starting REPL server protocol')

    LOGGER.debug('Starting console.protocol.serve_forever()')
    console.protocol.serve_forever()

    LOGGER.debug('Protocol serving exited')
    if repl_server_handle:
        LOGGER.debug('Stopping REPL server protocol')
        repl_server_handle.stop()


def main_discover():
    """Entrypoint for discover script"""
    main(Commands.Discover)


def main_poweron():
    """Entrypoint for poweron script"""
    main(Commands.PowerOn)


def main_poweroff():
    """Entrypoint for poweroff script"""
    main(Commands.PowerOff)


def main_repl():
    """Entrypoint for REPL script"""
    main(Commands.REPL)


def main_replserver():
    """Entrypoint for REPL server script"""
    main(Commands.REPLServer)


def main_falloutrelay():
    """Entrypoint for Fallout 4 relay script"""
    main(Commands.FalloutRelay)


def main_textinput():
    """Entrypoint for Text input script"""
    main(Commands.TextInput)


def main_gamepadinput():
    """Entrypoint for Gamepad input script"""
    main(Commands.GamepadInput)


def main_tui():
    """Entrypoint for TUI script"""
    main(Commands.TUI)


if __name__ == '__main__':
    main()
