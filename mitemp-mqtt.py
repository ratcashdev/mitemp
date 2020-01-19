#!/usr/bin/env python3
import argparse
import re
import getmac
import paho.mqtt.publish as publish

from btlewrap import BluepyBackend, GatttoolBackend, PygattBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY

MAC_ADDRESS = r'(?i)[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}'

def valid_mac(mac):
    """ Validates MAC address """
    regex_mac_address = re.compile(MAC_ADDRESS)
    if regex_mac_address.match(mac):
        return mac
    raise argparse.ArgumentTypeError('Invalid MAC address {}'.format(mac))

def mac_to_eui64(mac):
    """ Converts MAC address to EUI64 """
    if valid_mac(mac):
        eui64 = re.sub(r'[.:-]', '', mac).lower()
        eui64 = eui64[0:6] + 'fffe' + eui64[6:]
        eui64 = hex(int(eui64[0:2], 16) ^ 2)[2:].zfill(2) + eui64[2:]
        return eui64
    return None

MI_TEMP_V1 = r'(?i)58:2D:34:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}'
MI_TEMP_V2 = r'(?i)4C:65:A8:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}'

def valid_mitemp_mac(mac):
    """ Validates MiTemp MAC address """
    regex_v1 = re.compile(MI_TEMP_V1)
    regex_v2 = re.compile(MI_TEMP_V2)
    if regex_v1.match(mac) or regex_v2.match(mac):
        return mac
    raise argparse.ArgumentTypeError('Invalid MiTemp MAC address {}'.format(mac))

backend = None

def get_backend(args):
    """ Returns Bluetooth backend """
    if args.backend == 'gatttool':
        backend = GatttoolBackend
    elif args.backend == 'bluepy':
        backend = BluepyBackend
    elif args.backend == 'pygatt':
        backend = PygattBackend
    else:
        raise Exception('unknown backend: {}'.format(args.backend))
    return backend

parser = argparse.ArgumentParser()
parser.add_argument('macs', type=valid_mitemp_mac, nargs="*")
parser.add_argument('-s', '--server', default='localhost')
parser.add_argument('-p', '--port', default=1883)
parser.add_argument('-b', '--backend', choices=['gatttool', 'bluepy', 'pygatt'], default='gatttool')
parser.add_argument('-d', '--devinfo', action='store_true')
parser.add_argument('-e', '--health', action='store_true')
parser.add_argument('-m', '--measurements', action='store_true')

args = parser.parse_args()
backend = get_backend(args)

self_mac = getmac.get_mac_address()
self_eui64 = mac_to_eui64(valid_mac(self_mac))
mqtt_client_id = "mitemp-mqtt-" + self_eui64

for mitemp_mac in args.macs:
    mitemp_eui64 = mac_to_eui64(mitemp_mac)
    topic_device_info = 'OpenCH/Gw/{}/TeHu/{}/Evt/DeviceInfo'.format(self_eui64, mitemp_eui64)
    topic_health = 'OpenCH/Gw/{}/TeHu/{}/Evt/Health'.format(self_eui64, mitemp_eui64)
    topic_measurements = 'OpenCH/Gw/{}/TeHu/{}/Evt/Status'.format(self_eui64, mitemp_eui64)
    
    poller = MiTempBtPoller(mitemp_mac, backend)
    msgs = []

    try:
        if args.devinfo:
            payload = '{{"name":"{}","firmware_version":"{}"}}' \
                .format( \
                    poller.name(), \
                    poller.firmware_version())
            msgs.append({'topic': topic_device_info, 'payload': payload})     

        if args.health:
            payload = '{{"measurements":[{{"name":"battery","value":{},"units":"%"}}]}}' \
                .format( \
                    poller.parameter_value(MI_BATTERY))
            msgs.append({'topic': topic_health, 'payload': payload})     

        if args.measurements:
            payload = '{{"measurements":[{{"name":"temperature","value":{},"units":"℃"}},{{"name":"humidity","value":{},"units":"%"}}]}}' \
                .format( \
                    poller.parameter_value(MI_TEMPERATURE), \
                    poller.parameter_value(MI_HUMIDITY))
            msgs.append({'topic': topic_measurements, 'payload': payload}) 

    except Exception as e:
        print(mitemp_mac + ' mitemp sensor failure: ' + str(e))

    if len(msgs) > 0:
        publish.multiple(msgs, hostname = args.server, port = args.port, client_id = mqtt_client_id)