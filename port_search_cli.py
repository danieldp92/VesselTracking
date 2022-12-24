import argparse

from crawler import search_port
from utils import pretty_table


def args_config():
    parser = argparse.ArgumentParser(description='Port Search CLI')
    parser.add_argument('port_name', help='Name of the port to search')
    return parser.parse_args()


if __name__ == '__main__':
    args = args_config()

    if not args.port_name:
        print("No port name added.")
        raise SystemError(1)

    port = args.port_name
    ports = search_port(port)

    print()
    pretty_table(ports)