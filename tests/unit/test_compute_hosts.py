import mock
import socket
import unittest

from pyesm.compute_hosts import Host


class test_Host(unittest.TestCase):
    def test_Host_has_all_attrs(self):
        """ Check if a host can be correctly initialized from the JSON file """
        with mock.patch("socket.gethostname", return_value="ollie1"):
            test_host = Host()
        for attr in ["hostnames", "nodetypes", "batch_system",
                     "operating_system", "partitions", "cores", "cpus"]:
            testBool = hasattr(test_host, attr)
            self.assertTrue(testBool, msg="%s lacking %s" % (test_host, attr))


if __name__ == "__main__":
    unittest.main()
