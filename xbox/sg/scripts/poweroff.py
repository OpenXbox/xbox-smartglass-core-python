"""
Powers off xbox one console

You can either poweroff the console by providing LiveID,
IP address or a switch to poweroff all found consoles.
"""
import sys
import logging
import argparse

from xbox.webapi.authentication.manager import AuthenticationManager

from xbox.sg.console import Console
from xbox.sg.enum import ConnectionState
from xbox.sg.scripts import TOKENS_FILE


def main():
    parser = argparse.ArgumentParser(description="Power off xbox one console")
    parser.add_argument('--tokens', '-t', default=TOKENS_FILE,
                        help="Token file, created by xbox-authenticate script")
    parser.add_argument('--liveid', '-l',
                        help="Console Live ID")
    parser.add_argument('--address', '-a',
                        help="IP address of console")
    parser.add_argument('--all', action='store_true',
                        help="Power off all consoles")
    parser.add_argument('--refresh', '-r', action='store_true',
                        help="Refresh xbox live tokens in provided token file")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

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

    if not args.liveid and not args.address and not args.all:
        print("No arguments supplied!")
        parser.print_help()
        sys.exit(1)

    consoles = Console.discover(timeout=1, addr=args.address)
    if not len(consoles):
        print("No consoles found!")
        sys.exit(1)

    if not args.all and args.liveid:
        consoles = [c for c in consoles if c.liveid == args.liveid]
    if not args.all and args.address:
        consoles = [c for c in consoles if c.address == args.address]

    for c in consoles:
        state = c.connect(userhash, token)
        if state != ConnectionState.Connected:
            print("Connecting to %s failed" % c)
            continue
        c.wait(1)
        print("Shutting down %s ..." % c)
        c.power_off()


if __name__ == '__main__':
    main()
