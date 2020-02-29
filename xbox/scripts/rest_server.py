from gevent import monkey
monkey.patch_all()
from gevent import pywsgi
from flask.logging import default_handler
from logging.handlers import RotatingFileHandler

import argparse
import logging
from xbox.rest.app import app
from xbox.rest.scripts import TOKENS_FILE

LOG_FMT = '[%(asctime)s] %(levelname)s: %(message)s'


def main():
    parser = argparse.ArgumentParser(description="Xbox One SmartGlass REST server")
    parser.add_argument('--address', '-a', default='0.0.0.0',
                        help='IP address to bind to')
    parser.add_argument('--port', '-p', default=5557,
                        help='Port to bind to')
    parser.add_argument('--tokens', '-t', default=TOKENS_FILE,
                        help='Tokenfile to load')
    parser.add_argument('--logfile', '-l',
                        help="Path for logfile")

    args = parser.parse_args()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(default_handler)

    if args.logfile:
        app.logger.info('Setting logfile path to {0}'.format(args.logfile))
        file_handler = RotatingFileHandler(args.logfile, backupCount=2)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FMT))
        root_logger.addHandler(file_handler)

    app.logger.info('Starting Xbox Smartglass REST server started on {0}:{1}'.format(
        args.address, args.port
    ))

    app.logger.debug('Setting tokenfile path to {0}'.format(args.tokens))
    app.token_file = args.tokens
    try:
        app.logger.info('Trying to load & refresh tokens')
        app.authentication_mgr.load(args.tokens)
        app.authentication_mgr.authenticate(do_refresh=True)
    except Exception as e:
        app.logger.warning(
            'Failed to authenticate with tokenfile from {0}, error: {1}'.format(args.tokens, e)
        )

    server = pywsgi.WSGIServer((args.address, args.port), app)
    server.serve_forever()

if __name__ == '__main__':
    main()
