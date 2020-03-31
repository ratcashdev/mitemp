""" Test parsing of binary data.

"""

import unittest
from datetime import datetime
from test.helper import MockBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY


class KNXConversionTest(unittest.TestCase):
    """Test parsing of binary data."""
    # in testing access to protected fields is OK
    # pylint: disable=protected-access

    def test_parsing1(self):
        """Does the Mi TEMP BT data parser works correctly for positive double digit values? Value: 'T=25.6 H=23.6'"""
        poller = MiTempBtPoller(None, MockBackend)
        data = bytearray([0x54, 0x3d, 0x32, 0x35, 0x2e, 0x36, 0x20,
                          0x48, 0x3d, 0x32, 0x33, 0x2e, 0x36, 0x00]).decode("utf-8").strip(' \n\t')
        poller._cache = data
        poller._last_read = datetime.now()
        self.assertEqual(poller._parse_data()[MI_TEMPERATURE], 25.6)
        self.assertEqual(poller._parse_data()[MI_HUMIDITY], 23.6)

    def test_parsing2(self):
        """Does the Mi TEMP BT data parser works correctly for positive single digit values? Value: T=2.3 H=3.6"""
        poller = MiTempBtPoller(None, MockBackend)
        data = bytearray([0x54, 0x3d, 0x32, 0x2e, 0x33, 0x20,
                          0x48, 0x3d, 0x33, 0x2e, 0x36]).decode("utf-8").strip(' \n\t')
        poller._cache = data
        poller._last_read = datetime.now()
        self.assertEqual(poller._parse_data()[MI_TEMPERATURE], 2.3)
        self.assertEqual(poller._parse_data()[MI_HUMIDITY], 3.6)

    def test_parsing3(self):
        """Does the Mi TEMP BT data parser works correctly for negative single digit values? Value: T=-9.3 H=36.6"""
        poller = MiTempBtPoller(None, MockBackend)
        data = bytearray([0x54, 0x3d, 0x2d, 0x39, 0x2e, 0x33, 0x20,
                          0x48, 0x3d, 0x33, 0x36, 0x2e, 0x36]).decode("utf-8").strip(' \n\t')
        poller._cache = data
        poller._last_read = datetime.now()
        self.assertEqual(poller._parse_data()[MI_TEMPERATURE], -9.3)
        self.assertEqual(poller._parse_data()[MI_HUMIDITY], 36.6)

    def test_parsing4(self):
        """Does the Mi TEMP BT data parser works correctly for negative double digit values? Value: T=-11.3 H=37.6"""
        poller = MiTempBtPoller(None, MockBackend)
        data = bytearray([0x54, 0x3d, 0x2d, 0x31, 0x31, 0x2e, 0x33, 0x20,
                          0x48, 0x3d, 0x33, 0x37, 0x2e, 0x36]).decode("utf-8").strip(' \n\t')
        poller._cache = data
        poller._last_read = datetime.now()
        self.assertEqual(poller._parse_data()[MI_TEMPERATURE], -11.3)
        self.assertEqual(poller._parse_data()[MI_HUMIDITY], 37.6)

    def test_parsing5(self):
        """Does the Mi TEMP BT data parser works correctly with spurious binary data? Value: T=-11.3 H=53.0\x02"""
        poller = MiTempBtPoller(None, MockBackend)
        data = bytearray([0x54, 0x3d, 0x2d, 0x31, 0x31, 0x2e, 0x33, 0x20,
                          0x48, 0x3d, 0x35, 0x33, 0x2e, 0x30, 0x02]).decode("utf-8").strip(' \n\t')
        poller._cache = data
        poller._last_read = datetime.now()
        self.assertEqual(poller._parse_data()[MI_TEMPERATURE], -11.3)
        self.assertEqual(poller._parse_data()[MI_HUMIDITY], 53.0)
