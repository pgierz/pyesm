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
import inspect
import os
import shutil

from pyesm.core.component import Component
from pyesm.core.helpers import ComponentFile
from pyesm.core.time_control import EsmCalendar
from pyesm.core.compute_hosts import Host

from ruamel.yaml import YAML, yaml_object
yaml = YAML()


@yaml_object(yaml)
class ComponentCompute(Component):
    """
    Contains elements of a Component related to actually running a simulation
    """

    def __init__(self, *Component_args, **Component_kwargs):
        """ Initialization of a Compute part for a Component with phase
        instructions for prepare, work, and cleanup.

        Upon initialization, a work directory is generated and attached to the
        object, without a ``NAME`` subdirectory. The compute requirements are
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
        yaml_file : str
            The path to the YAML configuration for this particular component.
        calendar : ESMCalendar
            The parameter passed in during initialization is attached to the object.
        """
        super(ComponentCompute, self).__init__(*Component_args, **Component_kwargs)

        self._register_directory("work", use_name=False)

        
        self._default_prepare_steps = [
                "read_from_dataset",
                "override_filetables_from_env",
                "copy_files_to_exp_tree",
                ]

    def prepare(self, steps=None):
        """
        All steps needed to actually prepare a run happen here.

        The following (possibly non-implemented) methods are called:

        1. Component._prepare_read_from_dataset()

        2. Component._prepare_override_filedicts_from_env()

        3. Component._prepare_copy_files_to_exp_tree()

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
        steps = steps or self._default_prepare_steps
        self._call_steps(phase="prepare", steps=steps)

    def _prepare_override_filedicts_from_env(self):
        """
        Replace the src of specific ComponentFile from the enviornment

        Since we use the old esm-style variable names as keys, we can use the strings of the
        old esm-style variable names as sources for each ComponentFile in the FileDict for each
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
                toplevel_destination = os.path.normpath("/".join([getattr(self, filetype + "_dir"),
                                                                os.path.basename(thisfile.dest)]))
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
        + ``@NAME@`` --> ``self.NAME``
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

@yaml_object(yaml)
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

