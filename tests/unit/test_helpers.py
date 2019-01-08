"""
Various tests for classes in helpers
"""
import os
import unittest

import f90nml

from pyesm.helpers import ComponentFile, ComponentNamelist, FileDict


class TestComponentFile(unittest.TestCase):
    """Various tests for ComponentFile class."""

    def test_ComponentFile_new(self):
        """ComponentFile initializes correctly"""
        # Check if initializations work in general
        self.assertIsInstance(ComponentFile("/foo/bar"),
                              ComponentFile)
        self.assertIsInstance(ComponentFile("/foo/bar", "/foo/lar"),
                              ComponentFile)

    def test_ComponentFile_arg_subs(self):
        """ Check if argument substitutions work correctly"""
        self.assertEqual(ComponentFile("./", "./").copy_method,
                         ComponentFile("./", "./", "copy").copy_method)
        self.assertEqual(ComponentFile("/foo/bar").dest,
                         ComponentFile("/foo/bar", "bar").dest)

    def test_ComponentFile_linkcopy(self):
        """ Check that links are correctly different from copies"""
        self.assertNotEqual(ComponentFile("./", "./"),
                            ComponentFile("./", "./", "link"))

    def test_ComponentFile_unknowncopy(self):
        """Checks that you can only give copy or link"""
        self.assertRaises(ValueError,
                          ComponentFile,
                          "./", "./", "banana")

    def test_ComponentFile_digest(self):
        """ Tests if digest works for ComponentFile """
        with open("foo", "w") as f:
            f.write("a test file")
        test_comp_file = ComponentFile(src="foo", dest="/tmp")
        test_comp_file.digest()
        for f in "foo", "/tmp/foo":
            os.remove(f)

    def test_ComponentFile_str(self):
        """ComponentFile __str__ works and is useful"""
        copy_file = ComponentFile(src="/foo/bar", dest="/foo/lar", copy_method="copy")
        self.assertEqual(copy_file.__str__(), "/foo/bar -- copied --> /foo/lar")
        link_file = ComponentFile(src="/foo/bar", dest="/foo/lar", copy_method="link")
        self.assertEqual(link_file.__str__(), "/foo/bar -- linked --> /foo/lar")

class TestComponentNamelist(unittest.TestCase):
    def setUp(self):
        nml = {
            'config_nml': {
                    'input': 'wind.nc',
                    'steps': 864,
                    'layout': [8, 16],
                    'visc': 0.0001,
                    'use_biharmonic': False
            }
        }
        with open("sample.nml", "w") as nml_file:
            nml = f90nml.namelist.Namelist(nml)
            nml.write(nml_file)

    def test_ComponentNamelist_new(self):
        """ Tests if a ComponentNamelist can be correctly initialized """
        example_nml = ComponentNamelist(src="sample.nml")
        for attr in "src", "dest", "copy_method", "nml":
            assert hasattr(example_nml, attr)

    def test_ComponentNamelist_extend_chapter(self):
        """ Tests if a new entry to an existing chapter can be added """
        example_nml = ComponentNamelist(src="sample.nml")
        example_nml.nml["config_nml"]["forcing_file"] = "something"
        self.assertIn("forcing_file", example_nml.nml["config_nml"])

    def test_ComponentNamelist_reduce_chapter(self):
        """Tests if an entry can be removed from an existing chapter """
        example_nml = ComponentNamelist(src="sample.nml")
        del example_nml.nml["config_nml"]["steps"]
        self.assertNotIn("steps", example_nml.nml["config_nml"])

    def test_ComponentNamelist_change_entry(self):
        example_nml = ComponentNamelist(src="sample.nml")
        example_nml.nml["config_nml"]["input"] = "waves.nc"
        self.assertEqual("waves.nc", example_nml.nml["config_nml"]["input"])
        
    def test_ComponentNamelist_delete_chapter(self):
        """Tests if an entire chapter can be removed"""
        example_nml = ComponentNamelist(src="sample.nml")
        del example_nml.nml["config_nml"]

    def test_ComponentNamelist_new_chapter(self):
        """ Tests if an new chapter can be added to the namelist """
        new_chapter = {
                "test_chapter": {
                    "output": "a_file.nc",
                    "an_int": 1234,
                    "a_list": [1,2,3,4],
                    "a_float": 42.000000,
                    "a_bool": True
                    }
                }
        extend_nml = f90nml.namelist.Namelist(new_chapter)
        example_nml = ComponentNamelist(src="sample.nml")
        example_nml.nml.update(extend_nml)
        self.assertIn("config_nml", example_nml.nml)
        self.assertIn("test_chapter", example_nml.nml)

    def test_ComponentNamelist_digest(self):
        """ Tests if the digest of a namelist works correctly """
        example_nml = ComponentNamelist(src="sample.nml", dest="/tmp/")
        example_nml.digest()
        os.remove("/tmp/sample.nml")

    def tearDown(self):
        os.remove("sample.nml")

class TestFileDict(unittest.TestCase):
    """Various tests for FileDict"""

    def setUp(self):
        self.test_list = FileDict()
        with open("testfile_original", "w") as f:
            f.write("This is a small testfile")
        self.cleanup_list = ["testfile_original"]

    def test_FileDict_new_empty(self):
        """An empty FileDict can be initialized"""
        self.assertIsInstance(self.test_list, FileDict)

    def test_FileDict_new_good_arguments(self):
        """FileDict can be initialized with correct arguments"""
        TestList = FileDict({"first_key": ComponentFile("/foo/bar")})
        self.assertIsInstance(TestList, FileDict)
        TestList = FileDict({"first_key": ComponentFile("/foo/bar"), "second_key": ComponentFile("/lar/mar")})
        self.assertIsInstance(TestList, FileDict)

    def test_FileDict_new_bad_arguments(self):
        """FileDict cannot be initialized with bad arguments"""
        self.assertRaises(TypeError, FileDict, "a", 1, 1.0)

    def test_FileDict_update(self):
        """FileDict can be updated to properly"""
        self.test_list.update({"foo": ComponentFile("/foo/bar")})

        self.assertEqual(self.test_list["foo"],
                         ComponentFile("/foo/bar"))

    def test_FileDict_append_bad(self):
        """FileDict fails if you try to do something stupid, like appending a non-ComponentFile"""
        self.assertRaises(TypeError,
                          self.test_list.update, {"my favorite key": "lala"})

    def test_FileDict_copyandrename(self):
        """FileDict can digest the a ComponentFile with the copy method, and rename it"""
        TestList = FileDict({"my_testfile": ComponentFile(src="testfile_original", dest="testfile_copy")})
        TestList.digest()
        assert os.path.isfile("./testfile_copy")
        self.cleanup_list.append("testfile_copy")

    def test_FileDict_linkandrename(self):
        """FileDict can digest the a ComponentFile with the link method, and rename it"""
        TestList = FileDict({"my link": ComponentFile(src="testfile_original", dest="testfile_link", copy_method="link")})
        TestList.digest()
        assert os.path.islink("./testfile_link")
        self.cleanup_list.append("testfile_link")

    def test_FileDict_digest_empty(self):
        """FileDict are empty after digestion with flag=work"""
        TestList = FileDict({"my link": ComponentFile(src="testfile_original", dest="testfile_link_newlink", copy_method="link")})
        TestList.digest(flag="work")
        self.assertEqual(len(TestList), 0)
        self.cleanup_list.append("testfile_link_newlink")

    def tearDown(self):
        """Removes testfiles generated by FileDict tests"""
        for testfile in self.cleanup_list:
            os.remove(testfile)


if __name__ == "__main__":
    unittest.main()
