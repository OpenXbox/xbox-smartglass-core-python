"""
Power on a console via LiveID

Requires the console to be in standby-mode
"""
import logging
import argparse

from xbox.sg.console import Console


def main():
    parser = argparse.ArgumentParser(description="Power on xbox one console")
    parser.add_argument('liveid',
                        help="Console Live ID")
    parser.add_argument('--address', '-a',
                        help="IP address of console")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    print('Waking up console \'%s\'' % args.liveid)
    Console.power_on(args.liveid, args.address, tries=10)


if __name__ == '__main__':
    main()
