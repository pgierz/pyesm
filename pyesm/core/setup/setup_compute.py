"""
Classes to hold Compute and PostProcessing jobs for entire setups

----
"""
import importlib
from pkg_resources import resource_filename
import os
import sys

from ruamel.yaml import YAML, yaml_object

import pyesm.core.logging as logging
from pyesm.core.component.component_compute import ComponentCompute
from pyesm.core.compute_hosts import Host
from pyesm.core.time_control import EsmCalendar, esm_calendar
from pyesm.core.dark_magic import dynamically_load_and_initialize_component

yaml = YAML()


@yaml_object(yaml)
class SetUpCompute(object):
    """
    Container for a tightly-coupled simulation launcher
    """
    def __init__(self):
        env = os.environ
        this_setup = None
        self.components = {}
        # Read a YAML if given
        if 'read_yaml' in env:
            print("Reading yaml...")
            for yaml_file in env['read_yaml']:
                self.personal_config.update(self.read_yaml(yaml_file))
                this_setup = self.personal_config.get('setup_name', None)
                print(self.personal_config)

        # Read the environment
        self.NAME = env.get('setup_name', this_setup)
        if 'standalone' in self.NAME:
            self.NAME = self.NAME.split("_standalone")[0]
            for var in env:
                if var.endswith(self.NAME+"_standalone") and var.split("_"+self.NAME+"_standalone")[0] not in env:
                    env[var.split("_"+self.NAME+"_standalone")[0]] = env[var]
                    del env[var]
        
        # Read Default YAML File for this setup (e.g. AWICM, ECHAM, usw)
        self.config = self.read_yaml(self.NAME)
        
        # Everything the user put in a YAML file
        if 'read_yaml' in env:
            self.config.update(self.personal_config)
        
        for component in self.components.values():
            self.update_component_from_env(component, env)

        self.expid = env.get("EXP_ID", "test")

        calendar = esm_calendar.Calendar(calendar_type=1)

        initial_date = env.get("INITIAL_DATE", None)
        final_date = env.get("FINAL_DATE", None)

        initial_date = esm_calendar.Date(initial_date, calendar)
        final_date = esm_calendar.Date(final_date, calendar)
        delta_date = [int(env.get("NYEAR", 0)),
                      int(env.get("NMONTH", 0)),
                      int(env.get("NDAY", 0)),
                      0,
                      0,
                      0]

        delta_date = esm_calendar.Date.from_list(delta_date) # ...?

        self.calendar = EsmCalendar(initial_date, final_date, delta_date)

        # Computation requirments might be defined in the environment: 
        self.machine = Host(env.get("machine_name"),
                            batch_system=env.get("batch_system", None))
        self.total_tasks = 0
        self.job_time = self.compute_time = env.get("compute_time", None)

        self.preform_replacements()


    def dump_yaml_to_stdout(self):
        all_yamls = {}
        all_yamls.update(self.config)
        with open('yaml_dump_setup_configs.yaml', 'w') as yml:
            yaml.dump(all_yamls, yml)
        for component in self.components:
            all_yamls['included_component_'+component] = self.components[component].config
        yaml.dump(all_yamls, sys.stdout)
        with open('yaml_dump_all_configs.yaml', 'w') as yml:
            yaml.dump(all_yamls, yml)

    def find_yaml_path(self, component_name):
        if '/' in component_name:
            return resource_filename('pyesm', component_name)
        if component_name.endswith('.yaml'):
            return resource_filename('pyesm', '/components/'+component_name)
        else:
            return resource_filename('pyesm', '/components/'+component_name+'.yaml')

    def read_yaml(self, yaml_file, current_config={}):
        print(80*"#")
        print("Top of method read_yaml")
        print(self.NAME, ":", current_config)
        yaml_filepath = self.find_yaml_path(yaml_file)
        with open(yaml_filepath) as yml:
            current_config.update(yaml.load(yml))
        print(80*"#")
        print(current_config)
        if 'further_reading' in current_config:
            print("Reading further_reading chapter in %s", yaml_file)
            for additional_yaml in current_config['further_reading']:
                current_config['further_reading'].remove(additional_yaml)
                self.read_yaml(additional_yaml, current_config)
        if 'include_submodels' in current_config:
            for submodel in current_config['include_submodels']:
                current_config['include_submodels'].remove(submodel)
                submodel_config = {}
                this_component = ComponentCompute(
                        config=self.read_yaml(
                            submodel, 
                            current_config=submodel_config
                            )
                        )
                print(this_component)
                print(dir(this_component))
                self.components[this_component.NAME] = this_component

        return current_config

    def update_component_from_env(self, component, env):
        for key, value in env.items():
            if key.endswith("_"+component.NAME):
                component.config[key] = value


    def preform_replacements(self):
        for key, value in self.config.items():
            if key.startswith("choose_"):
                chosen_key = key.replace("choose_", "")
                if chosen_key in self.config:
                    chosen_value = self.config[chosen_key]
                    if chosen_value in value:
                        for subkey, subvalue in self.config[key][chosen_value]:
                            self.config.setdefault(subkey, subvalue)
                    else:
                        print("Warning: Unknown %s" % chosen_key)
                else:
                    print("Error")
                    sys.exit(4)
                self.config.remove(key)

    def _call_phase(self, Phase, SetUp_Last=True):
        """ Run a Phase for all registered components and any "top-level"
        magic that might need to happen for the SetUp

        A requirement here is that the Phase **does not take any arguments**
        other than ``self``. By default, the SetUp method is called **last**.
        This allows a method SetUpCompute.work() to be defined so that the
        actual execution command of the models occurs here.

        Parameters
        ----------
        Phase : str
            The name of the Phase to run
        SetUp_Last : bool, optional
            Default is ``True``. Order in which to run the method: components
            first, then setup, or other way around.
        """
        SimPart_List = (self.components.values() + [self]) if SetUp_Last else ([self] + self.components.values())
        logging.debug("SimPart_List = %s", SimPart_List)
        for SimPart in SimPart_List:
            logging.debug("Trying to call %s steps for %s", Phase, SimPart.NAME)
            SimPart_Phase = getattr(SimPart, Phase, None)
            if callable(SimPart_Phase):
                logging.debug("Calling %s...", Phase)
                SimPart_Phase()


    def prepare(self):
        """ Prepare steps that occur for the **entire** setup """
        pass

    def work(self):
        """ Get total compute requirements and figure out the launching command

        The following steps are performed here:

        #. The total compute requirements are added up.
        #. The submission command is constructed.
        #. The simulation is sent to the queue.
        #. The script waits until the simulation completes before continuing
           with cleanup.
        """

        steps = ["add_up_compute_requirements", "set_exec_command", "submit_job"]

    def _work_add_up_compute_requirements(self):
        """ Adds up the total number of tasks needed for each component in order to submit a correct batch job """
        for component in self.components.values():
            if component.num_tasks is None:
                component.num_tasks = 0
            self.total_tasks += component.num_tasks

    def _work_set_exec_command(self):
        """ Generates the command that will be sent to the supercomputer via
        ``subprocess.check_output``

        This performs a few substeps:

        #. Gets appropriate submit flags based upon the requirements specified
           by the components
        #. Gets launcher and appropritate flags
        #. Combines these to a submission command, which is logged to main
           output and stored in a variable for use in the next step

        """
        submitter_flag_args = {
                            "job_flag": "compute",
                            "job_time": self.job_time,
                            "job_ntasks": self.total_tasks,
                            "job_name": self.expid,
                            "job_logfile": "out.$$",
                            "job_mailtype": "FAIL",
                            "exclusive": True
                            }
        submit_command = self.batch_system.construct_submit_command(**submitter_flag_args)

        executable_commands = [component.command for component in self.components.values()]
        executable_tasks = [component.num_tasks for component in self.components.values()]
        execution_command = self.batch_system.construct_execution_command(self.total_tasks, executable_commands, executable_tasks)

    def _cleanup_checkpoint_simulation(self):
        # IDEA: After everything has finished (for the first run) register the simulation in a
        # sharable database, to avoid repeating it and potentially wasting compute resources.
        # self.register_SQL()
        pass
