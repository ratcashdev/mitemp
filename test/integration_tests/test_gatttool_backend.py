"""Test GatttoolBackend with real sensor."""
import unittest
from test import (_HANDLE_READ_NAME, _HANDLE_READ_FIRMWARE_VERSION,
                  _HANDLE_READ_WRITE_SENSOR_DATA, _HANDLE_READ_BATTERY_LEVEL, TEST_MAC)
import pytest
from btlewrap.base import BluetoothBackendException
from btlewrap.gatttool import GatttoolBackend


class TestGatttoolBackend(unittest.TestCase):
    """Test GatttoolBackend with real sensor."""
    # pylint does not understand pytest fixtures, so we have to disable the warning
    # pylint: disable=no-member

    def setUp(self):
        """Setup of the test case."""
        self.backend = GatttoolBackend(retries=0, timeout=20)

    @pytest.mark.usefixtures("mac")
    def test_read_name(self):
        """Test reading a handle from the sensor."""
        self.backend.connect(self.mac)
        result = self.backend.read_handle(_HANDLE_READ_NAME)
        self.assertIsNotNone(result)
        self.backend.disconnect()

    @pytest.mark.usefixtures("mac")
    def test_read_battery(self):
        """Test reading a handle from the sensor."""
        self.backend.connect(self.mac)
        result = self.backend.read_handle(_HANDLE_READ_BATTERY_LEVEL)
        self.assertIsNotNone(result)
        self.backend.disconnect()

    @pytest.mark.usefixtures("mac")
    def test_read_firmware(self):
        """Test reading a handle from the sensor."""
        self.backend.connect(self.mac)
        result = self.backend.read_handle(_HANDLE_READ_FIRMWARE_VERSION)
        self.assertIsNotNone(result)
        self.backend.disconnect()

    @pytest.mark.usefixtures("mac")
    def test_wait_for_notification(self):
        """Test writing data to handle of the sensor."""
        self.backend.connect(self.mac)
        result = self.backend.wait_for_notification(_HANDLE_READ_WRITE_SENSOR_DATA, self, 10)
        self.assertIsNotNone(result)
        self.backend.disconnect()

    def test_read_not_connected(self):
        """Test error handling if not connected."""
        with self.assertRaises(BluetoothBackendException):
            self.backend.read_handle(_HANDLE_READ_NAME)

    def test_check_backend(self):
        """Test check_backend function."""
        self.assertTrue(self.backend.check_backend())

    def test_invalid_mac_exception(self):
        """Test writing data to handle of the sensor."""
        with self.assertRaises(BluetoothBackendException):
            self.backend.connect(TEST_MAC)
            self.backend.read_handle(_HANDLE_READ_NAME)

    def handleNotification(self, handle, raw_data):  # pylint: disable=unused-argument,invalid-name,no-self-use
        """ gets called by the backend when using wait_for_notification
        """
        if raw_data is None:
            raise Exception('no data given')
        self.assertTrue(len(raw_data) == 14)
