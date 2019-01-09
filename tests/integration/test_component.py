import os
import sys
import shutil
import unittest

import pyesm.logging as logging
from pyesm.component.component_simulation import ComponentCompute

display_logging = False

if display_logging:
    logger = logging.getLogger()
    logger.level = logging.DEBUG
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)


class TestComponentCompute_Integration(unittest.TestCase):
    """Tests for seperate large methods of a ComponentCompute object"""

    def setUp(self):
        os.mkdir(type(self).__name__)
        self.test_component_compute = ComponentCompute(parent_dir=type(self).__name__,
                                                       calendar=None,
                                                       table_dir="tests/test_component_minitree")

    def test_ComponentCompute_prepare(self):
        self.test_component_compute.prepare()

    def test_ComponentCompute_work(self):
        shutil.rmtree(type(self).__name__)
        shutil.copytree("tests/test_component_minitree_after_prepare",
                        type(self).__name__, symlinks=True)
        self.test_component_compute.work()

    def test_ComponentCompute_cleanup(self):
        shutil.rmtree(type(self).__name__+"/test/work")
        shutil.copytree("tests/test_component_minitree_after_work/work",
                        type(self).__name__+"/test/work", symlinks=True)
        self.test_component_compute.cleanup()

    def test_ComponentCompute_full_cycle(self):
        self.test_component_compute.prepare()
        self.test_component_compute.work()
        # This next part is a dummy model which would write some random data to
        # the work folder:
        os.system("ls -l "+self.test_component_compute.work_dir) 
        for outputfile in ["output1", "output2", "output3", "restart_output"]:
            f = open(self.test_component_compute.work_dir+"/"+outputfile, "w")
            f.close()
        os.system("ls -l "+self.test_component_compute.work_dir) 
        self.test_component_compute.cleanup()

    def tearDown(self):
        shutil.rmtree(type(self).__name__)


if __name__ == "__main__":
    stream_handler.stream = sys.stdout
    unittest.main()
