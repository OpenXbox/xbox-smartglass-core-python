import logging

from gevent import monkey
monkey.patch_all()
from gevent import pywsgi  # noqa: E402

from flask.logging import default_handler  # noqa: E402

from xbox.rest.app import app  # noqa: E402
from xbox.scripts import main_cli  # noqa: E402

LOGGER = logging.getLogger(__name__)

REST_DEFAULT_SERVER_PORT = 5557


def main():
    args = main_cli.parse_arguments()
    main_cli.handle_logging_setup(args)

    LOGGER.addHandler(default_handler)

    if args.port == 0:
        LOGGER.info('No defaults provided, '
                    'Setting REST server port to {0}'.format(REST_DEFAULT_SERVER_PORT))
        args.port = REST_DEFAULT_SERVER_PORT

    print('Xbox Smartglass REST server started on {0}:{1}'.format(
        args.address, args.port
    ))

    server = pywsgi.WSGIServer((args.bind, args.port), app)
    server.serve_forever()


if __name__ == '__main__':
    main()
