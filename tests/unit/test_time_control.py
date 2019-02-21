"""
Tests for Time Control. The following is tested:

The functions:
    + ``find_remainder_minutes``
    + ``find_remainder_hours``

For the class ``Calendar``:
    + ???

For the class ``Date``:
    + Date can be initialized
    + Dates can be added together
    + Dates can be subtracted
    + Dates can be correctly compared
"""
import unittest
import tempfile

from pyesm.core.time_control import EsmCalendar
from pyesm.core.time_control.esm_calendar import Date
import pyesm.core.time_control.esm_calendar

class TestEsmCalendar(unittest.TestCase):
    """ Various tests for the EsmCalendar Time Controller """

    def test_ESM_Calendar_init(self):
        """ Test to make sure ESM Calendar initializes correctly """
        test_cal = EsmCalendar("1850-01-01", "1851-01-01", "0001-00-00")
        self.assertEqual(test_cal.initial_date, Date("1850-01-01"))
        self.assertEqual(test_cal.final_date, Date("1851-01-01"))
        self.assertEqual(test_cal.delta_date, Date("0001-00-00"))

        test_cal = EsmCalendar("1850-03-28", "1851-01-01", "0000-01-00")
        self.assertEqual(test_cal.initial_date, Date("1850-03-28"))
        self.assertEqual(test_cal.final_date, Date("1851-01-01"))
        self.assertEqual(test_cal.delta_date, Date("0000-01-00"))

    def test_ESM_Calendar_repr(self):
        """ Tests if the repr is useful and makes sense """
        test_cal = EsmCalendar("1850-01-01", "1851-01-01", "0001-00-00")
        self.assertEqual(test_cal.__repr__(), 
                "EsmCalendar(initial_date=1850-1-1T0:0:0, final_date=1851-1-1T0:0:0, delta_date=1-0-0T0:0:0)")

    def test_ESM_Calendar_read_date_file_missing(self):
        """ Test to make sure ESM Calendar gets correct values if the date file is not there """
        test_cal = EsmCalendar("18500101", "18510101", "00010101")
        test_cal.read_date_file("/dev/null/nothing")
        self.assertEqual(test_cal.run_number, 1)

    def test_ESM_Calendar_update_dates(self):
        """ Tests if update dates works correctly """
        test_cal = EsmCalendar("1850-01-01", "1851-01-01", "0001-00-00")
        test_cal.update_dates()
        self.assertEqual(test_cal.next_run_number, 2)
        self.assertEqual(test_cal.previous_run_number, 0)

        self.assertEqual(test_cal.next_date, Date("1851-01-01"))
        self.assertEqual(test_cal.previous_date, Date("1849-01-01"))

    def test_ESM_Calendar_read_date_file(self):
        test_cal = EsmCalendar("1850-01-01", "1855-01-01", "0001-00-00")
        dummy_date_file = tempfile.TemporaryFile("w")
        dummy_date_file.write("1851-01-01 2")
        dummy_date_file.flush()
        test_cal.read_date_file(dummy_date_file)
        self.assertEqual(test_cal.current_date, Date("1851-01-01"))
        self.assertEqual(test_cal.run_number, 2)

class TestFunctions(unittest.TestCase):
    """Tests for functions in esm_calendar"""
    def test_find_remaining_minutes(self):
        """ Finding overflowed minutes works"""
        answer = pyesm.core.time_control.esm_calendar.find_remaining_minutes(70)
        self.assertEqual(answer, 10)

    def test_find_remaining_hours(self):
        """ Finding overflowed hours works"""
        answer = pyesm.core.time_control.esm_calendar.find_remaining_hours(70)
        self.assertEqual(answer, 10)


class TestCalendar(unittest.TestCase):
    """Tests for the Calendar class"""
    def test_Calendar_init(self):
        """Various types of calendars can be initialized"""
        leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=1)
        no_leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=0)
        equal_month_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=30)

    def test_Calendar_leapyear(self):
        """Leap year logic works in calendars"""
        leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=1)
        self.assertTrue(leap_year_calendar.isleapyear(2000))
        self.assertTrue(leap_year_calendar.isleapyear(2004))
        self.assertFalse(leap_year_calendar.isleapyear(2005))
        self.assertFalse(leap_year_calendar.isleapyear(2100))
        no_leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=0)
        self.assertFalse(no_leap_year_calendar.isleapyear(2100))

    def test_Calendar_days_in_year(self):
        """Counting days in the year works correctly"""
        leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=1)
        self.assertEqual(leap_year_calendar.day_in_year(2000), 366)

        no_leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=0)
        self.assertEqual(no_leap_year_calendar.day_in_year(2000), 365)

        equal_month_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=30)
        self.assertEqual(equal_month_calendar.day_in_year(2000), 12*30)

    def test_Calendar_days_in_month(self):
        """ Counting days in the month works correctly"""
        leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=1)
        # Get days in month from a string
        self.assertEqual(leap_year_calendar.day_in_month(2000, "jan"), 31)
        self.assertEqual(leap_year_calendar.day_in_month(2000, "FEB"), 29)
        # Get days in month from an int
        self.assertEqual(leap_year_calendar.day_in_month(2000, 1), 31)
        self.assertEqual(leap_year_calendar.day_in_month(2000, 4), 30)
        # Raise an exception of bad data is passed
        self.assertRaises(TypeError, leap_year_calendar.day_in_month, 2000, 0.25)
        # Equal month calendars always give back the number of days in the month
        equal_month_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=30)
        self.assertEqual(equal_month_calendar.day_in_month(2000, 2), 30)

    def test_Calendar_repr(self):
        """repr works for Calendars"""
        leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=1)
        self.assertEqual(leap_year_calendar.__repr__(), "esm_calendar(calendar_type=1)")

    def test_Calendar_str(self):
        """str representation works for Calendars"""
        leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=1)
        no_leap_year_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=0)
        equal_month_calendar = pyesm.core.time_control.esm_calendar.Calendar(calendar_type=30)
        self.assertEqual(str(leap_year_calendar), 'esm_calendar object with allowed leap years')
        self.assertEqual(str(no_leap_year_calendar), 'esm_calender object with no leap years allowed')
        self.assertEqual(str(equal_month_calendar), 'esm_calendar object with equal-length months of 30 days')


class TestDate(unittest.TestCase):
    """Tests for the Date class"""
    def test_Date_init(self):
        """A Date object can be correctly initialized from various forms"""
        # Normal date
        pyesm.core.time_control.esm_calendar.Date("1850-01-01")
        pyesm.core.time_control.esm_calendar.Date("0001-01-01")
        pyesm.core.time_control.esm_calendar.Date("1850-01-01T00:00:00")
        pyesm.core.time_control.esm_calendar.Date("1850-01-01_00:00:00")
        pyesm.core.time_control.esm_calendar.Date("18500101")

    def test_Date_negative_init(self):
        """ Dates can be initialized for negative years, months, days"""
        # Negative year
        pyesm.core.time_control.esm_calendar.Date("-12700-01-01")
        # Negative year, month, and day
        pyesm.core.time_control.esm_calendar.Date("-12700--01--01")
        # Positive year, month, and day, negative time
        pyesm.core.time_control.esm_calendar.Date("1850-01-01T-00:-00:-00")

    def test_Date_from_list(self):
        """A Date object can correctly be initialized from a list"""
        date = pyesm.core.time_control.esm_calendar.Date.from_list([1850, 1, 1, 0, 0, 0])
        date = pyesm.core.time_control.esm_calendar.Date.from_list([-12700, 1, 1, 0, 0, 0])
        date = pyesm.core.time_control.esm_calendar.Date.from_list([-12700, -1, -1, 0, 0, 0])

    def test_Date_attributes(self):
        """ Tests if a Date object has the correct attributes """
        date = pyesm.core.time_control.esm_calendar.Date("1850-01-01")
        for attr in ["year", "month", "day", "hour", "minute", "second"]:
            self.assertTrue(hasattr(date, attr))

    def test_Date_getindex(self):
        """ Tests if a Date object can access years, months, ect..."""
        date = pyesm.core.time_control.esm_calendar.Date("1850-01-01")
        # Get via index:
        self.assertEqual(date[0], 1850)
        self.assertEqual(date[1], 1)
        self.assertEqual(date[2], 1)
        self.assertEqual(date[3], 0)
        self.assertEqual(date[4], 0)
        self.assertEqual(date[5], 0)
        # Get via name:
        self.assertEqual(date.year, 1850)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 1)
        self.assertEqual(date.hour, 0)
        self.assertEqual(date.minute, 0)
        self.assertEqual(date.second, 0)

    def test_Date_setindex(self):
        """ Tests if a Date object can be mutated"""
        date = pyesm.core.time_control.esm_calendar.Date("18500101")
        date[0] = "1930"
        date[1] = "35"
        date[2] = "70"
        date[3] = "15"
        date[4] = "8"
        self.assertRaises(IndexError, date.__setitem__, 6, "10") 

    def test_Date_subtract(self):
        """ Tests if subtracting two dates works """
        date1 = pyesm.core.time_control.esm_calendar.Date("1850-01-01")
        date2 = pyesm.core.time_control.esm_calendar.Date("1853-01-01")
        answer = date2 - date1
        self.assertEqual(answer, pyesm.core.time_control.esm_calendar.Date("0003-00-00"))

    def test_Date_addmethod(self):
        """Tests if adding a delta date to this date works"""
        date1 = pyesm.core.time_control.esm_calendar.Date("1850-01-01")
        date2 = pyesm.core.time_control.esm_calendar.Date("0001-00-00")
        answer = date1.add(date2)
        self.assertEqual(answer, pyesm.core.time_control.esm_calendar.Date("1851-01-01"))


if __name__ == "__main__":
    unittest.main()
