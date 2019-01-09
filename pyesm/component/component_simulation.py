"""
Compute and Post-Processing Jobs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All parts of a component needed to RUN the simulation are here. Two classes are
defined

#. ComponentCompute
#. ComponentPostprocess

``ComponentCompute``
    The ``ComponentCompute`` class defines steps needed for setup, execution,
    and tear-down of a simulation. In addition to the initialization needed for
    a basic ``Component``, you need to specify a ``table_dir``, which
    defines where the filetables are generated from.  Additionally, a
    ``calendar`` must be specified.

``ComponentPostprocess`` 
    Defines tasks that should be performed after the simulation is complete.
    This usually occurs as a seperate batch job.

----
"""
import csv
import inspect
import json
import os
import shutil

import pyesm.logging as logging
from pyesm.component import Component
from pyesm.helpers import ComponentFile
from pyesm.time_control import EsmCalendar

logger = logging.set_logging_this_module()

class ComponentCompute(Component):
    """
    Contains elements of a Component related to actually running a simulation
    """

    def __init__(self, table_dir=None, calendar=None, *Component_args, **Component_kwargs):
        """ Initialization of a Compute part for a Component with phase
        instructions for prepare, work, and cleanup.

        Upon initialization, a work directory is generated and attached to the
        object, without a ``Name`` subdirectory. The compute requirements are
        also set during initialization.

        Parameters
        ----------
        table_dir : str
            The directory location from which the filetables are read.
        calendar : ESMCalendar
            A ESMCalendar which allows for parsing of the current date
            information.
        *Component_args:
            Additional arguments passed to the Component initialization
        **Component_kwargs:
            Additional keyword arguments passed to the Component initialization

        Attributes
        ----------
        calendar : ESMCalendar
            The parameter passed in during initialization is attached to the object.
        _table_dir : str
            The directory where JSON filetables are read from.
        executable : str
            The name of the executable
        command : str
            The full execution command, most often just ``./executable``
        num_tasks : int
            The number of tasks for this component
        num_threads : int
            The number of threads`
        """
        super(ComponentCompute, self).__init__(*Component_args, **Component_kwargs)
        self.calendar = calendar or EsmCalendar()

        # FIXME: This needs to point to whatever the module directory is...

        self._table_dir = table_dir or "."
        self._register_directory("work", use_Name=False)
        self._compute_requirements()
        self._log_compute_requirements()
        self._finalize_log_messages()

    def _compute_requirements(self):
        """
        Defines compute requirements

        The following attributes are set here:

        Attributes
        ----------
        executable : str
            The name of the executable
        command : str
            The full execution command, most often just ``./executable``
        num_tasks : int
            The number of tasks for this component
        num_threads : int
            The number of threads`
        """
        self.EXECUTEABLE = None
        self.COMMAND = None
        self.NUM_TASKS = None
        # NOTE: I don't know if this is really needed.
        self.NUM_THREADS = None

    def _log_compute_requirements(self):
        """ Print out information about the compute requirements """
        logger.info(80*"-")
        info_str="compute requirements for " + self.Name
        info_str = " ".join(info_str.split()).upper().center(80)
        logger.info(info_str)
        logger.info("\n%s will use the executable: \nexecutable=%s", self.Name, self.EXECUTEABLE)
        logger.info("\n%s will use: \nnum_threads=%s", self.Name, self.NUM_THREADS)
        logger.info("\nThe execution command will be: \ncommand=%s", self.COMMAND)
        logger.info(80*"-")

    def prepare(self, steps=None):
        """
        All steps needed to actually prepare a run happen here.

        The following (possibly non-implemented) methods are called:

        1. Component._prepare_read_filetables()

        2. Component._prepare_modify_filetables()

        3. Component._prepare_override_filetables_from_env()

        4. Component._prepare_copy_files_to_exp_tree()

        5. Component._prepare_modify_files()

        Alternatively, when implementing a ComponentSimulation for a specific
        ESM Model, you can pass a list of strings as the argument
        ``steps=["step1", "step2", "step3"]``, which will be given to
        _call_steps with the phase classification "prepare"

        Parameters
        ----------
        steps : list, optional
            The names of the steps to do durng the prepare phase. They will
            **always** be prepended with ``_prepare_``, so when you write a
            method to perform one of these steps, it should have the definition
            ``_prepare_<step_name>``
        """
        steps = steps or ["read_filetables", "modify_filetables", "override_filetables_from_env",
                          "copy_files_to_exp_tree", "modify_files"]
        self._call_steps(phase="prepare", steps=steps)

    def _read_filetables(self, json_dir, tag, name=None):
        """
        A small helper method to load a JSON file which contains a list of all the files
        used during simulation execution.

        _read_filetables is a helper method. Here, you can define files needed by your
        simulation for each of the pre-defined filetypes. Currently, if you need a filetype
        that is not implemented, an KeyError is raised.

        The JSON file contains a collection of dicts which can can take either
        lists or dicts as **values**.

            + Lists: You must give a list of the form [src, dest, link], which will then be
                     given to the ComponentFile. Omitting entries is allowed, so you can,
                     for example, only give src. However, the order cannot change.
            + Dicts: You must give a dict of the form:
                     {"src": srcfile, "dest": destfile, "copy_method": "link"}.
                     Here, you can omit the dest and only give, for example, src and
                     copy_method

        The **keys** will be conform to the old-style ESM variable names, in such a way
        you can overload the keys from the os.environ dictionary.

        The filetable to be read will have a name defined by the arguments
        Name, Version, and tag. For example, given a Component with following
        attributes:

        >>> my_component = Component()
        >>> my_component.Name
        Component
        >>> my_component.Version
        0.0.0

        a filetable would be read like this:
 
        >>> tag = "example"
        >>> my_component._read_filetables(json_dir=".", tag)
        Loaded files for Component from JSON Table ./Component_0.0.0_example_files.json

        Parameters
        ----------
        json_dir : str
            The directory where the table should be loaded from
        tag : str
            The type of files to load, usually one of ``prepare``, ``work``, or ``cleanup``
        """
        # Read the JSON into a flat dictionary, which can be overriden by user supplied
        # variables ("new" runscript) or environmental variables ("old" runscript)
        #
        # FIXME: Here we need something that controls preferrence of JSON vs
        # YAML vs something else...  Alternatively, we need an entirely second
        # _read_filetables function, and seperate based upon the method name,
        #
        assert isinstance(json_dir, str)
        if json_dir[-1] != "/":
            json_dir += "/"

        if name is None:
            name = "_".join([self.Name, self.Version, tag, "files.json"])
        data_file_string = json_dir + name 
        with open(data_file_string) as data_file:
            table_files = json.load(data_file)
        logger.debug("Loaded files for %s from JSON Table %s", self.Name, data_file_string)
        logger.debug("Here is what was loaded: %s", table_files)

        for filetype, entrylist in table_files.items():
            logger.debug("filetype --> %s entrylist --> %s", filetype, entrylist)
            if filetype in self.files.keys():
                for entry in entrylist:
                    logger.debug("entry --> %s", entrylist[entry])
                    logger.debug("*entry --> %s", " ".join(entrylist[entry]))
                    #
                    # NOTE: Here, we check if the JSON file was interpred as a ``list`` or
                    # as a ``dict``. In the case of ``list``, we **assume the user was smart**
                    # and got the argument order correct in order to construct a valid ComponentFile
                    #
                    # I'm not sure I like this, to be honest. Don't trust people to be smart...
                    #
                    # The ``dict`` case forces the use of kwargs for ComponentFile, and ensures that
                    # errors will be raised if the arguments have an incorrect form.
                    #
                    if isinstance(entrylist[entry], list):
                        self.files[filetype].update({entry: ComponentFile(*entrylist[entry])})
                    elif isinstance(entrylist[entry], dict):
                        self.files[filetype].update({entry: ComponentFile(**entrylist[entry])})
                    else:
                        raise TypeError("You are tying to use _read_filetables to put data into ComponentFile; only list or dict are allowed!")
            else:
                raise KeyError("Invalid key: %s. You must give one of %s in your JSON file %s" % (filetype, self._filetypes, data_file_string))
        logger.debug(self.files)

    def _prepare_read_filetables(self, json_dir=None):
        """
        Reads in the default fileset

        Here, the default FileDicts are read in from a JSON file. See the accompanying
        documentation for _read_filetables for more information on how such a filetable should
        be constructed.

        Parameters
        ----------
        json_dir : str, optional
            Default is ``None``. Here, you can overload where the table should
            be read from. Otherwise, the object attribute ``_table_dir`` is
            used.
        """
        if json_dir is None:
            json_dir = self._table_dir

        logger.debug("The used JSON dir in _prepare_read_filetables is %s", json_dir)
        self._read_filetables(json_dir, "prepare_default")

    def _prepare_modify_filetables(self, json_dir=None):
        """
        Modifies the default fileset

        Here, it is possible to modify the FileDict that are read from the JSON file in the
        previous step. At this point, you would redefine things like:

            + Which restart file you **currently** want to use

            + A forcing file which always needs to have the same name
              in the working directory but needs a different source for
              each run

        Parameters
        ----------
        json_dir : str, optional
            Default is ``None``. Here, you can overload where the table should
            be read from. Otherwise, the object attribute ``_table_dir`` is
            used.
        """
        if json_dir is None:
            json_dir = self._table_dir

        if os.path.exists("/".join([json_dir, "_".join([self.Name, self.Version,
                                                        "prepare_modify", "files.json"])])):
            logger.debug("Modify Table for %s exists, reading and modifying files...", self.Name)
            self._read_filetables(json_dir, "prepare_modify")

    def _prepare_override_filetables_from_env(self):
        """
        Replace the src of specific ComponentFile from the enviornment

        Since we use the old esm-style variable names as keys, we can use the strings of the
        old esm-style variable names as sources for each ComponenFile in the FileDict for each
        type. This **should** allow for the usage of old runscripts.
        """
        for FileDict in self.files.values():
            for key in FileDict.keys():
                FileDict[key].src = os.environ.get(key, FileDict[key].src)

    def _prepare_copy_files_to_exp_tree(self):
        """
        Copies files from wherever they may be in the filesystem to the appropriate locations
        in the experiment tree.
        """
        # Process all filetypes except outdata, this is done on the way back **out** of the work
        for filetype in [filetype for filetype in self._filetypes if filetype != "outdata"]:
            for thisfile in self.files[filetype].values():
                actual_destination = os.path.normpath("/".join([getattr(self, filetype + "_dir"),
                                                                os.path.basename(thisfile.dest)]))
                if thisfile.dest != os.path.basename(thisfile.dest):
                    logger.warning("You gave a full path for %s; it will be re-set to go to %s",
                                    thisfile.dest,
                                    actual_destination)
                thisfile.dest = actual_destination
            self.files[filetype].digest(flag="prepare", new_dest=self.work_dir)

    def _prepare_modify_files(self):
        """
        Modify Files that have been placed in the exp tree

        In the basic Component case, this does nothing, and it must be overloaded for specific
        components upon implementation
        """
        pass

    def work(self):
        """
        All steps that occur immediately before the simulation happen here.

        **NOTE** The execution command is called somewhere else.
        """
        steps = ["copy_files", "modify_files", "modify_namelists"]
        self._call_steps("work", steps)

    def _work_copy_files(self):
        """ Moves all files from the experiment tree to the work directory """
        for filetype in [filetype for filetype in self._filetypes if filetype != "outdata"]:
            self.files[filetype].digest(flag="work")

    def _work_modify_files(self):
        """ Method can be overloaded to modify files after they have been moved to working directory and before simulation is executed """
        pass # No useful implementation in skeleton implementation

    def _work_modify_namelists(self):
        """ Method can be overloaded to modify namelists after thay have been moved to working directory and before simulation is executed """
        pass # No useful implementation in skeleton implementation

    def cleanup(self):
        """
        All steps that occur immediately after the simulation happen here"
        """
        steps = ["copy_files"] 
        self._call_steps("cleanup", steps)

    def _cleanup_copy_files(self, json_dir=None):
        """
        This method moves files produced by the simulation to the outdata folder.

        In order to determine which files have been produced, we read another JSON file. Here, an
        important variable interpolation is performed:

        ``@STR@`` is relaced with ``value`` for the following:

        + ``@EXPID@`` --> ``self.expid``
        + ``@NAME@`` --> ``self.Name``
        + ``@DATE@`` --> ``str(self.calendar)``, leads to ``YYYYMMDD``
        + ``@LRES@`` --> ``self.LateralResolution``
        + ``@VRES@`` --> ``self.VerticalResolution``

        The ComponentFiles are ensured to have a source which consists of
        ``self.work_dir/<src>``, i.e. the WORK_DIR and the filename of what is
        given in the JSON file. The dest is ensured to point to:
        ``self.outdata_dir/<dest>`` where ``<dest>`` is the translated version
        of the filename according to the rules above.

        Parameters
        ----------
        json_dir : str, optional
            Default is ``None``. Here, you can overload where the table should
            be read from. Otherwise, the attribute ``self._table_dir`` is
            used.
        """
        if json_dir is None:
            json_dir = self._table_dir
        self._read_filetables(json_dir, "cleanup_default")

        module_file = inspect.getfile(ComponentCompute)
        module_directory = os.path.dirname(module_file)
        module_file_basename_without_ext = os.path.splitext(os.path.basename(module_file))[0]

        with open(module_directory+"/"+module_file_basename_without_ext+"_replacement_rules.csv") as f:
            replacement_dict = csv.DictReader(f, delimiter=";", skipinitialspace=True)
            replace_rules = {}
            for entry in replacement_dict:
                print(entry)
                key, value = entry['string'], entry['replacement']
                if "self." in value:
                    value = getattr(self, value.replace("self.", "").strip())
                replace_rules[key] = str(value)

        work_to_output_filetypes = ["outdata", "restart"]
        for cleanup_filetype in work_to_output_filetypes:
            for ThisComponentFile in self.files[cleanup_filetype].values():
                destination_dir = getattr(self, "_".join([cleanup_filetype, "dir"]))
                # Ensure that the src is taken from the work dir:
                ThisSrc = ThisComponentFile.src
                ThisComponentFile.src = self.work_dir+"/"+os.path.basename(ThisSrc)
                # Replace following the rules defined above:
                ThisDest = ThisComponentFile.dest
                for old_value, new_value in replace_rules.items():
                    ThisDest = ThisDest.replace(old_value, new_value)
                ThisComponentFile.dest = destination_dir+"/"+os.path.basename(ThisDest)
                # Ensure that the copy_method is copy and not link
                ThisComponentFile.copy_method = shutil.copyfile
                # Do the operation
                ThisComponentFile.digest()

class ComponentPostprocess(Component):

    def __init__(self):
        super(ComponentPostprocess, self).__init__()

    def post(self):
        steps = ["postprocess", "tar_output", "archive_to_tape", "cleanup"]
        self._call_steps("post", steps)

    def _post_postprocess(self):
        pass
    def _post_tar_ouput(self):
        pass
    def _post_archive_to_tape(self):
        pass
    def _post_cleanup(self):
        # delete uploaded tars
        # delete post directory
        pass

