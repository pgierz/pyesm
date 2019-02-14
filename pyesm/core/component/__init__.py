"""
Code for generic components
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here, we collect the initialization routines for a generic component. The following **must** be defined
upon implementation of a ESM Component:

+ NAME
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

from ruamel.yaml import YAML, yaml_object

from pyesm.core.database import ESMDatabase
from pyesm.core.helpers import FileDict, SimElement


yaml = YAML()


@yaml_object(yaml)
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
            under ``self.database``, and the component NAME, Version,
            Lateral/Vertical Resolution and Timestep are entered into the
            database. This is useful for finding experiments performed with the
            same components.


        The following attributes are defined:

        Attributes
        ----------
        expid : str
            The expid
        NAME : str
            The name of the component (e.g. ECHAM6, FESOM, MPIOM, OIFS, NEMO,
            ...) Default is "component". **This should be overloaded!** 
        Version : str
            The version of the component, (e.g. ECHAM 6.3.04p2) Default is
            "0.0.0" **This should be overloaded!**
        Type : str
            The "type" of the component (e.g. atmosphere, ocean, ice,
            vegetation, solid earth, ...) Default is "Generic" **This should be
            overloaded**
        """
        super(Component, self).__init__(parent_dir=parent_dir+"/"+expid)

        # Set up public attributes
        self.expid = expid

        # Set up filetypes with empty lists and generate directories
        self.files = {k: FileDict() for k in self._filetypes}
        for filetype in self._filetypes:
            self._register_directory(filetype)
        # Set up resolution:
        self._resolution(resolution)

        # Keep an optional database of Components and simulations performed with them.
        if use_SQL:
            self.database = ESMDatabase()
            # FIXME: The database needs to get fixed to handle a more generic
            # resolution description...
            self.database.register_component(self.NAME,
                                             self.Version,
                                            ) 


    def _resolution(self, res_key=None):
        """
        Defines the resolution and generates the following attributes
        """
        for key, value in self.Resolutions[res_key].items():
            setattr(self, key, value)

