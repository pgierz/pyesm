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

from pkg_resources import resource_filename
from ruamel.yaml import YAML, yaml_object

from pyesm.core.database import ESMDatabase
from pyesm.core.helpers import FileDict, SimElement

import pyesm

yaml = YAML()


@yaml_object(yaml)
class Component(SimElement):
    """A generic class to hold methods a specific component can overload."""

    def __init__(self, expid="test", parent_dir=".", config=None):
        """
        Creates a component and an experiment tree, optionally registering it
        in a database.

        Parameters
        ----------
        expid : str, optional
            Default is "test". This is the Experiment ID for your simulation.
        parent_dir : str, optional
            Default is "." (the current working directory). This defines where
            your experiment should built it's directory tree for all of the
            various files.

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

        print("Initializing a component")
        # Set up public attributes
        self.expid = expid
        self.config = config
        # Set up filetypes with empty lists and generate directories
        self.files = {k: FileDict() for k in self._filetypes}
        for filetype in self._filetypes:
            self._register_directory(filetype)
        
        self.NAME = self.config.get('model')
        self.VERSION = self.config.get('version')
        self.TYPE = self.config.get('type')

    
