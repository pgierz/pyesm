"""
General Couple Class that contains functionality for coupling two model types together.

- - - -
"""

# Standard Library Imports
import glob
import logging
import os
import tempfile

# This Library imports
from pyesm.component.component_simulation import ComponentCompute
from pyesm.helpers import ComponentFile, FileDict
from pyesm.time_control import CouplingEsmCalendar

# "External" Imports:
import cdo
import nco

class ComponentCouple(ComponentCompute):
        """ Contains functions to generalize coupling between two model types """
        COMPATIBLE_COUPLE_TYPES = []  # Should be a list of general types that this component can couple to

        def __init__(self, **ComponentComputeArgs):
                super(ComponentCouple, self).__init__(**ComponentComputeArgs)

                try:
                    assert isinstance(self.calendar, CouplingEsmCalendar)
                except AssertionError:
                    raise TypeError("You must supply a calendar with coupling functionality: CouplingEsmCalendar, and not %s" % type(self.calendar))

                self.files["couple"] = FileDict()
                self._register_directory("couple", use_Name="generic")

                self.__compatible_couple_types = type(self).COMPATIBLE_COUPLE_TYPES

                self._cleanup_list = []
                self._cdo_stderr = open(self.couple_dir+"/"+self.Name+"Couple_cdo_log", "w")
                self.CDO = cdo.Cdo(logging=True, logFile=self._cdo_stderr)

        def prep_recieve(self):
                for couple_type in self.__compatible_couple_types:
                    self.files["couple"][couple_type+"_file"] = \
                                    ComponentFile(src=self.couple_dir+"/../"+couple_type+"/"+couple_type+"_file_for_"+self.Type+".nc",
                                                  dest=self.couple_dir+"/"+"_".join([couple_type, "file", str(self.calendar)]))
                    self.files["couple"][couple_type+"_grid"] = \
                                    ComponentFile(src=self.couple_dir+"/../"+couple_type+"/"+couple_type+".griddes",
                                                  dest=self.couple_dir+"/"+"_".join([couple_type, "grid", str(self.calendar)]))
                    self.files["couple"][couple_type+"_vars"] = \
                                    ComponentFile(src=self.couple_dir+"/../"+couple_type+"/"+couple_type+"_vars.dat",
                                                  dest=self.couple_dir+"/"+"_".join([couple_type, "var", str(self.calendar)]))
        def recieve(self, other_type):
                for meta in ["file", "grid", "vars"]:
                        for this_file in self.files["couple"]["_".join([other_type, meta])]:
                                this_file.digest()
                getattr(self, recieve+"_"+other_type)()
