"""
Classes to hold Compute and PostProcessing jobs for entire setups

----
"""
import importlib
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
    def __init__(self, env):
        self.expid = env.get("EXP_ID", "test")

        calendar = esm_calendar.Calendar(calendar_type=1)

        initial_date = env.get("INITIAL_DATE", None)
        final_date = env.get("FINAL_DATE", None)

        initial_date = env.get("INITIAL_DATE_"+self.NAME, initial_date)
        final_date = env.get("FINAL_DATE_"+self.NAME, final_date)

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

        self.machine = Host(os.environ.get("machine_name"),
                            batch_system=os.environ.get("batch_system", None))

        self.total_tasks = 0
        self.job_time = self.compute_time = env.get("compute_time", None)

        for component_key, component_value in self.components.items():
            if issubclass(type(component_value), ComponentCompute):
                this_component = component_value
            elif isinstance(component_value, dict):
                this_component = self._register_component(component_key, **component_value)
            else:
                error_message = "Give an initialized component, or a dict of arguments to construct one!"
                raise TypeError(error_message)
            setattr(self, this_component.NAME, this_component)
            self.components[component_key] = this_component

    def _register_component(self, component_name, **component_kwargs):
        """ Dynamically import a ComponentCompute, and initialize a ComponentCompute

        This dynamically imports ``component_name``'s ``ComponentCompute``
        class, initializes it using ``component_args``, and registers it to the
        SetUp as an attribute

        Parameters
        ----------
        component_name : str
            The name of the component, which will be used to load the module.
        component_args : list or dict
            A collection of arguments or keyword arguments to pass to the
            component initializer.

        Example
        -------

        >>> my_setup = SetUpCompute._register_component(component_name="component",
        ...                                             components_args={"arg1": "value1"})

        The following would happen in the background:
        >>> from component import ComponentCompute
        >>> example_component = ComponentCompute(arg1="value1")

        Imagine we have a uninitialized setup object, called my_setup as above

        >>> my_setup.Component = example_component
        """
        this_component = dynamically_load_and_initialize_component(component_name,
                                                                   "compute",
                                                                   calendar=self.calendar,
                                                                   machine=self.machine,
                                                                   **component_kwargs)
        return this_component

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
