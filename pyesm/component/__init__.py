"""
Code for generic components
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here, we collect the initialization routines for a generic component. The following **must** be defined
upon implementation of a ESM Component:

+ Name
+ Version
+ Type

Optionally, you may overload:

+ The filetypes associated with the component
+ The resolution

An additional hook for a SQL database is included, which allows you to register both the Component
description, as well as experiments performed with it to a SQL database to enable quick searching
and organization of work performed.

----

Subclasses include:
^^^^^^^^^^^^^^^^^^^

``ComponentCompute``
    A subclass designed to hold functionality for executing your Component on a supercomputing platform

``ComponentPostProcess``
    A subclass designed to post-processed data produced by a simulation

.. NOTE::
    Not yet implemented.

``ComponentAnalysis``
    A subclass designed to hold common analysis routines to enable users of your component to quickly
    and repeatably perform common analyses of output

.. NOTE::
    Not yet implemented.

``ComponentVisualization``
    A subclass designed to produce graphics of simulation output

.. NOTE::
    Not yet implemented.

----
"""
# Note on names: see https://stackoverflow.com/questions/935378/difference-between-method-and-method

import os

import pyesm.logging as logging
from pyesm.database import ESMDatabase
from pyesm.helpers import FileDict, SimElement

DOWNLOAD_ADDRESS = "http://some/address/of/a/project"

logger = logging.set_logging_this_module()

class Component(SimElement):
    """A generic class to hold methods a specific component can overload."""
    NAME = "component"
    VERSION = "0.0.0"
    TYPE = "Generic"

    def __init__(self, expid="test", resolution=None, parent_dir=".", use_SQL=False):
        """
        Creates a component and an experiment tree, optionally registering it
        in a database.

        Parameters
        ----------
        expid : str, optional
            Default is "test". This is the Experiment ID for your simulation.
        resolution : str, optional
            Default is None. This should correspond to a resolution string
            which allows you to get resolution in lateral/vertical and
            timestep.
        parent_dir : str, optional
            Default is "." (the current working directory). This defines where
            your experiment should built it's directory tree for all of the
            various files.
        use_SQL : bool, optional
            Default is False. If True, a ``ESMDatabase`` instance is attached
            under ``self.database``, and the component Name, Version,
            Lateral/Vertical Resolution and Timestep are entered into the
            database. This is useful for finding experiments performed with the
            same components.


        The following attributes are defined:

        Attributes
        ----------
        expid : str
            The expid
        Name : str
            The name of the component (e.g. ECHAM6, FESOM, MPIOM, OIFS, NEMO,
            ...) Default is "component". **This should be overloaded!** 
        Version : str
            The version of the component, (e.g. ECHAM 6.3.04p2) Default is
            "0.0.0" **This should be overloaded!**
        Type : str
            The "type" of the component (e.g. atmosphere, ocean, ice,
            vegetation, solid earth, ...) Default is "Generic" **This should be
            overloaded**
        LateralResolution : str (or other)
            The lateral resolution used for this component (**Note** This is
            defined by the private method ``_resolution``)
        VerticalResolution : str (or other)
            The vertical resolution used for this component (**Note** This is
            defined by the private method ``_resolution``)
        Timestep : str (or other)
            The timestep used for this component (**Note** This is defined by
            the private method ``_resolution``)
        _nx : int
            Default None. Number of x gridpoints
        _ny : int
            Default None. Number of y gridpoints
        _nz : int
            Default None. Number of z gridpoints
        _ngridpoints : int
            Default None. Total number of gridpoints
        files : dict
            A dictionary of `helpers.FileDict` objects for each of the
            `helpers.SimElement._filetypes` ["config", "forcing", "input",
            "log", "mon", "outdata", "restart"]
        _<filetype>_dir : str
            Each of the filetypes gets an attribute assigned "_<filetype>_dir",
            for example "_outdata_dir", which points to the absolute location
            of the outdata for this specific Component.
        """
        logger.info(80*"=")
        logger.info("\n")
        super(Component, self).__init__(parent_dir=parent_dir+"/"+expid)

        # Set up public attributes
        self.expid = expid


        # Call private methods which might be interesting for initialization
        #
        # NOTE: You only need to overload the _resolution method, the logging will
        # be taken care of automatically:
        if resolution is None:
            self._resolution()
        else:
            self._resolution(resolution)
        self._log_resolution()
        # Set up filetypes with empty lists and generate directories
        self.files = {k: FileDict() for k in self._filetypes}
        for filetype in self._filetypes:
            self._register_directory(filetype)

        # Set up the logger to log everything to the log/component directory for this particular component:
        self.logger = logging.set_logging_this_module(log_dir=self.log_dir)
        self.logger.info(80*"=")
        self.logger.info("\n")
        log_str = " ".join((self.Type + "Model: "+ self.Name +" version: "+ self.Version).split()).upper().center(80)
        self.logger.info(log_str)
        self.logger.info("\n")
        self.logger.info(80*"=")
        self._log_resolution()

        # Keep an optional database of Components and simulations performed with them.
        if use_SQL:
            self.logger.info("Using SQL for component %s", self.Name)
            self.database = ESMDatabase()
            self.database.register_component(self.Name,
                                             self.Version,
                                             self.LateralResolution,
                                             self.VerticalResolution,
                                             self.Timestep)


        # Only finalize log messages if you aren't a subclass
        if type(self).__name__ == "Component":
            self._finalize_log_messages()

    def _resolution(self, res_key=None):
        """
        Defines the resolution and generates the following attributes
        """
        Resolutions = {None:
                        {"LateralResolution": None,
                        "VerticalResolution": None,
                        "Timestep": None,
                        "_nx": None,
                        "_ny": None,
                        "_nz": None,
                        "_ngridpoints": None,
                        }
                      }
        for key, value in Resolutions[res_key].items():
            setattr(self, key, value)

    def _log_resolution(self):
        """ Print out information about the resolution """
        self.logger.info(80*"-")
        info_str="resolution information for "+self.Name
        info_str = " ".join(info_str.split()).upper().center(80)
        self.logger.info(info_str)
        self.logger.info("\n%s will be run with: \nLateralResolution=%s\nVerticalResolution=%s",
                     self.Name,
                     self.LateralResolution,
                     self.VerticalResolution)
        self.logger.info("\n%s will use a computational timestep:\ntimestep=%s",
                     self.Name, self.Timestep)
        self.logger.info(80*"-")

    def _finalize_log_messages(self):
        """ Logging messages to be printed at the very end of the init step.
        Overload this if you want to print out additional information """

        self.logger.info("Initialized a new component: %s", self.Name)
        self.logger.debug("This is known in the current namespace for %s: %s", self.Name, locals())
        self.logger.debug("Here is what is attached to self: %s", dir(self))
        self.logger.info(80*"=")
        self.logger.info("\n")
        self.logger.info(80*"=")
