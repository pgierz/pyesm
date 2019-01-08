import os
import sys
import shutil
import unittest
import logging

from pyesm.time_control import EsmCalendar

class TestEsmCalendar(unittest.TestCase):
    """ Various tests for the EsmCalendar Time Controller """

    def setUp(self):
        os.mkdir(type(self).__name__)

    def test_ESM_Calendar_init(self):
        """ Test to make sure ESM Calendar initializes correctly """
        test_cal = EsmCalendar("18500101", "18510101", "years=1")
        self.assertEqual(test_cal.current_date.format("YYYY"), "1850")
        self.assertEqual(test_cal.current_date.format("MM"), "01")
        self.assertEqual(test_cal.current_date.format("DD"), "01")

        test_cal = EsmCalendar("18500328", "18510101", "years=1")
        self.assertEqual(test_cal.current_date.format("YYYY"), "1850")
        self.assertEqual(test_cal.current_date.format("MM"), "03")
        self.assertEqual(test_cal.current_date.format("DD"), "28")

    def test_ESM_Calendar_read_date_file_missing(self):
        """ Test to make sure ESM Calendar gets correct values if the date file is not there """
        test_cal = EsmCalendar("18500101", "18510101", "years=1")
        test_cal.read_date_file("/dev/null/nothing")
        self.assertEqual(test_cal.run_number, 1)

    def test_ESM_Calendar_read_date_file(self):
        """ Test to make sure ESM Calendar gets correct values if the date file exists """
        test_cal = EsmCalendar("18500101", "19500101", "years=1")
        with open(type(self).__name__+"/test.date", "w") as f:
            f.write("18510101 2")
        test_cal.read_date_file(type(self).__name__+"/test.date") 
        self.assertEqual(test_cal.run_number, "2")
        self.assertEqual(test_cal.current_date.format("YYYY"), "1851")

    def test_ESM_Calendar_prev_date(self):
        """ Tests if previous date is correct """
        test_cal = EsmCalendar("18500101", "18510101", "years=1")
        self.assertEqual(test_cal.previous_date.format("YYYY"), "1849")
        self.assertEqual(test_cal.previous_date.format("MM"), "01")
        self.assertEqual(test_cal.previous_date.format("DD"), "01")

    def test_ESM_Calendar_next_date(self):
        """ Tests if next date is correct """
        test_cal = EsmCalendar("18500101", "18510101", "years=1")
        self.assertEqual(test_cal.next_date.format("YYYY"), "1851")
        self.assertEqual(test_cal.next_date.format("MM"), "01")
        self.assertEqual(test_cal.next_date.format("DD"), "01")

    def test_ESM_Calendar_write_date_file(self):
        test_cal = EsmCalendar("18500101", "19500101", "years=1")
        test_cal.write_date_file(type(self).__name__+"/test.date")

    def test_ESM_Calendar_str(self):
        test_cal = EsmCalendar("18500101", "19500101", "years=1")
        self.assertEqual(str(test_cal), "18500101")

    def tearDown(self):
        shutil.rmtree(type(self).__name__)

if __name__ == "__main__":
    unittest.main()
