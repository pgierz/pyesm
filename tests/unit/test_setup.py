import logging
import mock
import shutil
import socket
import sys
import unittest

from pyesm.setup import SetUp
from pyesm.setup.setup_simulation import SetUpCompute

display_logging = False

if display_logging:
    logger = logging.getLogger()
    logger.level = logging.DEBUG
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)


class TestSetUp(unittest.TestCase):
    def setUp(self):
        self.test_dir = type(self).__name__

    def test_SetUp_init(self):
        """ Tests SetUp Initialization """
        dummy_setup = SetUp(expid="test", parent_dir=self.test_dir)
        self.assertEqual(dummy_setup.expid, "test")
        self.assertEqual(dummy_setup._parent_dir, self.test_dir)

class TestSetUpCompute(unittest.TestCase):

    def setUp(self):
        self.test_dir = type(self).__name__

    def test_SetUpCompute_init(self):
        """ Tests SetUpCompute Initialization """
        with mock.patch("socket.gethostname", return_value="ollie1"):
            dummy_setup = SetUpCompute(expid="test", parent_dir=self.test_dir,
                                       components={"component": {"table_dir": "pyesm/component"}})
        self.assertEqual(dummy_setup.expid, "test")
        self.assertEqual(dummy_setup._parent_dir, self.test_dir)
        self.assertTrue(hasattr(dummy_setup, "component"))
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)

if __name__ == "__main__":
    unittest.main()
