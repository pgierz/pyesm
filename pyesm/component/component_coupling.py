"""
General Couple Class that contains functionality for coupling two model types together.

- - - -
"""

# Standard Library Imports
import glob
import json
import logging
import os
import tempfile
import warnings

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

                self.__compatible_other_model_types = type(self).COMPATIBLE_COUPLE_TYPES

                self.couple_attrs = {}
                self._grid_string = None
                self._cleanup_list = []
                self._cdo_stderr = open(self.couple_dir+"/"+self.Name+"Couple_cdo_log", "w")
                self.CDO = cdo.Cdo(logging=True, logFile=self._cdo_stderr)
                self.NCO = nco.Nco(debug=True)

        def correct_lonlat_order(self, fin, fout=None):
                """
                Corrects the order of dimensionality for lon/lat in ``fin``.

                TODO: Longer description.

                Parameters
                ----------
                fin : str ::
                        The filename you want to correct

                Returns
                -------
                fout : str ::
                        The filenmae with the corrected lon/lat dimensionality.
                """
                ofile = self.NCO.ncpdq(fin, output=fout, arrange=("lat", "lon"))
                print(ofile)
                return ofile

        def prepare_send(self):
                pass  # Nothing to do yet...

        def send(self):
                for other_model_type in self.__compatible_other_model_types:
                        try:
                                getattr(self, "send_"+other_model_type)()
                        except AttributeError:
                                warnings.warn(self.Name+" has no method to send to "+other_model_type)

        def finalize_send(self):
                pass

        def prepare_recieve(self):
                for other_model_type in self.__compatible_other_model_types:
                        self._define_couple_files(other_model_type)
                        self._get_couple_files(other_model_type)
                        self._attach_names(other_model_type)
                        self._remap_forcing_to_thismodel_grid(other_model_type)

        def recieve(self):
                for other_model_type in self.__compatible_other_model_types:
                        try:
                                getattr(self, "recieve_"+other_model_type)()
                        except AttributeError:
                                warnings.warn("tried to run recieve_"+other_model_type+"(): "+self.Name+" has no method to recieve from "+other_model_type)

        def finalize_recieve(self):
                pass

        def _generate_grid_weights(self, other_model_type, regrid_type):
                other_model_forcing_file = self.files["couple"][other_model_type+"_file"]._current_location
                if self._grid_string:
                        this_model_griddes = self._grid_string
                else:
                        this_model_griddes = self.files["couple"][self.Type+"_grid"]._current_location
                other_model_griddes = self.files["couple"][other_model_type+"_grid"]._current_location

                method_to_generate_this_weight = getattr(self.CDO, "gen"+regrid_type)
                weight_file = self.couple_dir+"/"+other_model_type+"_weights_for_remap"+regrid_type+".nc"
                if not os.path.exists(weight_file):
                        logging.info("Generating grid weights for:", "remap"+regrid_type)
                        method_to_generate_this_weight(this_model_griddes,
                                        input="-setgrid,"+other_model_griddes+" "+other_model_forcing_file,
                                        output=weight_file,
                                        options="-P 8")
                return ",".join([this_model_griddes, weight_file])

        def _define_couple_files(self, other_model_type):
                for other_model_type in self.__compatible_other_model_types:
                    self.files["couple"][other_model_type+"_file"] = \
                                    ComponentFile(src=self.couple_dir+"/../"+other_model_type+"/"+other_model_type+"_file_for_"+self.Type+".nc",
                                                  dest=self.couple_dir+"/"+"_".join([other_model_type, "file", str(self.calendar)])+".nc")
                    self.files["couple"][other_model_type+"_grid"] = \
                                    ComponentFile(src=self.couple_dir+"/../"+other_model_type+"/"+other_model_type+".griddes",
                                                  dest=self.couple_dir+"/"+"_".join([other_model_type, "grid", str(self.calendar)]))
                    self.files["couple"][other_model_type+"_vars"] = \
                                    ComponentFile(src=self.couple_dir+"/../"+other_model_type+"/"+other_model_type+"_vars.json",
                                                  dest=self.couple_dir+"/"+"_".join([other_model_type, "var", str(self.calendar)]))

        def _get_couple_files(self, other_model_type):
                for meta in ["file", "grid", "vars"]:
                        self.files["couple"]["_".join([other_model_type, meta])].digest()

        def _attach_names(self, other_model_type):
                with open(self.files["couple"][other_model_type+"_vars"]._current_location) as variable_file:
                        self.couple_attrs[other_model_type] = json.load(variable_file)

        def _remap_forcing_to_thismodel_grid(self, other_model_type, regrid_type="con"):
                """
                Tries to regrid a forcing file to the recieving model's grid.

                When coupling two models togther, we try to use the grid
                weights in the other model's couple folder, if they exist. This
                speeds up remapping considerably. If they don't exist, they
                should be automatically recomputed. The remap type can be
                selected via the argument ``remap_type``

                Parameters
                ----------
                other_model_type : str
                        the other type of model to couple to; e.g. ``ice``,
                        ``atmosphere``, ``ocean``, ``solid_earth``, ect...
                regrid_type : str, optional, default="con"
                        which type of remapping to use. See the CDO manual for
                        available types. Defaults to conservative remapping,
                        since it usually makes sense to conserve energy or
                        mass; unless you are living in a non-physical universe,
                        where energy and mass are not conserved ;-) In this
                        case, I'd bail out and try to find a universe where
                        mathematics make sense.
                """
                remap_argument = self._generate_grid_weights(other_model_type, regrid_type)
                other_model_forcing_on_thismodel_grid = self.CDO.remap(
                                remap_argument,
                                input=self.files["couple"][other_model_type+"_file"]._current_location,
                                output=self.couple_dir+"/"+other_model_type+"_remap"+regrid_type+"_to_"+self.Type+"_grid.nc",
                                options="-P 8")


def cleanup_after_send(meth):
        """ Cleans up after the send method of a ComponentCouple has been called"""
        def new_meth(*args, **kwargs):
                original_return_value = meth(*args, **kwargs)
                args[0].files['couple'].digest()
                for tmpfile in args[0]._cleanup_list:
                        os.remove(tmpfile)
                args[0].CDO.cleanTempDir()
                return original_return_value
        return new_meth

def write_couple_vars_to_json(meth):
        """ Writes a defined dictionary variable_description to a JSON file """
        def new_meth(*args, **kwargs):
                variable_description = meth(*args, **kwargs)
                with open(args[0].couple_dir + "/" + args[0].Type+"_vars.json", "w") as variable_file:
                        json.dump(variable_description, variable_file)
                return variable_description
        return new_meth
