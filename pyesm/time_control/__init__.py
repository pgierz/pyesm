"""
time_control contains objects related to time-keeping during a simulation.

``esm_calendar``: an object that controls:

+ inital_date
+ final_date
+ current_date
+ start_date
+ end_date
+ delta_date

Current external dependencies:
``pendulum``
    for easier handling of datetime objects. Could in principle be re-written for pure datetime

TODO: We still need a way to handle ``PISM`` calendars, since ``datetime`` objects can't do negative
time.

----
"""
import collections
import pendulum
import logging


def parse_esm_date_string(date_string):
    """
    Parses the date_string and returns seperate objects for year, month, day

    Arguments
    ---------
    date_string : str
        The date_string, which is assumed to have the form YYYYMMDD
        
    Returns
    -------
    ``datetime``:
        A ``pendulum.datetime`` object with year, month, day of the parsed string.
    """
    year, month, day = date_string[0:4], date_string[4:6], date_string[6:8]
    return pendulum.datetime(int(year), int(month), int(day))


class EsmCalendar(object):
    """
    The ESM-Calendar object should be able to control the following attributes of the simulation:

    Attributes
    ----------
    initial_date:
        The starting date of the entire simulation (this is hard-wired during
        initialization of a simulation)
    final_date:
        The final date of the entire simulation. (this is also hard_wired)
    current_date:
        Where the simulation currently is at
    start_date:
        the starting date of this run
    end_date:
        the ending date of this run
    delta_date:
        the "timestep" of the simulation. Should be a ``str`` of the form
        "years=x, months=y, days=z, hours=a, minutes=b, seconds=c".  Any of
        these parts can be omitted, e.g. you can say "years=1".  The **spaces**
        between the parts of the string are **mandatory**

        .. NOTE:
            This does not have anything to do with the the timesteps of the actual
            components, which are normally defined in namelists. This basically
            controls how often the simulation submits a new job.
    """
    def __init__(self, initial_date="18500101", final_date="18530101", delta_date="years=1"):
        """
        Initializes a new ``esm_calendar`` object
        """
        self.initial_date, self.final_date, self.delta_date = initial_date, final_date, delta_date

        self.run_number = 1
        delta_date_dict = dict(e.split("=") for e in delta_date.split(", "))
        for k, v in delta_date_dict.items():
            delta_date_dict[k] = int(v)
        self.delta_time = pendulum.duration(**delta_date_dict)
        self.current_date = self.start_date = parse_esm_date_string(self.initial_date)
        self.end_date = self.start_date + self.delta_time


    def update_dates(self):
        """ Updates previous_date, previous_run_number, next_date, and next_run_number """
        self.previous_date = self.current_date - self.delta_time
        self.previous_run_number = self.run_number - 1

        self.next_date = self.current_date + self.delta_time
        self.next_run_number = self.run_number + 1

    def __str__(self):
        return self.current_date.format("YYYYMMDD")

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
                self.current_date = parse_esm_date_string(date_string)
        # NOTE: IOError might be called FileNotFoundError in python3+
        except IOError:
            logging.debug("The datefile %s was not found, assuming very first run", date_file)
        self.update_dates()

    def write_date_file(self, date_file):
        """
        Writes the starting date and run number of the **NEXT** run. This is
        called at the very end of a simulation

        Parameters
        ----------
        date_file : str
            The full path with filename where the file should be written.
        """
        logging.debug("Writing next_date=%s and next_run_number=%s to %s for next run in file %s",
                      self.next_date, self.next_run_number, date_file)
        with open(date_file, "w") as f:
            f.write(" ".join([self.next_date.format("YYYYMMDD"), str(self.next_run_number)]))

class CouplingEsmCalendar(EsmCalendar):
    """
    Contains some extra functionality for iterative coupling to read chunk
    files as well as date files.
    """
    def __init__(self, chunk_lengths, **standard_calendar_kwargs):
        super(CouplingEsmCalendar, self).__init__(**standard_calendar_kwargs)
        self.setups = collections.deque(chunk_lengths.keys())
        # FIXME: where to turn the ints into datetimes? Here? Below? Not at all???
        self.chunk_lengths = chunk_lengths
        self.chunk_number = {setup: 1 for setup in self.setups}
        for setup in self.setups:
                self.coupling_start_date = {setup: self.start_date}
                self.coupling_end_date = {setup: self.coupling_start_date[setup].add(years=self.chunk_lengths[setup])}

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
