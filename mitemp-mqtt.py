#!/usr/bin/env python3

import argparse
import re
import paho.mqtt.client as mqtt

from btlewrap import available_backends, BluepyBackend, GatttoolBackend, PygattBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, \
    MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY

def valid_mitemp_mac(mac, pat=re.compile(r"58:2D:34:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}")):
#def valid_mitemp_mac(mac, pat=re.compile(r"4C:65:A8:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}")):
    """Check for valid mac adresses."""
    if not pat.match(mac.upper()):
        raise argparse.ArgumentTypeError('The MAC address "{}" seems to be in the wrong format'.format(mac))
    return mac

def mac_to_eui64(mac):
    if valid_mitemp_mac(mac):
        eui64 = re.sub(r'[.:-]', '', mac).lower()
        eui64 = eui64[0:6] + 'fffe' + eui64[6:]
        eui64 = hex(int(eui64[0:2], 16) ^ 2)[2:].zfill(2) + eui64[2:]
        return eui64
    return None

def get_backend(args):
    """Extract the backend class from the command line arguments."""
    if args.backend == 'gatttool':
        backend = GatttoolBackend
    # elif args.backend == 'bluepy':
    #     backend = BluepyBackend
    elif args.backend == 'pygatt':
        backend = PygattBackend
    else:
        raise Exception('unknown backend: {}'.format(args.backend))
    return backend


def list_backends(_):
    """List all available backends."""
    backends = [b.__name__ for b in available_backends()]
    print('\n'.join(backends))

parser = argparse.ArgumentParser()

parser.add_argument('macs', type=valid_mitemp_mac, nargs="*")
parser.add_argument('-b', '--backend', choices=['gatttool', 'bluepy', 'pygatt'], default='gatttool')
parser.add_argument('-d', '--devinfo', action='store_true')
parser.add_argument('-e', '--health', action='store_true')
parser.add_argument('-m', '--measurements', action='store_true')

args = parser.parse_args()

backend = get_backend(args)

mqtt_client = mqtt.Client("test2")
mqtt_client.connect("rpi-opench-gateway", 1883)

for mac in args.macs:
    topicDeviceInfo = 'OpenCH/TeHu/{}/PubDeviceInfo'.format(mac_to_eui64(mac))
    topicHealth = 'OpenCH/TeHu/{}/PubHealth'.format(mac_to_eui64(mac))
    topicMeasurements = 'OpenCH/TeHu/{}/PubState'.format(mac_to_eui64(mac))
    
    poller = MiTempBtPoller(mac, backend)

    if args.devinfo == True:
       message = '{{"name":"{}","firmware_version":"{}"}}' \
            .format(
                poller.name(),
                poller.firmware_version())
       mqtt_client.publish(topicDeviceInfo, message)

    if args.health == True:
        message = '{{"measurements":[{{"name":"battery","value":{},"units":"%"}}]}}' \
            .format(
                poller.parameter_value(MI_BATTERY))
        mqtt_client.publish(topicHealth, message)

    if args.measurements == True:
        message = '{{"measurements":[{{"name":"temperature","value":{},"units":"℃"}},{{"name":"humidity","value":{},"units":"%"}}]}}' \
            .format(
                poller.parameter_value(MI_TEMPERATURE),
                poller.parameter_value(MI_HUMIDITY))
        mqtt_client.publish(topicMeasurements, message)

mqtt_client.disconnect()

