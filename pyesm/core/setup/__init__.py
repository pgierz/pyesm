"""
Setup contains skeleton classes for constructing collections of Component
objects which share the same:

    + expid
    + Calendar
    + Experiment Directory

Typically, these are tightly coupled Atmosphere/Land Surface/Ocean models
relying on internal libararies to exchange information, such as ``OASIS3mct``
which can be loosely coupled to other components via a script-based interface.

----

The following classes are currently implemented

``SetUp``
    The generic top-level object, equivalent to Component

``SetUpCompute``
    The compute job launcher, equivalent to ComponentCompute

----
"""

import six

from pyesm.core.helpers import SimElement

class SetUp(SimElement):
    """
    Some description of a ``SetUp`` object
    """
    NAME = "setup"
    VERSION = "0.0.0"
    TYPE = "Generic"

    def __init__(self, expid, parent_dir=".", components={}):
        """ Sets up a SetUp object with various Component objects 

        Parameters
        ----------
        expid : str
            The ``expid`` used to identify your experiment.
        parent_dir : str, optional
            Default is "." (the current working directory). Where your
            experiment tree should be built.
        components : dict, optional
            Default is an empty dict. In real use, should be a dictionary in
            the following form: ``{"component_name": component_init_args}``.
            ``component_init_args`` might be a dictionary of
            keyword_argument=value pairs.

        Attributes
        ----------
        NAME : str
            Similar to `helpers.SimElement`. This is the name of your setup, e.g. AWICM
        Version : str
            The version number. Similar to `component.component` or `helpers.SimElement`.
        expid : str
            The experiment id
        component_list : list
            A list containing all components that are part of this setup.
        _parent_dir : str
            The parent directory where this setup is placed.

        """
        super(SetUp, self).__init__()

        self.expid = expid
        self.components = components
        self._parent_dir = parent_dir
