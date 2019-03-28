"""
time_control contains objects related to time-keeping during a simulation.

The time control module contains classes related to time keeping during a
simulation. These objects typically contain dates and run numbers, as well as
the length of a run before restarting or starting the next model in an
iteratively coupled system.

Classes
-------
+ EsmCalendar
+ CouplingEsmCalendar

----

Please see see the detailed documentation for each of the classes below:
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
    initial_date : ~`pyesm.core.time_control.esm_calendar.Date`
        The starting date of the entire simulation (this is hard-wired during
        initialization of a simulation)
    final_date : ~`pyesm.core.time_control.esm_calendar.Date`
        The final date of the entire simulation. (this is also hard0wired)
    current_date : ~`pyesm.core.time_control.esm_calendar.Date`
        Where the simulation currently is at
    start_date : ~`pyesm.core.time_control.esm_calendar.Date`
        the starting date of this run
    end_date : ~`pyesm.core.time_control.esm_calendar.Date`
        the ending date of this run
    delta_date : ~`pyesm.core.time_control.esm_calendar.Date`
        How long a simulation will last before restarting itself.

        .. NOTE:
            This does not have anything to do with the the timesteps of the actual
            components, which are normally defined in namelists. This controls
            how often the simulation submits a new job.

    Methods
    -------
    + update_dates
        Called when the date file is read; this will update the previous date,
        previous run number, next date, and next run number.
    + read_date_file
        Reads a date file and sets the dates in the EsmCalendar object
        accordingly.
    + write_date_file
        Writes a date file with information concerning the current date and
        current run number.
    """
    def __init__(self, initial_date, final_date, delta_date):
        self.initial_date = initial_date
        self.final_date = final_date
        self.delta_date = delta_date

        self.run_number = 1
        self.current_date = self.start_date = self.initial_date
        self.end_date = self.start_date.add(self.delta_date)

        logging.debug("\nInitialized a ``EsmCalendar`` with the following attributes:")
        logging.debug("Run Number = %s", self.run_number)
        logging.debug("Initial Date of the entire experiment = %s", self.initial_date)
        logging.debug("Final Date of the entire experiment = %s", self.final_date)
        logging.debug("Delta Date (how long one run will take) = %s", self.delta_date)
        logging.debug("Current Date (where the experiment currently is) = %s", self.current_date)
        logging.debug("End Date (where this run will stop before submitting the next one) = %s", self.end_date)

    def __str__(self):
        return 'Time control for this experiment. current_date=%s, run_number=%s' % (self.current_date, self.run_number)

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
        self.current_date

        This method also updates the previous/next run_number/date by calling
        update dates as it's last step.
        """
        try:
            with open(date_file, "r") as this_date_file:
                date_string, run_number = this_date_file.read().split()
                self.current_date = esm_calendar.Date(date_string)
                self.run_number = int(run_number)
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
        with open(date_file, "w") as this_date_file:
            this_date_file.write(" ".join([self.next_date.format(), str(self.next_run_number)]))


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

        self.chunk_lengths = {setup: esm_calendar.Date(self.chunk_lengths[setup]) for setup in self.setups}
        self.coupling_start_date = {setup: self.start_date for setup in self.setups}
        self.coupling_end_date = {setup: self.coupling_start_date[setup].add(self.chunk_lengths[setup]) for setup in self.setups}

        self.coupling_dates = {}
        for setup, chunk_length in self.chunk_lengths.items():
            coupling_dates = []
            for year in range(self.chunk_lengths[setup].year + 1):
                coupling_dates.append(
                        self.coupling_start_date[setup].add(esm_calendar.Date.from_list([year, 0, 0, 0, 0, 0])))
            self.coupling_dates[setup] = coupling_dates
        self.this_setup = self.setups[0]
        # Move the right-most setup to the front:
        self.setups.rotate()
        self.previous_setup = self.setups[0]
        # Rotate back to original deque, then put the next setup at the very
        # beginning:
        self.setups.rotate(-2)
        self.next_setup = self.setups[0]
        # Don't touch self.setups after this, the order will be written to the
        # chunk file at the end of the run; and it will be in the right order
        # for the next run!

        logging.debug("\nInitialized a ``CouplingEsmCalendar`` with the following attributes:")
        logging.debug("Chunk lengths = %s", self.chunk_lengths)
        logging.debug("Chunk start dates = %s", self.coupling_start_date)
        logging.debug("Chunk end dates = %s", self.coupling_end_date)
        logging.debug("All setup couple dates are: %s", self.coupling_dates)
        logging.debug("The setup that just finished: %s", self.previous_setup)
        logging.debug("This setup now simulating: %s", self.this_setup)
        logging.debug("The setup that will go next: %s", self.next_setup)
# PG: I'm not sure about this yet...
#    def write_chunk_file(self, chunk_file, setup_name):
#        """
#        Writes the starting date, chunk number, and run number of the **NEXT**
#        chunk. This is called at the very end of an iteratively coupled
#        simulation.
#
#        Parameters
#        ----------
#        chunk_file : str
#            The full path with the filename where the file should be written.
#        setup_name : str
#            The name of the setup that will start **NEXT**
#        """
#        with open(chunk_file, "w") as this_chunk_file:
#            logging.debug("Writing next chunk_start_date=%s, chunk_number=%s, and setup=%s for next chunk to file %s",
#                          self.next_chunk_start_date, self.chunk_number[setup_name], setup_name, chunk_file)
#            this_chunk_file.write(" ".join([self.next_chunk_start_date.format(),
#                                            str(self.next_chunk_number),
#                                            setup_name]))
