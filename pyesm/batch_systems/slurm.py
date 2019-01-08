"""``Slurm`` objects implement ``BatchSystem`` with appropriate methods for a SLURM job scheduler.

----

"""
import getpass
import logging
import os
import subprocess

from . import BatchSystem

class Slurm(BatchSystem):
    def __init__(self, host=None, account=None):
        """ Constructs a ``Slurm`` object with the functionality of ``BatchSystem``

        Parameters
        ----------
        host : Host, optional
            Default ``None``, see documentation of ``BatchSystem``
        account : str, optional
            Default ``None``, if given, this string is passed to the submit flags
            as ``--account=<account_argument>``


        .. note:: The attributes described below try to define themselves from the
                  host configuration. The name that may be used in the host config
                  file is given

        Attributes
        ----------
        submitter:
            Tries to read "batch_system_submitter" from the host config, or defaults
            to "sbatch"
        launcher:
            Tries to read "batch_system_launcher" from the host config, or defaults
            to "srun"
        launcher_flags:
            Tries to read "batch_system_launcher_flags" from the host config, or defaults
            to "-l kill-on-bad-exit=1 --cpu_bind=cores"
        status_command:
            Tries to read "batch_system_status" from the host config, defaults to "squeue"

        Notes
        -----
            If you use logging at the ``DEBUG`` level, you get a print-out upon initialization of
            the submitter, launcher, launcher flags, status command, and resource account
        """
        logging.debug(80*"*")
        super(Slurm, self).__init__(host)
        self.submitter = getattr(self._host, "batch_system_submitter", "sbatch")
        self.launcher = getattr(self._host, "batch_system_launcher", "srun")
        self.launcher_flags = getattr(self._host, "batch_system_launcher_flags",
                                      {"-l": True, "--kill-on-bad-exit": 1, "--cpu_bind": "cores"})
        self.status_command = getattr(self._host, "batch_system_status", "squeue")

        self._account = account

        logging.debug("\nInitialized a Slurm BatchSystem with following attributes:")
        for this_attr_name, this_attr_value in {"Submitter": self.submitter,
                                                "Launcher": self.launcher,
                                                "Launcher Flags": self.launcher_flags,
                                                "Status Command": self.status_command, 
                                                "Resource Account": self._account}.items():
            logging.debug("\t\t - %s: %s", this_attr_name, this_attr_value)

    @staticmethod
    def check_full_queue():
        """ Submits a ``squeue`` command and returns a string with queue info"""
        return subprocess.check_output(["squeue"])

    @staticmethod
    def check_my_queue():
        """ Determines username, and submits ``squeue -u USER``, returning string of output"""
        USERNAME = getpass.getuser()
        return subprocess.check_output(["squeue", "-u", USERNAME])

    def construct_submitter_flags(self,
                               job_flag="compute", job_time="03:00:00", job_ntasks="0",
                               job_name="test", job_logfile="output_log", job_mailtype="FAIL",
                               exclusive=True):
        """
        Constructs the submission flags to later be unpacked during the
        execution call

        Parameters
        ----------
        job_flag : str, optional
            Default is "compute". This is used to select information from the
            Host object attached as self._host for things like compute
            partition names, etc.
        job_time : str, optional
            Default is "03:00:00". This string signals the job time in "HH:MM:SS"
        job_ntasks : str, optional
            Default is "0". The amount of tasks your compute job will need.
        job_name : str, optional
            Default is "test". This is the job name shown in the queue system.
        job_logfile : str, optional
            Default is "output_log". The name of the logfile you will get from
            SLURM.
        job_mailtype : str, optional
            Default is "FAIL". This controls when SLURM should email you about
            status changes in your job.
        exclusive : bool, optional
            Default is "True". This controls whether or not your request to
            reserve the entire compute node for yourself.

        Returns
        -------
        submitter_flags_str : str
            A string containing all the information described above. This can
            be given to the ``sbatch`` submitter as a series of flags.
        """
        logging.debug(40*"- ")
        logging.debug("\nConstructing Submitter Flags for Slurm Batch System:")
        if self._account:
            self.submitter_flags["--account"] = self._account
        self.submitter_flags["--partition"] = self._host.partitions[job_flag]
        self.submitter_flags["--time"] = job_time
        self.submitter_flags["--ntasks"] = job_ntasks
        self.submitter_flags["--job-name"] = job_name
        self.submitter_flags["--output"] = job_logfile
        self.submitter_flags["--error"] = job_logfile
        self.submitter_flags["--mail-type"] = job_mailtype
        if exclusive:
            self.submitter_flags["--exclusive"] = True

        for key, val in self.submitter_flags.items():
            logging.debug("\t\t - %s: %s", key, val)

        submitter_flags_string = ' '.join("%s=%s" % (key,val) for (key,val) in self.submitter_flags.iteritems())
        submitter_flags_string = submitter_flags_string.replace("=True", "")
        logging.debug("\n\t\t - Finalized submitter flags: %s", submitter_flags_string)
        return submitter_flags_string

    def construct_submit_command(self, **submitter_flags):
        """ Constructs the final submit command to put a script onto the batch system 

        Parameters
        ----------
        **submitter_flags
            All arguments conform to ``construct_submitter_flags``

        Returns
        -------
        str
            A combination of submitter (sbatch) and submitter_flags
        """
        return ' '.join([self.submitter, self.construct_submitter_flags(**submitter_flags)])

    def construct_execution_command(self, job_ntasks, executable_commands, executable_tasks):
        """
        Constructs a launcher command and an appropriate hostfile srun

        .. note:: This function assumes it is working in the WORK_DIR of the
                  simulation, and the hostfile_srun is written in whatever directory
                  from which the function is currently being executed

        Parameters
        ----------
        job_ntasks: int
            The total number of tasks that should be allocated when
            creating the hostfile_srun
        executable_commands: list
            A list of strings which contain the executable commands to be
            written into the hostfile_srun
        executable_tasks: list
            A list of ints, which shows how many tasks should be given to each
            command.

        Returns
        -------
        str:
            A string suitable to be passed to ``subprocess.call`` or similar,
            with the launcher for this host (default srun), appropriate flags,
            and a reference to the hostfile_srun.
        """
        logging.debug(40*"- ")
        logging.debug("\nConstructing hostfile_srun...")
        if os.path.exists("hostfile_srun"):
            os.remove("hostfile_srun")

        current_start = 0
        current_end = 0
        for this_executable_command, this_executable_tasks in zip(executable_commands, executable_tasks):
            logging.debug("\t\t - %s tasks left to assign...", job_ntasks)
            logging.debug("\t\t - Assigning %s tasks for %s", this_executable_tasks, this_executable_command)
            current_start = current_end + 1
            current_end = current_start + this_executable_tasks - 1
            with open("hostfile_srun", "a") as hostfile_srun:
                hostfile_srun.write(str(current_start) + "-" + str(current_end) + " ./" + this_executable_command + "\n")
            job_ntasks -= this_executable_tasks
            logging.debug("\t\t - Current Start=%s, Current End = %s", current_start, current_end)
        launcher_flags_string = ' '.join("%s=%s" % (key,val) for (key,val) in self.launcher_flags.iteritems())
        launcher_flags_string = launcher_flags_string.replace("=True", "")
        return ' '.join([self.launcher, launcher_flags_string, "--multi-prog", "hostfile_srun"])  
