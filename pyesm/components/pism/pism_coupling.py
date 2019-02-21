"""

Allows for coupling from a generic ``atmosphere`` model to ``PISM``

- - - -
"""
# Standard Library Imports:
import glob
import json
import logging
import os
import tempfile

# This Library Imports:
from pyesm.component.component_coupling import ComponentCouple, cleanup_after_send, write_couple_vars_to_json
from pyesm.pism.pism_simulation import PismCompute
from pyesm.helpers import load_environmental_variable_1_0, ComponentFile, FileDict
from pyesm.time_control import CouplingEsmCalendar

# External Imports
import cdo
import nco
import xarray as xr


CDO = cdo.Cdo()
NCO = nco.Nco()


class PismCouple(PismCompute, ComponentCouple):
    """ Functionality to couple PISM with other models """
    COMPATIBLE_COUPLE_TYPES = ["atmosphere", "solid_earth"]

    def __init__(self, **PismComputeArgs):
        super(PismCouple, self).__init__(**PismComputeArgs)

    def recieve_atmosphere(self):
        """ Bundles up functionality to recieve a generic atmoshpere file """
        # TODO: How to get PISM_ATMO_couple_method in here?
        if PISM_ATMO_couple_method == "downscale_static":
                regrid_downscale()
        elif PISM_ATMO_couple_method == "interpolate":
                regrid_remap()
        elif PISM_ATMO_couple_method == "remap":
                regrid_remap()

    @cleanup_after_send
    def send_solid_earth(self):
        """ Sends a generic ice sheet field for use with a solid earth model"""
        self._generate_solid_earth_forcing_file()
        self._describe_grid()
        self._describe_variables()

    def _generate_solid_earth_forcing_file(self):
        """ Generates a solid earth forcing from ice output. 

        Some questions that still need to be clarified:
        1. Do we want to send the newest timestep?
        2. What happens if PISM restarts during a few chunks?
        """
        last_timestep_of_extra_file = self.CDO.seltimestep("-1", input=self.files["outdata"]["extra"]._current_location)
        ofile = self.CDO.selvar("thk", input=last_timestep_of_extra_file)
        self.files["couple"][self.Type+"_file"] = ComponentFile(src=ofile, dest=self.couple_dir+"/"+self.Type+"_file_for_solid_earth.nc")

    def _describe_grid(self):
        """ Gets the currently appropriate PISM grid in the couple dir """
        self.files["couple"][self.Type+"_grid"] = ComponentFile(src=self.POOL_DIR+"/".join(["", "grids", self.Domain])
                                                                    + "/"
                                                                    + "_".join([self.Executable, self.Domain, self.LateralResolution])
                                                                    +".griddes",
                                                                dest=self.couple_dir+"/"+self.Type+".griddes")

    @write_couple_vars_to_json
    def _describe_variables(self):
        """Writes variable description """
        return {"ice_thickness":
                        {"varname": "thk",
                         "units": "m",},
                }

    #def __init__(self):
    #    iter_coup_regrid_methods = {
    #            "DOWNSCALE": [self.regrid_downscale],
    #            "INTERPOLATE": [self.regrid_interpolate],
    #            "REMAP": [self.regrid_remap]
    #            }

    #    iter_coup_ablation_methods = {
    #            "PDD": [self.PDD_prepare_forcing, self.PDD_set_options],
    #            "EBM": [self.semic_prepare_forcing, self.semic_run, self.semic_pism_prepare_surface_forcing, self.semic_pism_set_surface_given]
    #            }

    def regrid_downscale(self):
        """ Does static (one-time only) downscaling of atmospheric forcing """
        # TODO: Get these next two from the environment if possible
        downscale_temp = True
        downscale_precip = True
        self._regrid_downscale_split_names()
        self._regrid_downscale_generate_elevation_difference()
        self._regrid_downscale_temperature() if downscale_temp else self._regrid_interpolate_temperature()
        self._regrid_downscale_precipitation() if downscale_precip else self._regrid_interpolate_precipitation()

    def regrid_interpolate(self):
        self._regrid_interpolate_temperature()
        self._regrid_interpolate_precipitation()

    def regrid_remap(self):
        self._regrid_remap_temperature()
        self._regrid_remap_precipitation()

    def PDD_prepare_forcing(self):
        self._PDD_set_temperature_units()
        self._PDD_set_precipitation_units()
        self._PDD_set_time_axis()

    def PDD_set_options(self):
        # TODO: Here, we need something that gives the following PISM switches:
        # -atmosphere given
        # -surface pdd
        # -atmosphere_given_file=/path/to/file
        pass

    def _PDD_set_temperature_units(self):
        temp_names = {atmosphere_file_temperature_varname: "air_temp"}
        # WTF is c? I am not sure if this makes sense...
        nco.ncrename(input="something", options=[c.Rename("v", temp_names)])
        # This needs to come from somewhere else....it shouldn't be hardcoded...
        unit_name_dict = {"temperture_variable_name": "temp2", "precipitation_variable_name": "aprt"}

        # This needs some sort of connection to ECHAMs standard output, which should be available via atmo_given...


    def _regrid_downscale_generate_elevation_difference(self):
        """Calculates ``elev_hi`` minus ``elev_lo``

        Using the ``INPUT_FILE_pism`` from the ``files`` attribute, this method
        calculates the difference between the high and lo resolution.

        NOTE
        ----
            Assumes that the variable named ``elevation`` is available in the
            lo-res elevation file

        Returns
        -------
        diff : np.array
            You get back a numpy array of the differences between the high
            resolution and low resolution grids.
        """
        ifile = self.files["input"]["INPUT_FILE_pism"]
        if using_xarray:
            # FIXME: the lo res resolution elevation should be extracted from the dictionary read during reading variable names from echam
            diff = ifile["elevation"] - self.files["couple"]["lo_res_elevation"]["elevation"]
            return diff #...?
        else:
            if "usurf" in CDO.pardes(input=ifile):
                hi_res_elevation = CDO.expr("elevation=usurf", input=ifile)
            elif ["thk", "topg"] in CDO.pardes(input=ifile):
                hi_res_elevation = CDO.expr("elevation=thk+topg", input=ifile)
            else:
                # TODO: Make CouplingError a real thing...
                raise CouplingError("Insufficient information for hi resolution elevation, sorry!")
            hi_res_elevation = self.files["couple"]["hi_res_elevation"] \
                            = ComponentFile(src=hi_res_elevation, dest="hi_res_elevation_"+self.Name+"_"+str(self.calendar)+".nc")
            return CDO.sub(input=hi_res_elevation+" "+self.files["couple"]["lo_res_elevation"])

        def _regrid_downscale_temperature(self):
            pass


















