""" Test parsing of binary data.

"""

import unittest
from datetime import datetime
from test.helper import MockBackend
from mitemp.mitemp_poller import MiTempPoller, MI_TEMPERATURE, MI_HUMIDITY


class KNXConversionTest(unittest.TestCase):
    """Test parsing of binary data."""
    # in testing access to protected fields is OK
    # pylint: disable=protected-access

    def test_parsing(self):
        """Does the Mi TEMP data parser works correctly?"""
        poller = MiTempPoller(None, MockBackend)
        data = bytes([0x54, 0x3d, 0x32, 0x35, 0x2e, 0x36, 0x20,
                      0x48, 0x3d, 0x32, 0x33, 0x2e, 0x36, 0x00])
        poller._cache = data
        poller._last_read = datetime.now()
        self.assertEqual(poller._parse_data()[MI_TEMPERATURE], 25.6)
        self.assertEqual(poller._parse_data()[MI_HUMIDITY], 23.6)
