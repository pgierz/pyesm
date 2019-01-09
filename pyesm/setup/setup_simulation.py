"""
Classes to hold Compute and PostProcessing jobs for entire setups


----
"""
import importlib
import os
import sys

import pyesm.logging as logging
from pyesm.time_control import EsmCalendar
from pyesm.setup import SetUp
from pyesm.time_control import EsmCalendar
from pyesm.compute_hosts import Host

logger = logging.set_logging_this_module()


class SetUpCompute(SetUp):
    """
    Container for a tightly-coupled simulation launcher
    """
    def __init__(self, expid, parent_dir=".", components=None,
                 initial_date="1850101", final_date="18530101", delta_date="years=1",
                 compute_time="00:30:00"):
        """
        Parameters
        ----------
        expid : str
            The experiment ID. Sent to SetUp init method.
        parent_dir : str, optional
            The parent directory. Sent to SetUp init method.
        components : dict, optional
            The component dictionary. See SetUp documentation. Sent to SetUp init method.
        initial_date : str, optional
            Default is ``"18500101"``. Used to initialize the calendar.
        final_date : str, optional
            Default is ``"18530101"``. Used to initialize the calendar
        delta_date : str, optional
            Default is "years=1". Should be a string compatiable for
            `time_control.delta_date`, e.g. ``"years=1, months=1, days=1,
            hours=1, minutes=1, seconds=1"``
        compute_time : str. optional
            The total time this job should run for. Should be a string in the format "HH:MM:SS"
        """
        super(SetUpCompute, self).__init__(expid, parent_dir, components)

        self.calendar = EsmCalendar(initial_date, final_date, delta_date)
        self.host = Host()
        self.batch_system = self._load_batch_system()

        self.total_tasks = 0
        self.job_time = self.compute_time = os.environ.get("compute_time", compute_time)

        for component_name, component_args in components.items():
            self._register_component(component_name, component_args)

    def _register_component(self, component_name, component_args):
        """ Dynamically import a ComponentCompute, and initialize a ComponentCompute

        This dynamically imports a component's ``ComponentCompute`` class, and
        registers it to the SetUp as an attribute

        Parameters
        ----------
        component_name : str
            The name of the component, which will be used to load the module.
        component_args : list or dict
            A collection of arguments or keyword arguments to pass to the
            component initializer.

        Example
        -------

        >>> my_setup = SetUpCompute._register_component(component_name="component", components_args={"arg1": "value1"})
        # The following would happen in the background:
        >>> from component import ComponentCompute
        >>> example_component = ComponentCompute(arg1="value1")
        # Imagine we have a uninitialized setup object, called my_setup as above
        >>> my_setup.Component = example_component
        """
        # This method involves some serious dark magic. Please don't touch.

        # Here, we import the ComponentCompute method of Component. This would be:
        #
        # >>> from component import ComponentCompute
        #
        importlib.import_module("pyesm."+component_name+"."+component_name+"_simulation",
                                component_name.capitalize()+"Compute")
        # The next part is for debugging:
        key_list = sorted(sys.modules.keys())
        maxlen = 3+len(max(key_list, key=len))
        debug_str="{:<"+str(maxlen)+"}{:<"+str(maxlen)+"}{:<}"
        for key_a, key_b, key_c in zip(key_list[::3], key_list[1::3], key_list[2::3]):
            logger.debug(debug_str.format(key_a, key_b, key_c))

        # Get the component's init method, initialize the component, and
        # register it to the setup under Component.Name This would be the same
        # as:
        #
        # >>> a_component_kwargs = {"arg1": value1, "arg2": value2}
        # >>> a_component = ComponentCompute(**a_component_kwargs)
        #
        this_component_init_method = getattr(sys.modules["pyesm."+component_name+"."+component_name+"_simulation"],
                                             component_name.capitalize()+"Compute")
        this_component = this_component_init_method(parent_dir=self._parent_dir, calendar=self.calendar, **component_args)
        setattr(self, this_component.Name, this_component)
        self.component_list.append(this_component)

    def _load_batch_system(self):
        """ Loads the batch system interface appropriate for this computing
        host

        Similar to _register_component, this dynamically loads the appropriate
        batch system for the current computing host, and returns an initialized
        object to be used by SetUpCompute
        """
        batch_system = self.host.batch_system
        importlib.import_module("pyesm.batch_systems."+batch_system, batch_system.capitalize())
        this_batch_system = getattr(sys.modules["pyesm.batch_systems."+batch_system], batch_system.capitalize())
        # TODO: Here we need to add the compute resource account if it is applicable...
        return this_batch_system(self.host)

    def _run_method(self, Method, SetUp_Last=True):
        """ Run a Method for all registered components and any "top-level"
        magic that might need to happen for the SetUp

        A requirement here is that the Method **does not take any arguments**
        other than ``self``. By default, the SetUp method is called **last**.
        This allows a method SetUpCompute.work() to be defined so that the
        actual execution command of the models occurs here. 
        
        Parameters
        ----------
        Method : str
            The name of the method to run
        SetUp_Last : bool, optional
            Default is ``True``. Order in which to run the method: components
            first, then setup, or other way around.
        """
        SimPart_List = (self.component_list + [self]) if SetUp_Last else ([self] + self.component_list)
        for SimPart in SimPart_List:
            SimPart_Method = getattr(SimPart, Method, None)
            if callable(SimPart_Method):
                SimPart_Method()


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
        for component in self.component_list:
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

        executable_commands = [component.command for component in self.component_list]
        executable_tasks = [component.num_tasks for component in self.component_list]
        execution_command = self.batch_system.construct_execution_command(self.total_tasks, executable_commands, executable_tasks)

    def _cleanup_checkpoint_simulation(self):
        # IDEA: After the simulation has finished, create a checkpoint in a VCS to easily
        # rollback or branch off from a simulation.
        self.commit_to_VCS()
        # IDEA: After everything has finished (for the first run) register the simulation in a
        # sharable database, to avoid repeating it and potentially wasting compute resources.
        self.register_SQL()

