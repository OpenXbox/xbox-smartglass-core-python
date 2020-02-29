"""
Text smartglass client
"""
import sys
import logging
import argparse
import functools

import gevent.socket
from gevent import signal

from xbox.scripts import TOKENS_FILE

from xbox.webapi.authentication.manager import AuthenticationManager

from xbox.sg.console import Console
from xbox.sg.enum import ConnectionState
from xbox.sg.manager import TextManager


def on_text_config(payload):
    pass


def on_text_input(console, payload):
    print(
        "\n\nWAITING FOR TEXT INPUT - "
        "SHELL WILL KEEP SCROLLING\n"
        "Prompt: %s\n" % console.text.text_prompt
    )
    gevent.socket.wait_read(sys.stdin.fileno())
    text = input()
    console.send_systemtext_input(text)
    console.finish_text_input()


def on_text_done(payload):
    pass


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
        console.add_manager(TextManager)
        console.text.on_systemtext_configuration += on_text_config
        console.text.on_systemtext_input += functools.partial(on_text_input, console)
        console.text.on_systemtext_done += on_text_done
        state = console.connect(userhash, token)
        if state != ConnectionState.Connected:
            print("Connection failed")
            sys.exit(1)
        console.wait(1)

        signal.signal(signal.SIGINT, lambda *args: console.protocol.stop())
        console.protocol.serve_forever()
    else:
        print("No consoles discovered")
        sys.exit(1)


if __name__ == '__main__':
    main()
