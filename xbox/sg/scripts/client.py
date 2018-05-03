"""
Basic smartglass client

It opens an authenticated connection to the console
and receives and acknowledges packets
"""
import sys
import logging
import argparse

from gevent import signal

from xbox.webapi.authentication.manager import AuthenticationManager

from xbox.sg.console import Console
from xbox.sg.enum import ConnectionState
from xbox.sg.scripts import TOKENS_FILE


class VerboseFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super(VerboseFormatter, self).__init__(*args, **kwargs)
        self._verbosefmt = self._fmt + '\n%(_msg)s'

    def formatMessage(self, record):
        if '_msg' in record.__dict__:
            return self._verbosefmt % record.__dict__
        return self._style.format(record)


def on_timeout():
    logging.info('Connection Timeout')
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Basic smartglass client")
    parser.add_argument('--tokens', '-t', default=TOKENS_FILE,
                        help="Token file, created by xbox-authenticate script")
    parser.add_argument('--address', '-a',
                        help="IP address of console")
    parser.add_argument('--refresh', '-r', action='store_true',
                        help="Refresh xbox live tokens in provided token file")
    parser.add_argument('--verbose', '-v', action='store_true',
                        help="Verbose flag, also log message content")

    args = parser.parse_args()

    if args.verbose:
        fmt = VerboseFormatter(logging.BASIC_FORMAT)
    else:
        fmt = logging.Formatter(logging.BASIC_FORMAT)

    handler = logging.StreamHandler()
    handler.setFormatter(fmt)
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.DEBUG)

    # logging.basicConfig(level=logging.DEBUG, format=logfmt)

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
        state = console.connect(userhash, token)
        if state != ConnectionState.Connected:
            logging.error("Connection failed")
            sys.exit(1)

        signal.signal(signal.SIGINT, lambda *args: console.protocol.stop())
        console.protocol.serve_forever()
    else:
        logging.error("No consoles discovered")
        sys.exit(1)


if __name__ == '__main__':
    main()
