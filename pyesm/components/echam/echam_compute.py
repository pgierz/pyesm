"""
Compute and Post-Processing Jobs for echam6

Written by component_cookiecutter

----
"""

from ruamel.yaml import YAML, yaml_object

from pyesm.core.component.component_compute import ComponentCompute
from pyesm.core.helpers import ComponentFile, ComponentNamelist
from pyesm.components.echam import Echam
from pyesm.components.echam.echam_dataset import r0007

from pkg_resources import resource_filename, resource_string
import inspect
import os
import sys

yaml = YAML()


@yaml_object(yaml)
class EchamCompute(Echam, ComponentCompute):
    """ A docstring. Please fill this out at least a little bit """

    def __init__(self,
                 dataset=r0007,
                 is_coupled=True,
                 *args, **kwargs):
        super(EchamCompute, self).__init__(*args, **kwargs)
        self.is_coupled = is_coupled
        self.oceres = "GR15"  # TODO: We need to get this from the environment...
        self.dataset = dataset(self.res, self.levels, self.oceres)
        self.pool_dir = self.machine.pool_directories['pool']+"/ECHAM6/"

        self._default_prepare_steps = ["read_from_dataset", "read_namelist", "configure_namelist", "copy_files_to_exp_tree"]

    def _compute_requirements(self):
        """ Compute requirements for echam6 """
        self.executeable = "echam6"
        self.command = None
        # Number of nodes is dependent on the cores per compute node. Here, we
        # use a dictionary of dictionaries. The dictionary of the **outer**
        # dictionary is the resolution, the dictionary key of the **inter**
        # dictionary is the number of nodes needed. The hostname decides how
        # many cores per compute node exit.
        self.__nnodes = {"T63": {36: 12, 24: 18}}[self.res]
        self.__nproca = {"T63": {36: 24, 24: 24}}[self.res]
        self.__nprocb = {"T63": {36: 18, 24: 18}}[self.res]
        self.__num_tasks = None
        self.__num_threads = None

    def _prepare_read_from_dataset(self):
        """
        Uses the Dataset to populate the appropriate file dictionaries.

        For each file type described in the Dataset, the current year is used
        to determine the appropriate file to copy from the pool directory. The
        determination is done via the Dataset's ``find`` method, which returns
        a generator. The generator returns files, which may vary based on the
        scenario selected and the current year of the simulation. These files
        are then added to the file dictionary for each file type, which can
        then be used for copying from the filesystem to the experiment file
        tree.

        Notes
        -----
        The following information needed in this method is determined by
        ``EchamCompute`` attributes:
            + The pool directory is machine dependent, and is retrived from the
              ``machine`` attribute attached to ``EchamCompute``.
            + The current year is determined by ``EchamCompute``'s calendar
              attribute, which has an attribute ``current_date.date``. Entry 0 is the
              year.

        See Also
        --------
            Dataset.find : Yields human readable names and filepaths
                appropriate for the year
        """
        for filetype in self._filetypes:
            if hasattr(self.dataset, filetype+"_in_pool"):
                files_for_this_year = self.dataset.find(
                    filetype=filetype+"_in_pool",
                    year=self.calendar.current_date.year)
                for human_readable_name, current_file in files_for_this_year:
                    self.files[filetype][human_readable_name] = ComponentFile(
                        src=self.pool_dir+current_file,
                        dest=getattr(self, filetype+"_dir"))

    def _prepare_read_namelist(
            self,
            NAMELIST_DIR_echam=None
            ):
        """
        Gets the namelist to be used for the experiment.

        This method gets the namelists needed for this experiment. They are
        modified with default values in the step `_prepare_configure_namelist`
        and then modified a second time for experiement specific steps in
        `_prepare_modify_namelist`.

        Parameters
        ----------
        NAMELIST_DIR_echam : <PYESM_ROOT>/components/echam/
            Defaults to None. This is the string pointing to the directory
            where the namelist should be found.
        """
        if not NAMELIST_DIR_echam:
             NAMELIST_DIR_echam = "/namelists/"+self.VERSION+"/"+self.SCENARIO+"/"
        namelist_echam = resource_filename(__name__, NAMELIST_DIR_echam+'namelist.echam')
        self.files['config']['namelist.echam'] = ComponentNamelist(
                src=namelist_echam,
                dest=self.config_dir)

    def _prepare_configure_namelist(self):
        """
        Provides some default configurations for a ``namelist.echam`` file.

        This method does standard processing for a ``namelist.echam`` file
        during a running simulation. Any user-specific configuration occurs in
        a different step; _prepare_modify_namelist.
        """
        # The nml attribute of the ComponentNamelist points to an editable
        # container with the namelist entries:
        namelist = self.files['config']['namelist.echam'].nml
        #
        # Stuff in runctl:
        namelist['runctl']['out_expname'] = self.expid
        # This will depend on the restart frequency:
        namelist['runctl']['dt_start'][0] = self.calendar.start_date.year
        namelist['runctl']['dt_stop'][0] = self.calendar.end_date.year
        namelist['runctl']['lresume'] = False # Need something like self.is_restart...? Probably should point to ``True`` or ``False``
        namelist['runctl']['out_datapath'] = self.work_dir
