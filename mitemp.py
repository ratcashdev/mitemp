#!/usr/bin/env python3
"""Demo file showing how to use the mitemp library."""

import argparse
import re
import logging
import sys

from btlewrap import available_backends, BluepyBackend, GatttoolBackend, PygattBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, \
    MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY


def valid_mitemp_mac(mac, pat=re.compile(r"58:2D:34:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}")):
#def valid_mitemp_mac(mac, pat=re.compile(r"4C:65:A8:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}")):
    """Check for valid mac adresses."""
    if not pat.match(mac.upper()):
        raise argparse.ArgumentTypeError('The MAC address "{}" seems to be in the wrong format'.format(mac))
    return mac


def poll(args):
    """Poll data from the sensor."""
    backend = _get_backend(args)
    for mac in args.macs:
        poller = MiTempBtPoller(mac, backend)

        if args.devinfo == True:
            print('{}->{{"name":"{}","fw":"{}","battery":{}}}'
                .format(
                    mac,
                    poller.name(),
                    poller.firmware_version(),
                    poller.parameter_value(MI_BATTERY)))
        else:
            s = '{}->{{"measurements":[{{"name":"temperature","value":{},"units":"℃"}},{{"name":"humidity","value":{},"units":"%"}}]}}' \
                .format(
                    mac,
                    poller.parameter_value(MI_TEMPERATURE),
                    poller.parameter_value(MI_HUMIDITY))
            print(s)

def _get_backend(args):
    """Extract the backend class from the command line arguments."""
    if args.backend == 'gatttool':
        backend = GatttoolBackend
    elif args.backend == 'bluepy':
        backend = BluepyBackend
    elif args.backend == 'pygatt':
        backend = PygattBackend
    else:
        raise Exception('unknown backend: {}'.format(args.backend))
    return backend


def list_backends(_):
    """List all available backends."""
    backends = [b.__name__ for b in available_backends()]
    print('\n'.join(backends))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backend', choices=['gatttool', 'bluepy', 'pygatt'], default='gatttool')
    parser.add_argument('-d', '--devinfo', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_const', const=True)
    subparsers = parser.add_subparsers(help='sub-command help', )

    parser_poll = subparsers.add_parser('poll', help='poll data from a sensor')
    parser_poll.add_argument('macs', type=valid_mitemp_mac, nargs="*")
    parser_poll.set_defaults(func=poll)

    parser_scan = subparsers.add_parser('backends', help='list the available backends')
    parser_scan.set_defaults(func=list_backends)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == '__main__':
    main()

