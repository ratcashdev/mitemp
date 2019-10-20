"""
Reading from the sensor is handled by the command line tool "gatttool" that
is part of bluez on Linux.
No other operating systems are supported at the moment
"""

from threading import current_thread
import os
import logging
import re
import time
from typing import Callable
from subprocess import Popen, PIPE, TimeoutExpired, signal, call
from btlewrap.base import AbstractBackend, BluetoothBackendException

_LOGGER = logging.getLogger(__name__)


def wrap_exception(func: Callable) -> Callable:
    """Wrap all IOErrors to BluetoothBackendException"""

    def _func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IOError as exception:
            raise BluetoothBackendException() from exception
    return _func_wrapper


class GatttoolBackend(AbstractBackend):
    """ Backend using gatttool."""

    # pylint: disable=subprocess-popen-preexec-fn

    def __init__(self, adapter: str = 'hci0', *, retries: int = 3, timeout: float = 20, address_type: str = 'public'):
        super(GatttoolBackend, self).__init__(adapter, address_type)
        self.adapter = adapter
        self.retries = retries
        self.timeout = timeout
        self.address_type = address_type
        self._mac = None

    def connect(self, mac: str):
        """Connect to sensor.

        Connection handling is not required when using gatttool, but we still need the mac
        """
        self._mac = mac

    def disconnect(self):
        """Disconnect from sensor.

        Connection handling is not required when using gatttool.
        """
        self._mac = None

    def is_connected(self) -> bool:
        """Check if we are connected to the backend."""
        return self._mac is not None

    @wrap_exception
    def write_handle(self, handle: int, value: bytes):
        # noqa: C901
        # pylint: disable=arguments-differ

        """Read from a BLE address.

        @param: mac - MAC address in format XX:XX:XX:XX:XX:XX
        @param: handle - BLE characteristics handle in format 0xXX
        @param: value - value to write to the given handle
        """

        if not self.is_connected():
            raise BluetoothBackendException('Not connected to any device.')

        attempt = 0
        delay = 10
        _LOGGER.debug("Enter write_ble (%s)", current_thread())

        while attempt <= self.retries:
            cmd = "gatttool --device={} --addr-type={} --char-write-req -a {} -n {} --adapter={}".format(
                self._mac, self.address_type, self.byte_to_handle(handle), self.bytes_to_string(value), self.adapter)
            _LOGGER.debug("Running gatttool with a timeout of %d: %s",
                          self.timeout, cmd)

            with Popen(cmd,
                       shell=True,
                       stdout=PIPE,
                       stderr=PIPE,
                       preexec_fn=os.setsid) as process:
                try:
                    result = process.communicate(timeout=self.timeout)[0]
                    _LOGGER.debug("Finished gatttool")
                except TimeoutExpired:
                    # send signal to the process group
                    os.killpg(process.pid, signal.SIGINT)
                    result = process.communicate()[0]
                    _LOGGER.debug("Killed hanging gatttool")

            result = result.decode("utf-8").strip(' \n\t')
            if "Write Request failed" in result:
                raise BluetoothBackendException('Error writing handle to sensor: {}'.format(result))
            _LOGGER.debug("Got %s from gatttool", result)
            # Parse the output
            if "successfully" in result:
                _LOGGER.debug(
                    "Exit write_ble with result (%s)", current_thread())
                return True

            attempt += 1
            _LOGGER.debug("Waiting for %s seconds before retrying", delay)
            if attempt < self.retries:
                time.sleep(delay)
                delay *= 2

        raise BluetoothBackendException("Exit write_ble, no data ({})".format(current_thread()))

    @wrap_exception
    def wait_for_notification(self, handle: int, delegate, notification_timeout: float):
        """Listen for characteristics changes from a BLE address.

        @param: mac - MAC address in format XX:XX:XX:XX:XX:XX
        @param: handle - BLE characteristics handle in format 0xXX
                         a value of 0x0100 is written to register for listening
        @param: delegate - gatttool receives the
            --listen argument and the delegate object's handleNotification is
            called for every returned row
        @param: notification_timeout
        """

        if not self.is_connected():
            raise BluetoothBackendException('Not connected to any device.')

        attempt = 0
        delay = 10
        _LOGGER.debug("Enter write_ble (%s)", current_thread())

        while attempt <= self.retries:
            cmd = "gatttool --device={} --addr-type={} --char-write-req -a {} -n {} --adapter={} --listen".format(
                self._mac, self.address_type, self.byte_to_handle(handle), self.bytes_to_string(self._DATA_MODE_LISTEN),
                self.adapter)
            _LOGGER.debug("Running gatttool with a timeout of %d: %s", notification_timeout, cmd)

            with Popen(cmd,
                       shell=True,
                       stdout=PIPE,
                       stderr=PIPE,
                       preexec_fn=os.setsid) as process:
                try:
                    result = process.communicate(timeout=notification_timeout)[0]
                    _LOGGER.debug("Finished gatttool")
                except TimeoutExpired:
                    # send signal to the process group, because listening always hangs
                    os.killpg(process.pid, signal.SIGINT)
                    result = process.communicate()[0]
                    _LOGGER.debug("Listening stopped forcefully after timeout.")

            result = result.decode("utf-8").strip(' \n\t')
            if "Write Request failed" in result:
                raise BluetoothBackendException('Error writing handle to sensor: {}'.format(result))
            _LOGGER.debug("Got %s from gatttool", result)
            # Parse the output to determine success
            if "successfully" in result:
                _LOGGER.debug("Exit write_ble with result (%s)", current_thread())
                # extract useful data.
                for element in self.extract_notification_payload(result):
                    delegate.handleNotification(handle, bytes([int(x, 16) for x in element.split()]))
                return True

            attempt += 1
            _LOGGER.debug("Waiting for %s seconds before retrying", delay)
            if attempt < self.retries:
                time.sleep(delay)
                delay *= 2

        raise BluetoothBackendException("Exit write_ble, no data ({})".format(current_thread()))

    @staticmethod
    def extract_notification_payload(process_output):
        """
        Processes the raw output from Gatttool stripping the first line and the
            'Notification handle = 0x000e value: ' from each line
        @param: process_output - the raw output from a listen commad of GattTool
        which may look like this:
            Characteristic value was written successfully
            Notification handle = 0x000e value: 54 3d 32 37 2e 33 20 48 3d 32 37 2e 30 00
            Notification handle = 0x000e value: 54 3d 32 37 2e 32 20 48 3d 32 37 2e 32 00
            Notification handle = 0x000e value: 54 3d 32 37 2e 33 20 48 3d 32 37 2e 31 00
            Notification handle = 0x000e value: 54 3d 32 37 2e 32 20 48 3d 32 37 2e 33 00
            Notification handle = 0x000e value: 54 3d 32 37 2e 33 20 48 3d 32 37 2e 31 00
            Notification handle = 0x000e value: 54 3d 32 37 2e 31 20 48 3d 32 37 2e 34 00


            This method strips the fist line and strips the 'Notification handle = 0x000e value: ' from each line
        @returns a processed string only containing the values.
        """
        data = []
        for element in process_output.splitlines()[1:]:
            parts = element.split(": ")
            if len(parts) == 2:
                data.append(parts[1])
        return data

    @wrap_exception
    def read_handle(self, handle: int) -> bytes:
        """Read from a BLE address.

        @param: mac - MAC address in format XX:XX:XX:XX:XX:XX
        @param: handle - BLE characteristics handle in format 0xXX
        @param: timeout - timeout in seconds
        """

        if not self.is_connected():
            raise BluetoothBackendException('Not connected to any device.')

        attempt = 0
        delay = 10
        _LOGGER.debug("Enter read_ble (%s)", current_thread())

        while attempt <= self.retries:
            cmd = "gatttool --device={} --addr-type={} --char-read -a {} --adapter={}".format(
                self._mac, self.address_type, self.byte_to_handle(handle), self.adapter)
            _LOGGER.debug("Running gatttool with a timeout of %d: %s",
                          self.timeout, cmd)
            with Popen(cmd,
                       shell=True,
                       stdout=PIPE,
                       stderr=PIPE,
                       preexec_fn=os.setsid) as process:
                try:
                    result = process.communicate(timeout=self.timeout)[0]
                    _LOGGER.debug("Finished gatttool")
                except TimeoutExpired:
                    # send signal to the process group
                    os.killpg(process.pid, signal.SIGINT)
                    result = process.communicate()[0]
                    _LOGGER.debug("Killed hanging gatttool")

            result = result.decode("utf-8").strip(' \n\t')
            _LOGGER.debug("Got \"%s\" from gatttool", result)
            # Parse the output
            if "read failed" in result:
                raise BluetoothBackendException("Read error from gatttool: {}".format(result))

            res = re.search("( [0-9a-fA-F][0-9a-fA-F])+", result)
            if res:
                _LOGGER.debug(
                    "Exit read_ble with result (%s)", current_thread())
                return bytes([int(x, 16) for x in res.group(0).split()])

            attempt += 1
            _LOGGER.debug("Waiting for %s seconds before retrying", delay)
            if attempt < self.retries:
                time.sleep(delay)
                delay *= 2

        raise BluetoothBackendException("Exit read_ble, no data ({})".format(current_thread()))

    @staticmethod
    def check_backend() -> bool:
        """Check if gatttool is available on the system."""
        try:
            call('gatttool', stdout=PIPE, stderr=PIPE)
            return True
        except OSError as os_err:
            msg = 'gatttool not found: {}'.format(str(os_err))
            _LOGGER.error(msg)
        return False

    @staticmethod
    def byte_to_handle(in_byte: int) -> str:
        """Convert a byte array to a handle string."""
        return '0x'+'{:02x}'.format(in_byte).upper()

    @staticmethod
    def bytes_to_string(raw_data: bytes, prefix: bool = False) -> str:
        """Convert a byte array to a hex string."""
        prefix_string = ''
        if prefix:
            prefix_string = '0x'
        suffix = ''.join([format(c, "02x") for c in raw_data])
        return prefix_string + suffix.upper()
