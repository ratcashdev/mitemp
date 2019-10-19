"""Backend for Miflora using the bluepy library."""
import re
import logging
import time
from typing import List, Tuple, Callable
from btlewrap.base import AbstractBackend, BluetoothBackendException

_LOGGER = logging.getLogger(__name__)
RETRY_LIMIT = 3
RETRY_DELAY = 0.1


def wrap_exception(func: Callable) -> Callable:
    """Decorator to wrap BTLEExceptions into BluetoothBackendException."""
    try:
        # only do the wrapping if bluepy is installed.
        # otherwise it's pointless anyway
        from bluepy.btle import BTLEException
    except ImportError:
        return func

    def _func_wrapper(*args, **kwargs):
        error_count = 0
        last_error = None
        while error_count < RETRY_LIMIT:
            try:
                return func(*args, **kwargs)
            except BTLEException as exception:
                error_count += 1
                last_error = exception
                time.sleep(RETRY_DELAY)
                _LOGGER.debug('Call to %s failed, try %d of %d', func, error_count, RETRY_LIMIT)
        raise BluetoothBackendException() from last_error

    return _func_wrapper


class BluepyBackend(AbstractBackend):
    """Backend for Miflora using the bluepy library."""

    def __init__(self, adapter: str = 'hci0', address_type: str = 'public'):
        """Create new instance of the backend."""
        super(BluepyBackend, self).__init__(adapter, address_type)
        self._peripheral = None

    @wrap_exception
    def connect(self, mac: str):
        """Connect to a device."""
        from bluepy.btle import Peripheral
        match_result = re.search(r'hci([\d]+)', self.adapter)
        if match_result is None:
            raise BluetoothBackendException(
                'Invalid pattern "{}" for BLuetooth adpater. '
                'Expetected something like "hci0".'.format(self.adapter))
        iface = int(match_result.group(1))
        self._peripheral = Peripheral(mac, iface=iface, addrType=self.address_type)

    @wrap_exception
    def disconnect(self):
        """Disconnect from a device if connected."""
        if self._peripheral is None:
            return

        self._peripheral.disconnect()
        self._peripheral = None

    @wrap_exception
    def read_handle(self, handle: int) -> bytes:
        """Read a handle from the device.

        You must be connected to do this.
        """
        if self._peripheral is None:
            raise BluetoothBackendException('not connected to backend')
        return self._peripheral.readCharacteristic(handle)

    @wrap_exception
    def write_handle(self, handle: int, value: bytes):
        """Write a handle from the device.

        You must be connected to do this.
        """
        if self._peripheral is None:
            raise BluetoothBackendException('not connected to backend')
        return self._peripheral.writeCharacteristic(handle, value, True)

    @wrap_exception
    def wait_for_notification(self, handle: int, delegate, notification_timeout: float):
        if self._peripheral is None:
            raise BluetoothBackendException('not connected to backend')
        self.write_handle(handle, self._DATA_MODE_LISTEN)
        self._peripheral.withDelegate(delegate)
        return self._peripheral.waitForNotifications(notification_timeout)

    @staticmethod
    def check_backend() -> bool:
        """Check if the backend is available."""
        try:
            import bluepy.btle  # noqa: F401 #pylint: disable=unused-import
            return True
        except ImportError as importerror:
            _LOGGER.error('bluepy not found: %s', str(importerror))
        return False

    @staticmethod
    @wrap_exception
    def scan_for_devices(timeout: float, adapter='hci0') -> List[Tuple[str, str]]:
        """Scan for bluetooth low energy devices.

        Note this must be run as root!"""
        from bluepy.btle import Scanner

        match_result = re.search(r'hci([\d]+)', adapter)
        if match_result is None:
            raise BluetoothBackendException(
                'Invalid pattern "{}" for BLuetooth adpater. '
                'Expetected something like "hci0".'.format(adapter))
        iface = int(match_result.group(1))

        scanner = Scanner(iface=iface)
        result = []
        for device in scanner.scan(timeout):
            result.append((device.addr, device.getValueText(9)))
        return result
