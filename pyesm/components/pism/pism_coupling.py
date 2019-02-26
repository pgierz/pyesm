"""

Allows for coupling from a generic ``atmosphere`` model to ``PISM``

- - - -
"""
# Standard Library Imports:
import glob
import json
import logging
import math
import os
import tempfile

# External Imports
import cdo
import nco
import numpy as np
import xarray as xr

# This Library Imports:
from pyesm.core.component.component_coupling import ComponentCouple, cleanup_after_send, write_couple_vars_to_json
from pyesm.components.pism.pism_compute import PismCompute
from pyesm.core.helpers import load_environmental_variable_1_0, ComponentFile, FileDict
from pyesm.core.errors import CouplingError

CDO = cdo.Cdo()
NCO = nco.Nco()


class PismCouple(PismCompute, ComponentCouple):
    """ Functionality to couple PISM with other models """
    COMPATIBLE_COUPLE_TYPES = ["atmosphere", "solid_earth"]

    def __init__(self, **PismComputeArgs):
        super(PismCouple, self).__init__(**PismComputeArgs)
        self.files['couple']['ice_grid'] = ComponentFile(
                src=self.POOL_DIR + "grids/" + self.Domain + "/pismr_" + self.Domain + "_" + self.LateralResolution + ".griddes",
                dest=self.couple_dir)

    ################################################################################
    ################################################################################
    ################################################################################
    #
    #           R E C I E V E    V A R I O U S   M O D E L S
    #
    ################################################################################
    ################################################################################
    ################################################################################


    ################################################################################
    #
    #           A T M O S P H E R E    T O   P I S M
    #
    ################################################################################
    def recieve_atmosphere(self):
        """
        Bundles up functionality to recieve a generic atmosphere file 

        Uses one of the following methods to get atmosphere fields into PISM
        compatiable input:
        1. downscale_static
            Downscales atmospheric temperature and precipitation using a lapse
            rate and precipitation reduction factor. See the method
            documentation for ``regrid_downscale`` for more information.
        2. interpolate
            Uses bilinear interpolation provided by CDO to interpolate to the
            PISM grid.
        3. regrid
            Uses conservative remapping to regrid to the PISM grid.
        """
        logging.info("\t\t *   Recieving information from a generic atmosphere model...")
        PISM_ATMO_couple_method = os.environ.get("PISM_ATMO_couple_method", "downscale_static")
        logging.info("\t\t *   Using coupling method: %s", PISM_ATMO_couple_method)
        if PISM_ATMO_couple_method == "downscale_static":
            forcing_file = self.regrid_downscale_static()
        elif PISM_ATMO_couple_method == "interpolate":
            forcing_file = self.regrid_remap()
        elif PISM_ATMO_couple_method == "remap":
            forcing_file = self.regrid_remap()
        self.files['forcing']['atmosphere_given'] = ComponentFile(
                src=forcing_file,
                dest=self.forcing_dir+"/atmo_given_file_"+self.calendar.current_date.format(form=0)+".nc")
        self.files['forcing']['atmosphere_given'].digest()

    def regrid_downscale_static(self):
        """ Does static (one-time only) downscaling of atmospheric forcing """
        # TODO: Get these next two from the environment if possible
        downscale_temp = True
        downscale_precip = True
        if downscale_temp or downscale_precip:
            elevation_difference = self._regrid_downscale_generate_elevation_difference()
        if downscale_temp:
            temperature = self._regrid_downscale_temperature(
                elevation_difference,
                lapse_rate=os.environ.get("DOWNSCALING_LAPSE_RATE", -0.7))
        else:
            temperature = self._regrid_interpolate_bilinear_array("air_temperature")
        if downscale_precip:
            temperature_ref = self._regrid_downscale_temperature(
                    elevation_difference,
                    lapse_rate=os.environ.get("DOWNSCALING_LAPSE_RATE", -0.7))
            temperature_0 = self._regrid_interpolate_bilinear_array("air_temperature")
            precipitation_0 = self._regrid_interpolate_bilinear_array("precipitation")
            DOWNSCALING_GAMMA_FACTOR = os.environ.get("DOWNSCALING_LAPSE_RATE", -0.07)
            precipitation = self._regrid_downscale_precipitation(
                    temperature_ref,
                    temperature_0,
                    precipitation_0, 
                    gamma=DOWNSCALING_GAMMA_FACTOR)
        else:
            precipitation = self._regrid_interpolate_bilinear_array("precipitation")
        forcing_file = self._finalize_forcing_for_PDD(temperature, precipitation)
        return forcing_file

    def regrid_interpolate(self):
        """
        Generates PISM forcing for PDD via bilinear interpolation
        """
        temperature = self._regrid_interpolate_bilinear_array("air_temperature")
        precipitation = self._regrid_interpolate_bilinear_array("precipitation")
        forcing_file = self._finalize_forcing_for_PDD(temperature, precipitation)

    def regrid_remap(self):
        temperature = self._regrid_interpolate_conservative_array("air_temperature")
        precipitation = self._regrid_interpolate_conservative_array("precipitation")
        forcing_file = self._finalize_forcing_for_PDD(temperature, precipitation)

    def _finalize_forcing_for_PDD(self, temperature, precipitation):
        """
        Finalizes a forcing file for PDD.

        The following steps are preformed here:
        1. Appropriate units are set for use with PISM's Positive Degree Day
           (PDD) scheme. Units are converted using the cf_units library. (LINK
           needed)
        2. A time axis is generated describing the time for the forcing to be used.

           Note that currently, we assume either a time mean, or monthly means.
           The time axis is generated such that is always points to days
           increasing from 0-1-1 00:00:00, in full days. If multiple years are
           given for coupling, it is assumed that you have given intervals of
           12 month blocks at a time, and the time axis increases beyond the 1
           year given.

        Parameters
        ----------
        temperature : xr.DataArray
            A DataArray describing the temperatures to be used by the PDD scheme.
        precipitation : xr.DataArray
            A DataArray describing the precipitation to be used by the PDD scheme.

        Returns
        -------
        str
            The path of the finished file is returned as a string, which is
            later passed further to ComponentFile

        Notes
        -----
        We still need to find a solution for multiple year means rather than
        multiple monthly cycles.
        """
        ofile = xr.Dataset(
            {
                "air_temp": temperature,
                "precipitation": precipitation
                }
            )
        ofile.air_temp.attrs['units'] = self.couple_attrs['atmosphere']['air_temperature']['units']
        ofile.precipitation.attrs['units'] = self.couple_attrs['atmosphere']['precipitation']['units']


        # Fix the time axis; it should be the number of the day in the year
        total_number_of_days_in_this_year = self.calendar.current_date._calendar.day_in_year(self.calendar.current_date.year)

        if len(ofile.time) == 1:
            ofile.time.data[:] = total_number_of_days_in_this_year / 2.0
            time_bound_array = np.array([1, total_number_of_days_in_this_year])
        else:
            end_day = 0
            date_list = [self.calendar.coupling_dates[self.NAME]]
            time_array = np.empty((len(date_list)*12, 1))
            time_bounds_array = np.empty((len(date_list)*12, 2))
            for year_number, date in enumerate(date_list):
                for index, month_name in enumerate(date._calendar.monthnames):
                    index += year_number * 12
                    length_of_this_month = date._calendar.day_in_month(date.year, month_name)
                    end_day += length_of_this_month
                    middle_day = end_day - (length_of_this_month / 2)
                    start_day = 1 + end_day - length_of_this_month
                    time_array[index] = middle_day
                    time_bounds_array[index, 0], time_bounds_array[index, 1] = start_day, end_day
        ofile.time.data[:] = time_array
        ofile.time_bounds.data[:] = time_bounds_array
        # Get time attributes to make sense:
        ofile.time.attrs['units'] = 'days since 0-1-1 00:00:00'
        ofile.time.attrs['calendar'] = str(total_number_of_days_in_this_year)+"_day"
        # Save output file:
        encoding_args = {'dtype': 'float32', '_FillValue': -9999}
        ofile.to_netcdf(self.couple_dir+"/atmo_given.nc",
                encoding={
                    "air_temp": encoding_args,
                    "precipitation": encoding_args
                    },
                unlimited_dims=["time"])
        return self.couple_dir+"/atmo_given.nc"

    def _regrid_interpolate_bilinear_array(self, varname):
        """
        Regrids the atmosphere field via bilinear interpolation
        """
        atmosphere_file = self._remap_forcing_to_thismodel_grid("atmosphere", regrid_type="bil")
        atmosphere_dataset = xr.open_dataset(atmosphere_file)
        return getattr(atmosphere_dataset, self.couple_attrs['atmosphere'][varname]['varname'])

    def _regrid_interpolate_conservative_array(self, varname):
        """
        Regrids the atmosphere field via bilinear interpolation
        """
        atmosphere_file = self._remap_forcing_to_thismodel_grid("atmosphere", regrid_type="con")
        atmosphere_dataset = xr.open_dataset(atmosphere_file)
        return getattr(atmosphere_dataset, self.couple_attrs['atmosphere'][varname]['varname'])

    def PDD_set_options(self):
        # TODO: Here, we need something that gives the following PISM switches:
        # -atmosphere given
        # -surface pdd
        # -atmosphere_given_file=/path/to/file
        pass


    def _regrid_downscale_generate_elevation_difference(self):
        """
        Calculates ``elev_hi`` minus ``elev_lo``

        Using the ``INPUT_FILE_pism`` from the ``files`` attribute, this method
        calculates the difference between the high and lo resolution.

        Note
        ----
            Assumes that a variable named ``orography`` or ``elevation`` is
            available in the lo-res elevation file. When selecting, the name
            ``orography`` takes preceedence.

        Returns
        -------
        diff : xarray.core.dataarray.DataArray
            You get back a DataArray of the time mean differences between the
            high resolution and low resolution grids.
        """
        ice_file = self.files["input"]["INPUT_FILE_pism"]
        ice_dataset = xr.open_dataset(ice_file._current_location)
        try:
            elevation_hi = getattr(ice_dataset, "usurf")
        except AttributeError:
            try:
                topg = getattr(ice_dataset, "topg")
                thk = getattr(ice_dataset, "thk")
                elevation_hi = topg + thk
            except AttributeError:
                raise CouplingError("The PISM input file needs to have usurf or topg and thk!")
        elevation_hi = elevation_hi.mean(dim="time")

        atmosphere_file = self._remap_forcing_to_thismodel_grid("atmosphere", regrid_type="bil")
        atmosphere_dataset = xr.open_dataset(atmosphere_file)
        try:
            elevation_lo = getattr(atmosphere_dataset, self.couple_attrs['atmosphere']['orography']['varname'])
        except AttributeError:
            try:
                elevation_lo = getattr(atmosphere_dataset, self.couple_attrs['atmosphere']['elevation']['varname'])
            except AttributeError:
                raise CouplingError("The atmosphere file needs a variable either orography or elevation!")
        elevation_lo = elevation_lo.mean(dim="time")

        return elevation_hi - elevation_lo

    def _regrid_downscale_temperature(self, elevation_difference, lapse_rate):
        """
        Downscales via temperature via elevation differences and a lapse rate.

        The lapse rate is applied to the elevation differences in order to
        modify temperatures. This is equivalent to the following
        mathematically:

        T_downscaled = T_lo_res + gamma * elevation_difference

        Parameters
        ----------
        elevation_difference
            An array with differences in elevation between the low resolution
            atmosphere model and the high resolution ice sheet model. Units are
            in meters.
        lapse_rate
            A lapse rate to apply to the elevation differnces. Units are Kelvin
            per meter

        Returns
        -------
        temperature_hi
            Temperatures that have been modified via the elevation differences.
        """
        atmosphere_file = self._remap_forcing_to_thismodel_grid("atmosphere", regrid_type="bil")
        atmosphere_dataset = xr.open_dataset(atmosphere_file)
        temperature_lo = getattr(atmosphere_dataset, self.couple_attrs['atmosphere']['air_temperature']['varname'])
        return temperature_lo + lapse_rate * elevation_difference

    def _regrid_downscale_precipitation(self, temperature_ref, temperature_0, precipitation_0, gamma=-0.07):
        """
        Downscales precipitation using temperature differences and a factor gamma.

        An implementation of equation 2 from Quiquet et al., 2012. Downscales
        temperature using a exponential factor gamma which corresponds to
        removing precipitation as the air gets colder.

        Parameters
        ----------
        temperature_ref : xr.DataArray
            The high resolution temperatures
        temperature_0 : xr.DataArray
            The low resolution temperatures
        precipitation_0 : xr.DataArray
            The low resolution precipitation field
        gamma : float
            Default to -0.07 as in the paper. This is the factor by which precent
            precipitation is reduced. The default corresponds to a 7.3%
            decrease for every 1K of temperature decrease

        Returns
        -------
        precipitation_ref : xr.DataArray
            The precipitation required by the high-resolution ice sheet model.

        References
        ----------
        Quiquet, A., Punge, H. J., Ritz, C., Fettweis, X., Gallee, H.,
        Kageyama, M., Krinner, G., Salas y Melia, D., and Sjolte, J.:
            Sensitivity of a Greenland ice sheet model to atmospheric forcing
            fields, The Cryosphere, 6, 999-1018,
            https://doi.org/10.5194/tc-6-999-2012, 2012.
        """
        precipitation_ref = precipitation_0 * math.e ** (gamma * (temperature_ref - temperature_0))
        return precipitation_ref

    ################################################################################
    ################################################################################
    ################################################################################
    #
    #           S E N D   V A R I O U S   M O D E L S
    #
    ################################################################################
    ################################################################################
    ################################################################################
    
    ################################################################################
    #
    #           G E N E R A L   S E N D
    #
    ################################################################################
    def _describe_grid(self):
        """ Gets the currently appropriate PISM grid in the couple dir """
        self.files["couple"][self.Type+"_grid"] = ComponentFile(src=self.POOL_DIR+"/".join(["", "grids", self.Domain])
                                                                + "/"
                                                                + "_".join([self.EXECUTABLE, self.Domain, self.LateralResolution])
                                                                +".griddes",
                                                                dest=self.couple_dir+"/"+self.TYPE+".griddes")

    @write_couple_vars_to_json
    def _describe_variables(self):
        """Writes variable description """
        return {"ice_thickness":
                        {"varname": "thk",
                         "units": "m",},
                }

    ################################################################################
    #
    #           P I S M   T O   S O L I D   E A R T H
    #
    ################################################################################

    @cleanup_after_send
    def send_solid_earth(self):
        """ Sends a generic ice sheet field for use with a solid earth model"""
        self._generate_solid_earth_forcing_file()
        self._describe_grid()  # See section general send
        self._describe_variables()  # See section general send

    def _generate_solid_earth_forcing_file(self):
        """ Generates a solid earth forcing from ice output.

        Some questions that still need to be clarified:
        1. Do we want to send the newest timestep?
        2. What happens if PISM restarts during a few chunks?
        """
        last_timestep_of_extra_file = self.CDO.seltimestep("-1", input=self.files["outdata"]["extra"]._current_location)
        ofile = self.CDO.selvar("thk", input=last_timestep_of_extra_file)
        self.files["couple"][self.Type+"_file"] = ComponentFile(src=ofile, dest=self.couple_dir+"/"+self.Type+"_file_for_solid_earth.nc")
