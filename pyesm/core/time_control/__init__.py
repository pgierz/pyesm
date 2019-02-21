"""
time_control contains objects related to time-keeping during a simulation.

``EsmCalendar`` an object that controls:

+ inital_date
+ final_date
+ current_date
+ start_date
+ end_date
+ delta_date


----
"""
import collections
import logging

from ruamel.yaml import YAML, yaml_object
import pendulum

from pyesm.core.time_control import esm_calendar

yaml = YAML()


@yaml_object(yaml)
class EsmCalendar(object):
    """
    The ESMCalendar object should be able to control the following attributes
    of the simulation:

    Attributes
    ----------
    initial_date : ~`pyesm.core.time_control.esm_calendar.date`
        The starting date of the entire simulation (this is hard-wired during
        initialization of a simulation)
    final_date : ~`pyesm.core.time_control.esm_calendar.date`
        The final date of the entire simulation. (this is also hard_wired)
    current_date : ~`pyesm.core.time_control.esm_calendar.date`
        Where the simulation currently is at
    start_date : ~`pyesm.core.time_control.esm_calendar.date`
        the starting date of this run
    end_date : ~`pyesm.core.time_control.esm_calendar.date`
        the ending date of this run
    delta_date : ~`pyesm.core.time_control.esm_calendar.date`
        the "timestep" of the simulation. Should be a ``str`` of the form
        "years=x, months=y, days=z, hours=a, minutes=b, seconds=c".  Any of
        these parts can be omitted, e.g. you can say "years=1".  The **spaces**
        between the parts of the string are **mandatory**

        .. NOTE:
            This does not have anything to do with the the timesteps of the actual
            components, which are normally defined in namelists. This controls
            how often the simulation submits a new job.
    """
    def __init__(self, initial_date, final_date, delta_date):
        """
        Initializes a new ``esm_calendar`` object
        """

        self.initial_date = esm_calendar.Date(initial_date)
        self.final_date = esm_calendar.Date(final_date)
        self.delta_date = esm_calendar.Date(delta_date)

        self.run_number = 1
        self.current_date = self.start_date = self.initial_date
        self.end_date = self.start_date.add(self.delta_date)

        logging.debug("\nInitialized a ``EsmCalendar`` with the following attributes:")
        for k, v in self.__dict__.items():
            logging.debug("%s=%s", k, v)

    def __str__(self):
        return 'calendar'

    def __repr__(self):
        return "EsmCalendar(initial_date=%s, final_date=%s, delta_date=%s)" % \
                (self.initial_date, self.final_date, self.delta_date)

    def update_dates(self):
        """
        Updates previous_date, previous_run_number, next_date, and next_run_number

        Uses the current delta_date attribute of the ``EsmCalendar`` to modify
        the following attributes:

        + previous_date
        + previous_run_number
        + next_date
        + next_run_number
        """
        logging.debug("Updating next and previous dates...")
        self.previous_date = self.current_date.sub(self.delta_date)
        self.previous_run_number = int(self.run_number) - 1
        logging.debug("previous_date=%s", self.previous_date)
        logging.debug("previous_run_number=%s", self.previous_run_number)

        self.next_date = self.current_date.add(self.delta_date)
        self.next_run_number = int(self.run_number) + 1
        logging.debug("next_date=%s", self.next_date)
        logging.debug("next_run_number=%s", self.next_run_number)

    def read_date_file(self, date_file):
        """
        Tries to read the date_file if it exists.

        Parameters
        ----------
        date_file
            The path to the date_file to read (with filename)


        Sets up the following attributes:

        Attributes
        ----------
        self.run_number
        self.current_year
        self.current_month
        self.current_day
        """
        try:
            with open(date_file, "r") as f:
                date_string, self.run_number = f.read().split()
                self.current_date = esm_calendar.Date(date_string)
        # NOTE: IOError might be called FileNotFoundError in python3+
        except IOError:
            logging.debug("The datefile %s was not found, assuming very first run", date_file)
        self.update_dates()

    def write_date_file(self, date_file):
        """
        Writes the starting date and run number of the **NEXT** run. This
        should be called at the very end of a simulation

        Parameters
        ----------
        date_file : str
            The full path with filename where the file should be written.
        """
        logging.debug("Writing next_date=%s and next_run_number=%s to %s for next run",
                      self.next_date, self.next_run_number, date_file)
        with open(date_file, "w") as f:
            f.write(" ".join([self.next_date.format(), str(self.next_run_number)]))


class CouplingEsmCalendar(EsmCalendar):
    """
    Contains some extra functionality for iterative coupling to read chunk
    files as well as date files.
    """
    def __init__(self, chunk_lengths, **standard_calendar_kwargs):
        """
        Initialize a coupling calendar.

        Parameters
        ----------
        chunk_lengths : dict of strs
            A dictionary containing the name of the setups as the keys, and the
            length of the runs as strings as the values. These strings should
            be formatted according to esm_calendar.Date formatting
            requirements.
        **standard_calendar_kwargs
            Other arguments passed to the standard calendar constructor.
        """
        super(CouplingEsmCalendar, self).__init__(**standard_calendar_kwargs)

        self.setups = collections.deque(chunk_lengths.keys())
        self.chunk_lengths = chunk_lengths
        self.chunk_number = {setup: 1 for setup in self.setups}

        for setup, chunk_length in self.chunk_lengths.items():
            self.chunk_lengths[setup] = esm_calendar.Date(chunk_length)
            self.coupling_start_date = {setup: self.start_date}
            self.coupling_end_date = {setup: self.coupling_start_date[setup].add(self.chunk_lengths[setup])}

        logging.debug("\nInitialized a ``CouplingEsmCalendar`` with the following attributes:")
        for k, v in self.__dict__.items():
            logging.debug("%s=%s", k, v)

    def write_chunk_file(self, setup_name):
        """
        Writes the starting date, chunk number, and run number of the **NEXT**
        chunk. This is called at the very end of an iteratively coupled
        simulation.

        Parameters
        ----------
        chunk_file : str
            The full path with the filename where the file should be written.
        setup_name : str
            The name of the setup that will start **NEXT**
        """
        logging.debug("Writing next chunk_start_date=%s, chunk_number=%s, and setup=%s for next chunk to file %s",
                      self.next_chunk_start_date, self.chunk_number[setup_name], setup_name, chunk_file)
        with open(chunk_file, "w") as f:
            f.write(" ".join([self.next_chunk_start_date.format("YYYYMMDD"),
                              str(self.next_chunk_number),
                              setup_name]))
