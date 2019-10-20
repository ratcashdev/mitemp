"""Bluetooth backend for Blue Giga based bluetooth devices.

This backend uses the pygatt API: https://github.com/peplin/pygatt
"""
from typing import Callable
from btlewrap.base import AbstractBackend, BluetoothBackendException


def wrap_exception(func: Callable) -> Callable:
    """Decorator to wrap pygatt exceptions into BluetoothBackendException."""
    try:
        # only do the wrapping if pygatt is installed.
        # otherwise it's pointless anyway
        from pygatt.backends.bgapi.exceptions import BGAPIError
        from pygatt.exceptions import NotConnectedError
    except ImportError:
        return func

    def _func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BGAPIError as exception:
            raise BluetoothBackendException() from exception
        except NotConnectedError as exception:
            raise BluetoothBackendException() from exception

    return _func_wrapper


class PygattBackend(AbstractBackend):
    """Bluetooth backend for Blue Giga based bluetooth devices."""

    @wrap_exception
    def __init__(self, adapter: str = None, address_type: str = 'public'):
        """Create a new instance.

        Note: the parameter "adapter" is ignored, pygatt detects the right USB port automagically.
        """
        super(PygattBackend, self).__init__(adapter, address_type)
        self.check_backend()

        import pygatt
        self._adapter = pygatt.BGAPIBackend()
        self._adapter.start()
        self._device = None

    def __del__(self):
        if self._adapter is not None:
            self._adapter.stop()

    @wrap_exception
    def connect(self, mac: str):
        """Connect to a device."""
        import pygatt

        address_type = pygatt.BLEAddressType.public
        if self.address_type == 'random':
            address_type = pygatt.BLEAddressType.random
        self._device = self._adapter.connect(mac, address_type=address_type)

    def is_connected(self) -> bool:
        """Check if connected to a device."""
        return self._device is not None

    @wrap_exception
    def disconnect(self):
        """Disconnect from a device."""
        if self.is_connected():
            self._device.disconnect()
            self._device = None

    @wrap_exception
    def read_handle(self, handle: int) -> bytes:
        """Read a handle from the device."""
        if not self.is_connected():
            raise BluetoothBackendException('Not connected to device!')
        return self._device.char_read_handle(handle)

    @wrap_exception
    def write_handle(self, handle: int, value: bytes):
        """Write a handle to the device."""
        if not self.is_connected():
            raise BluetoothBackendException('Not connected to device!')
        self._device.char_write_handle(handle, value, True)
        return True

    @staticmethod
    def check_backend() -> bool:
        """Check if the backend is available."""
        try:
            import pygatt  # noqa: F401 # pylint: disable=unused-import
            return True
        except ImportError:
            return False
