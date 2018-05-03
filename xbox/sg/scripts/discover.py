"""
Discovers consoles on the network
"""
import logging
import argparse

from xbox.sg.console import Console


def main():
    parser = argparse.ArgumentParser(description="Discover consoles on the network")
    parser.add_argument('--address', '-a',
                        help="IP address of console")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    print("Discovering consoles...")
    discovered = Console.discover(timeout=1, addr=args.address)
    if len(discovered):
        print("Discovered %d consoles:" % len(discovered))
        for console in discovered:
            print("\t%s" % console)
    else:
        print("No consoles discovered!")


if __name__ == '__main__':
    main()
