import unittest

from pyesm.echam6.echam_dataset import Dataset


class TestDataset(unittest.TestCase):
    """ Various tests for Datasets in ECHAM6 """
    def setUp(self):
        self.my_dataset = Dataset()

    def test_Dataset_check_year_valid(self):
        """ Tests if the check_year method returns true if a year is given in a
        specific range. """
        good_value = self.my_dataset.check_year(1850, 1750, 2000)
        self.assertTrue(good_value)

    def test_Dataset_check_year_invalid(self):
        """ Tests if the check_year method returns false if a year outside the
        valid range is given."""
        bad_value = self.my_dataset.check_year(9999, 1750, 2000)
        self.assertFalse(bad_value)

    def test_Dataset_find_min_case(self):
        the_big_bang = self.my_dataset.find("example_fileset", 1989)
        self.assertEqual(the_big_bang, "big_bang")

    def test_Dataset_find_middle_case(self):
        trump = self.my_dataset.find("example_fileset", 2019)
        self.assertEqual(trump, "Trump_Time_and_Sadness")

    def test_Dataset_find_max_case(self):
        the_future = self.my_dataset.find("example_fileset", 2022)
        self.assertEqual(the_future, "The_Future_at_2022")


if __name__ == "__main__":
    unittest.main()
