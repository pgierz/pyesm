"""
Allows for coupling between ``ECHAM6`` and a **generic ice sheet**

- - - -
"""

# Standard Library Imports:
import logging
import tempfile

# This Library Imports:
from pyesm.core.component.component_coupling import ComponentCouple, cleanup_after_send, write_couple_vars_to_json 
from pyesm.components.echam.echam_compute import EchamCompute
from pyesm.core.helpers import load_environmental_variable_1_0, ComponentFile
from pyesm.core.errors import CouplingError


ACCELERATION_DUE_TO_GRAVITY = 9.81  # m/s**2


class EchamCouple(EchamCompute, ComponentCouple):
    """ Contains functionality to cut out ice sheet forcing from ECHAM6 output """
    COMPATIBLE_COUPLE_TYPES = ("ice",)
    def __init__(self, **EchamComputeArgs):
        super(EchamCouple, self).__init__(**EchamComputeArgs)

        # Get relevant environmental variables
        self.ECHAM_TO_ISM_multiyear_mean = load_environmental_variable_1_0("ECHAM_TO_ISM_multiyear_mean")
        self.ECHAM_TO_ISM_time_mean = load_environmental_variable_1_0("ECHAM_TO_ISM_time_mean")

    @cleanup_after_send
    def send_ice(self):
        """ Sends a generic atmosphere field for an ice sheet model """
        self._generate_ice_forcing_file()
        self._write_grid_description()
        self._write_variable_description()

    def _generate_ice_forcing_file(self):
        """Makes a forcing file for an ice sheet.

        The following information is included:
        + ...
        """
        logging.info("\t\t Preparing %s file for processing in an ice sheet model...", self.NAME)

        start_year = self.calendar.coupling_start_date[self.NAME].year
        end_year = self.calendar.coupling_end_date[self.NAME].year

        file_list = self._construct_input_list(start_year, end_year)
        files_with_selected_variables = self._select_relevant_variables(file_list)

        final_output = self._concatenate_files(files_with_selected_variables)

        if self.ECHAM_TO_ISM_multiyear_mean:
            final_output = self._multiyear_mean(final_output)
        if self.ECHAM_TO_ISM_time_mean:
            final_output = self._time_mean(final_output)

        self.files["couple"]["atmosphere_file_for_ice"] = ComponentFile(src=final_output,
                                                                        dest=self.couple_dir+"/atmosphere_file_for_ice.nc")
        logging.info("\t\t ...done!")

    def _write_grid_description(self):
        """ Writes echam6 grid descrption to atmosphere.griddes """
        logging.info("\t\t Writing echam6 grid description to generic file atmosphere.griddes...")
        logging.info("\t\t *   generatic griddes")
        griddes = self.CDO.griddes(input=self.files["couple"]["atmosphere_file_for_ice"].src)
        ofile = open(self.couple_dir+"/griddes_file", "w")
        ofile.write("\n".join(griddes))
        ofile.flush()
        self.files["couple"]["atmosphere_grid_description"] = ComponentFile(src=ofile.name,
                                                                            dest=self.couple_dir+"/atmosphere.griddes")
        self._cleanup_list.append(ofile.name)
        logging.info("\t\t ...done!")

    @write_couple_vars_to_json
    def _write_variable_description(self):
        """Writes variable descrptions to a file"""
        return {"air_temperature":
                {"varname": "temp2",
                 "units": "K"},
                "precipitation":
                {"varname": "aprt",
                 "units": "kg m-2 s-1"},
                "orography":
                {"varname": "orog",
                 "units": "m"},
                "shortwave_down":
                {"varname": "bottom_sw_down",
                 "units": "W m-2"}}

    def _construct_input_list(self, start_year, end_year):
        """
        Generates an input list for the files needed for coupling

        Parameters
        ----------
        start_year: int
            which **year** to start at. Note that months will be added automatically
        end_year: int
            which **year** to end at.

        Returns
        -------
        file_list : list
            a list of the files which have been selected for use in coupling

        .. NOTE::
            This method is **very dependent** on how the actual files are
            named, which in turn depends on two things:
            1. What the ``echam6`` namelist is set to
            2. How the pyesm functions rearrange the output.
        """
        logging.info("\t\t *   constructing input list...")
        # FIXME: This depends on how the model is configured to output data.
        # This **SHOULD** be defined somehow in one of the namelists...
        file_list = []
        logging.debug("Using start_year=%s and end_year=%s", start_year, end_year)
        # NOTE: Remember in the range, the end step is NOT-INCLUSIVE. Thus,
        # plus 1.
        for year in range(int(start_year), int(end_year)+1):
            for month in range(1, 13):
                datestamp = str(year).zfill(4)+str(month).zfill(2)
                file_list.append(self.outdata_dir+"/"+self.expid+"_echam6_echam_"+datestamp+".grb")
        logging.debug(file_list)
        return file_list

    def _select_relevant_variables(self, file_list):
        """
        Selects relevant variables from a list of files

        Currently, the following variables are extracted:

        + The orography ``orog``, which is derived from the geopotential height
          divided by the acceleration due to gravity.
        + The total precipitation ``aprt``, which is derived from the sum of
          large-scale and convective precipitation
        + Near surface temperature ``temp2``
        + Shortwave radiation at the bottom of the atmosphere
          ``bottom_sw_down``, derived as ``srads`` minus ``sradsu``.

        Parameters
        ----------
        file_list: list
            The list of files where relevant variables will be selected from

        Returns
        -------
        files_with_selected_variables: list
            A list of files containing the reduced information

        Raises
        ------
        CouplingError
            Raised if the returned list would have a length of 0.
        """
        logging.info("\t\t *   selecting relevant variables...")
        files_with_selected_variables = []
        with tempfile.NamedTemporaryFile('w') as instruction_file:
            # Write instructions to a file:
            instruction_file.write("orog=geosp/%(g)s; \n" % {"g": ACCELERATION_DUE_TO_GRAVITY})
            instruction_file.write("aprt=aprl+aprc; \n")
            instruction_file.write("temp2=temp2; \n")
            instruction_file.write("bottom_sw_down=srads-sradsu; \n")

            # Save the file, it will be deleted after the with statement closes
            instruction_file.flush()
            # Sorry, this has to be made by hand...
            required_vars = ["geosp", "aprl", "aprc", "temp2", "srads", "sradsu"]

            # Run the loop
            for this_file in file_list:
                vars_in_this_file = self.CDO.pardes(input=this_file, options="-t echam6")
                # Use only the second entry, the first is the code number, the
                # rest is long name
                vars_in_this_file = [var.split()[1] for var in vars_in_this_file]
                if set(required_vars).issubset(set(vars_in_this_file)):
                    ofile = self.CDO.exprf(instruction_file.name,
                                           input=this_file, options="-t echam6 -f nc")
                    for lst in files_with_selected_variables, self._cleanup_list:
                        lst.append(ofile)
                else:
                    logging.warning("\t\t *   WARNING: Not all variables needed were present, skipping %s", this_file)
                    logging.debug("Skipped file %s", this_file)
                    logging.debug("These were needed: %s", "\n".join(required_vars))
                    logging.debug("These were available: %s", "\n".join(vars_in_this_file))
        if len(files_with_selected_variables) > 0:
            return files_with_selected_variables
        logging.critical(files_with_selected_variables)
        raise CouplingError("The filelist you supplied did not contain any information to generate generic ice sheet forcing!")

    def _concatenate_files(self, file_list):
        logging.info("\t\t *   concatenating files...")
        return self.CDO.cat(input=file_list, options="-f nc")

    def _multiyear_mean(self, ifile):
        logging.info("\t\t *   generating multi-year monthly mean...")
        print(self.CDO.ntime(input=ifile))
        print(self.CDO.showdate(input=ifile))
        return self.CDO.ymonmean(input=ifile, options="-f nc")

    def _time_mean(self, ifile):
        logging.info("\t\t *   generating full time mean...")
        return self.CDO.timmean(input=ifile, options="-f nc")
