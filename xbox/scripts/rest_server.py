import sys

from gevent import monkey
monkey.patch_all()

from xbox.scripts import main_cli  # noqa: E402


def main():
    print('Starting REST server from dedicated script')
    return sys.exit(main_cli.main('rest'))


if __name__ == '__main__':
    main()
