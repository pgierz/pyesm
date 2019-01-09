import json
import os
import shutil
import sys
import tempfile
import unittest

from pyesm.component import Component
from pyesm.component.component_simulation import ComponentCompute
from pyesm.helpers import ComponentFile, FileDict
import pyesm.logging as logging

from tests import set_env

display_logging = False

if display_logging:
    logger = logging.getLogger()
    logger.level = logging.DEBUG
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)


def dummy_test(self, arg1, arg2="hi there"):
    logging.debug(arg1, arg2)


def dummy_user_test(self):
    logging.debug("A user function")


def dummy_USER_test(self, default_val=False):
    if default_val:
        logging.debug("a USER function that is very important!")


class TestComponentBase(unittest.TestCase):
    def setUp(self):
        self.test_dir = type(self).__name__ 
        os.mkdir(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

class TestComponent(TestComponentBase):
    """Various tests for a basic component"""

    def setUp(self):
        super(TestComponent, self).setUp()
        self.test_comp = Component(parent_dir=self.test_dir)

    def test_Component_init(self, comp=None):
        """Component initializes correctly"""
        if comp is None:
            comp = self.test_comp
        assert comp.Name == "component"
        assert comp.Version == "0.0.0"
        print("Parent_dir", comp._parent_dir, "test_dir and name", self.test_dir+"/"+comp.expid)
        assert comp._parent_dir == self.test_dir + "/" + comp.expid
        for filetype in ["restart", "config", "forcing", "input", "log", "mon", "outdata"]:
            assert hasattr(comp, filetype + "_dir")
        for ResString in ["LateralResolution", "VerticalResolution", "Timestep"]:
            assert hasattr(comp, ResString)
            assert getattr(comp, ResString) is None
        for ResProperty in ["_nx", "_ny", "_nz"]:
            assert hasattr(comp, ResProperty)
            assert getattr(comp, ResProperty) is None

    def test_Component_call_steps_required_fail(self):
        """ A dummy phase should fail immediately """
        self.assertRaises(NotImplementedError, self.test_comp._call_steps, "dummy", "test")

    def test_Component_call_steps_add_methods(self):
        """Adding steps to a phase works"""

        Component._dummy_test = dummy_test
        Component._dummy_test_args = ["Dummy Test from Default"]
        Component._dummy_test_kwargs = {"arg2": "Howdy!"}

        Component._dummy_user_test = dummy_user_test

        Component._dummy_USER_test = dummy_USER_test
        Component._dummy_USER_test_kwargs = {"default_val": True}

        Component._dummy2_test = dummy_test
        Component._dummy2_test_args = ["A arg only test"]

        old_test_comp = self.test_comp

        shutil.rmtree(self.test_dir)
        self_test_comp = Component(parent_dir=self.test_dir)
        self.test_comp._call_steps("dummy", ["test"])
        self.test_comp._call_steps("dummy2", ["test"])
        self.test_comp = old_test_comp

    def tearDown(self):
        shutil.rmtree(self.test_dir)


class TestComponentSQL(TestComponent):
    """Tests specific to SQL-enabled components"""

    def test_Component_with_SQL(self):
        """Component can initialize when using SQL database interface"""
        self.test_Component_init(comp=Component(parent_dir=self.test_dir, use_SQL=True))


class TestComponentCompute_Basics(unittest.TestCase):
    """Tests basic steps always needed in a ComponentCompute """

    def setUp(self):
        self.test_dir = type(self).__name__
        os.mkdir(self.test_dir)

    def test_filetable_method(self):
        """Tests if correct errors are raised for filetable reading"""
        tmp_table_dir = tempfile.mkdtemp()
        test_component_compute = ComponentCompute(parent_dir=self.test_dir,
                                                  table_dir=tmp_table_dir,
                                                  calendar=None)
        with open(tmp_table_dir+"/component_0.0.0_test_files.json", mode="w") as tmp_json_file:
            data = {}
            data["bad_key"] = "lalala"
            json.dump(data, tmp_json_file)

        self.assertRaises(KeyError, test_component_compute._read_filetables,
                          json_dir=tmp_table_dir,
                          tag="test")
        
        with open(tmp_table_dir+"/component_0.0.0_test_files.json", mode="w") as tmp_json_file:
            data = {}
            data["input"] = {"lalala": "not a list"}
            json.dump(data, tmp_json_file)

        self.assertRaises(TypeError, test_component_compute._read_filetables,
                          json_dir=tmp_table_dir,
                          tag="test")

        shutil.rmtree(tmp_table_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

class TestComponentCompute_Prepare(unittest.TestCase):
    """Tests for seperate large methods of a ComponentCompute object: prepare phase"""

    def setUp(self):
        """ Sets up small independent tests for a generic ComponentCompute object in the Prepare Phase"""
        os.mkdir(type(self).__name__)
        self.test_component_compute = ComponentCompute(parent_dir=type(self).__name__, table_dir="pyesm/component", 
                                                       calendar=None)

    def test_read_filetables(self):
        """ ComponentCompute can read a default JSON filetable """
        self.test_component_compute._prepare_read_filetables()
        self.assertEqual(self.test_component_compute.files["input"],
                         FileDict({"input_file_1": ComponentFile(src="/this/is/the/first/testfile/file1_source",
                                                                 dest="/this/is/the/first/testfile/file1_dest"),
                                   "input_file_2": ComponentFile(src="/this/is/the/second/testfile/file2_source",
                                                                 dest="/this/is/the/second/testfile/file2_dest")}))

    def test_modify_filetables(self):
        """ ComponentCompute can modify src files based upon a modify JSON filetable """
        self.test_component_compute._prepare_read_filetables()
        input_before = self.test_component_compute.files["input"].items()
        self.test_component_compute._prepare_modify_filetables()
        input_after = self.test_component_compute.files["input"].items()
        self.assertEqual(self.test_component_compute.files["input"],
                         FileDict({"input_file_1": ComponentFile(src="/this/is/the/first/testfile/file1_source_different",
                                                                 dest="/this/is/the/first/testfile/file1_dest"),
                                   "input_file_2": ComponentFile(src="/this/is/the/second/testfile/file2_source",
                                                                 dest="/this/is/the/second/testfile/file2_dest")}),
                         msg="Input before was %s, Input after was %s" % (input_before, input_after))

    def test_env_override_filetables(self):
        """ ComponentCompute can override ComponentFile object `src` from enviornmental variables """
        self.test_component_compute.files["input"] = FileDict({"foo": ComponentFile("/foo/bar")})
        with set_env(foo="/fiz/buzz"):
            self.test_component_compute._prepare_override_filetables_from_env()
        self.assertEqual(self.test_component_compute.files["input"]["foo"].src, "/fiz/buzz",
                         "The actual input is %s" % self.test_component_compute.files["input"]["foo"].src)

    def test_copy_files_to_exp_tree(self):
        """ Files are copied to work for a 'dummy' fileset """
        self.test_component_compute._prepare_read_filetables(json_dir="tests/test_component_minitree/")
        self.test_component_compute._prepare_copy_files_to_exp_tree()

        try:
            assert os.path.isfile(type(self).__name__ + "/" + self.test_component_compute.expid + "/input/component/initial_conditions")
        except AssertionError:
            for path, dirs, files in os.walk(type(self).__name__):
                print(path)
                for f in files:
                    print(f)
        assert os.path.isfile(type(self).__name__ + "/" + self.test_component_compute.expid + "/input/component/boundary_conditions")
        assert os.path.isfile(type(self).__name__ + "/" + self.test_component_compute.expid + "/forcing/component/forcing1")
        assert os.path.islink(type(self).__name__ + "/" + self.test_component_compute.expid + "/restart/component/restart1")

    def tearDown(self):
        """ Clean up small independent tests for a generic ComponentCompute object in the Prepare Phase """
        shutil.rmtree(type(self).__name__)

class TestComponentCompute_Work(TestComponentBase):
    """ Tests for seperate large methods of a ComponentCompute object: work phase """
    def test_copy_files_to_workdir(self):
        """ Checks if files that have already been copied to the exp_tree can be copied to the work folder """
        self.test_component_compute = ComponentCompute(parent_dir=self.test_dir, table_dir="component",
                                                       calendar=None)
        self.test_component_compute._prepare_read_filetables(json_dir="tests/test_component_minitree/")
        self.test_component_compute._prepare_copy_files_to_exp_tree()
        self.test_component_compute._work_copy_files()

class TestComponentCompute_Cleanup(TestComponentBase):
    """ Tests for seperate large methods of a ComponentCompute object: cleanup phase """
    def test_copy_files_from_workdir(self):
        """ Checks if files are generated during the simulation can be copied to the outdata tree """
        test_component_compute = ComponentCompute(parent_dir=self.test_dir, table_dir="component",
                                                  calendar=None)
        shutil.rmtree(self.test_dir+"/"+test_component_compute.expid+"/work")
        shutil.copytree("tests/test_component_minitree_after_work/work", self.test_dir+"/"+test_component_compute.expid+"/work")
        test_component_compute._cleanup_copy_files(json_dir="tests/test_component_minitree_after_work/")

if __name__ == "__main__":
    stream_handler.stream = sys.stdout
    unittest.main()
