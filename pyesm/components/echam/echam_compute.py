"""
Compute and Post-Processing Jobs for echam6

This module contains classes used to set up EchamCompute and
EchamPostprocessing objects. All classes inherit from the base Echam class, and
depending on their purpose, ComponentCompute or ComponentPostprocess

----
"""
import os
from pkg_resources import resource_filename

from ruamel.yaml import YAML, yaml_object

from pyesm.core.component.component_compute import ComponentCompute
from pyesm.core.helpers import ComponentFile, ComponentNamelist
from pyesm.components.echam import Echam
from pyesm.components.echam.echam_dataset import r0007


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
        self.oceres = 'GR15'  # TODO: We need to get this from the environment...
        self.dataset = dataset(self.res, self.levels, self.oceres)
        self.pool_dir = self.machine.pool_directories['pool']+'/ECHAM6/'

        self._default_prepare_steps = [
            'files_from_dataset',
            'files_from_restart_in',
            'configure_files_default',
            'configure_files_user',
            'read_namelist',
            'configure_namelist_default',
            'configure_namelist_user',
            'copy_files_to_exp_tree',
            ]

    def _compute_requirements(self):
        """ Compute requirements for echam6 """
        self.executeable = 'echam6'
        self.command = None
        # Number of nodes is dependent on the cores per compute node. Here, we
        # use a dictionary of dictionaries. The dictionary of the **outer**
        # dictionary is the resolution, the dictionary key of the **inter**
        # dictionary is the number of nodes needed. The hostname decides how
        # many cores per compute node exit.
        self._nnodes = {'T63': {36: 12, 24: 18}}[self.res]
        self._nproca = {'T63': {36: 24, 24: 24}}[self.res]
        self._nprocb = {'T63': {36: 18, 24: 18}}[self.res]
        self._num_tasks = None
        self._num_threads = None

    def _prepare_files_from_dataset(self):
        """
        Uses the Dataset to populate the appropriate file dictionaries.

        This replaces the normal steps for files_from_forcing_in and
        files_from_input_in.

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

        The Dataset currently implements paths for the following filetypes:
        + ``forcing``
        + ``input``

        The restart filetype dictionary is propulated in
        _prepare_files_from_restart_in


        See Also
        --------
            Dataset.find : Yields human readable names and filepaths
                appropriate for the year
        """
        for filetype in self._filetypes:
            if hasattr(self.dataset, filetype+'_in_pool'):
                files_for_this_year = self.dataset.find(
                    filetype=filetype+'_in_pool',
                    year=self.calendar.current_date.year
                    )
                for human_readable_name, current_file in files_for_this_year:
                    self.files[filetype][human_readable_name] = ComponentFile(
                        src=self.pool_dir+current_file,
                        dest=getattr(self, filetype+'_dir')
                        )

    def _prepare_files_from_restart_in(self):
        """
        Gets the restart files to be used for the experiment that are relevant
        for echam.

        This method gets restart files from either:
        + Somewhere on the filesystem (If you are doing a "cold start",
          restarts are taken from the pool directory, if you are doing a restart
          from a different experiment, restarts are taken from the environmental
          variables INI_RESTART_DIR_echam)
        + The experiments own restart directory

        Notes
        -----
        The following relevant variables can be set in the shell runscript to
        override certain defaults:
        + INI_PARENT_EXP_ID_echam
        + INI_PARENT_DATE_echam
        + INI_RESTART_DIR_echam
        """
        if self.calendar.run_number == 1:
            restart_expid = os.environ.get('INI_PARENT_EXP_ID_echam', 'khw0030')
            restart_date = os.environ.get('INI_PARENT_DATE_echam', '22941231')
            restart_files_directory = os.environ.get(
                'INI_RESTART_DIR_echam',
                self.pool_dir+'/../MPIESM/restart/dev/'+restart_expid+'/restart/echam6'
                )
        else:
            restart_expid = self.expid
            restart_date = self.calendar.previous_date
            restart_files_directory = self.restart_dir

        # Get the restart files
        invalid_streams = ['yasso', 'jsbid', 'jsbach', 'surf', 'nitro', 'veg', 'land']
        all_files_in_restart_dir = os.listdir(restart_files_directory)
        # Use a set to automatically discard duplicates, since we are going
        # over two loops:
        restart_files = set()
        for invalid_stream in invalid_streams:
            for f in all_files_in_restart_dir:
                if invalid_stream in f:
                    continue
                if f.startswith('restart_'+restart_expid) and restart_date in f:
                    restart_files.add(f)
        for f in restart_files:
            self.files['restart'][f] = ComponentFile(
                src=restart_files_directory+'/'+f,
                dest=self.restart_dir
                )

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
            where the namelist should be found. If possible, this is retrieved
            from the environment.
        """
        if not NAMELIST_DIR_echam:
             NAMELIST_DIR_echam = os.environ.get(
                     'NAMELIST_DIR_echam',
                     '/namelists/'+self.VERSION+'/'+self.SCENARIO+'/')
        namelist_echam = resource_filename(__name__, NAMELIST_DIR_echam+'namelist.echam')
        self.files['config']['namelist.echam'] = ComponentNamelist(
                src=namelist_echam,
                dest=self.config_dir)

    def _prepare_configure_namelist_default(self):
        """
        Provides some default configurations for a ``namelist.echam`` file.

        This method does standard processing for a ``namelist.echam`` file
        during which will be used running simulation. Any user-specific
        configuration occurs in a different step; _prepare_modify_namelist.

        Some of the settings chosen depend on the compute host configuration
        (attached to ComponentCompute classes as self.machine) as well as the
        resolution.
        """
        ######################################################################
        # The nml attribute of the ComponentNamelist points to an editable
        # dictionary-like container with the namelist entries:
        namelist = self.files['config']['namelist.echam'].nml

        ######################################################################
        # Changes in runctl:
        #
        namelist['runctl']['out_expname'] = self.expid
        # dt_start, dt_stop and dt_resume point to "$pseudo_date_start_echam",
        # "$pseudo_date_end_echam", and "$pseudo_date_resume_echam"
        #
        # Unfortunately the shell version doesn't really explain what these
        # are, so just placeholder strings for now to demonstrate that
        # namelists can be changed:
        namelist['runctl']['dt_start'] = self.calendar.start_date.year
        namelist['runctl']['dt_stop'] = self.calendar.end_date.year
        namelist['runctl']['dt_resume'] = self.calendar.start_date.year
        # Get lresume from the environment; and cast to boolean since it
        # probably is a "1" or "0" string:
        if self.calendar.run_number > 1:
            lresume_in_namelist = True
        else:
            lresume_in_namelist = bool(os.environ.get('LRESUME_echam', False))
        namelist['runctl']['lresume'] = lresume_in_namelist
        namelist['runctl']['out_datapath'] = self.work_dir
        namelist['runctl']['lcouple'] = self.is_coupled
        # Allow for 6-hourly output:
        if os.environ.get('OUTPUT6H_echam', None):
            namelist['runctl']['putdata'] = [6, 'hours', 'last', 0]
        # TODO:
        # namelist['runctl']['putrerun']
        # namelist['runctl']['delta_time']

        ######################################################################
        # Changes in parctl
        #
        # We get _nproca and _nprocb attributes (defined in the compute
        # requirements), and determine the values we need based upon the number
        # of cores available on the compute nodes (defined in compute_host
        # configuration file)
        namelist['parctl']['nproca'] = self._nproca[self.machine.cores]
        namelist['parctl']['nprocb'] = self._nprocb[self.machine.cores]


        ######################################################################
        # Changes in radctl
        #
        # Allow for user defined greenhouse gas values:
        for ghg_in_env, ghg_in_namelist in zip(
                ['CO2_echam', 'CH4_echam', 'N2O_echam'],
                ['co2vmr', 'ch4vmr', 'n2ovmr']):
            if os.environ.get(ghg_in_env, None):
                namelist['radctl'][ghg_in_namelist] = float(os.environ.get(ghg_in_env))

        # Allow for user defined orbital values:
        for orb_in_env, orb_in_namelist in zip(
                ['CECC_echam', 'COBLD_echam', 'CLONP_echam'],
                ['cecc', 'cobld', 'clonp']):
            if os.environ.get(orb_in_env, None):
                namelist['radctl'][orb_in_namelist] = float(os.environ.get(orb_in_env))
                del namelist['radctl']['yr_perp']
                namelist['runctl']['l_orbvsop87'] = False
