"""
Contains classes and other objects for helping
"""
import collections
import logging
import shutil
import os

class SimElement(object):
    """
    A meta-object to hold both Component and SetUp
    """
    NAME = "SimElement"
    VERSION = "0.0.0"
    TYPE = "Generic"

    def __init__(self, parent_dir="."):
        """
        This is sets up some of the very basics needed in any simulation element.

        Attributes
        ----------
        Name : str
            What the SimElement is called (e.g. AWIESM, ECHAM6, FESOM, OASIS, ...)
        Version : str
            The version number
        Type : str
            The "type" of the element (e.g. Atmosphere, Coupler, AOGCM, ect...)
        _parent_dir : str
            The parent directory, default is ``.`` (current working directory).
        _filetypes : list
            The filetypes associated with this Simulation Element, a subfolder
            can be made for each. Default is "config", "forcing", "input",
            "log", "mon", "outdata", "restart"
        """
        self.NAME = self.Name = self.name = type(self).NAME
        self.VERSION = self.Version = self.version = type(self).VERSION
        self.TYPE = self.Type = self.type = type(self).TYPE

        self._parent_dir = parent_dir
        self._filetypes = ["config", "forcing", "input", "log", "mon", "outdata", "restart"]

    def _register_directory(self, directory_type, use_Name=True):
        """
        Sets an attribute ``component.<directory_type>_dir`` and creates the
        directory if it doesn't exist.

        Parameters
        ----------
        directory_type : str
            The name of the directory type you want to register/create
        use_Name : bool, optional
            Default is True. If this is set, the directory type will contain a
            sub-directory with the SimElement's ``Name`` attribute

        Examples
        --------
        >>> example_sim_element = SimElement()
        >>> example_sim_element._register_directory("outdata")
        >>> example_sim_element._outdata_dir
        ./outdata/component
        >>> example_sim_element._register_directory("analysis", use_Name=False)
        >>> example_sim_element._analysis_dir
        ./analysis
        """
        if use_Name:
            dir_location = "/".join([self._parent_dir, directory_type, self.Name])
        else:
            dir_location = "/".join([self._parent_dir, directory_type])

        setattr(self, directory_type + "_dir", dir_location)
        if not os.path.exists(dir_location):
            logging.debug("Making directory: %s", str(dir_location))
            os.makedirs(dir_location)

    def _call_steps(self, phase, steps):
            """
            This method provides the ability to call a list of steps for a
            simulation, with optional hooks for user-defined methods before and
            after the built-in ones.

            The actual methods of an object called are defined as follows:
            ``self._<phase>_<order>_<stepname>``

            where:

            + phase is the name of the current phase passed in to
              ``_call_steps``. Could be something like "prepare", "work",
              "cleanup"
            + order: automatically determined. Steps run in the order: user,
              default, USER. The "default" is does not need a special name, it is
              automatically used from the method name, e.g.
              ``_<phase>_<stepname>``
            + stepname: the name of the current step from the ``steps`` list.

            Parameters
            ----------
            phase : str
                The "type" of step being preformed, could be something like
                "prepare", "work", "cleanup"

            steps : list (or iterable)
                any iterable of ``str`` that provides method names to be
                called.

            Raises
            ------
            NotImplementedError:
                If a required (non-user-defined) step is missing, a
                NotImplemented error is raised.

            Example
            -------

            >>> component._call_steps("example", ["step1", "step2"])
            calling component._example_user_step1
            calling component._example_step1
            calling component._example_USER_step1
            calling component._example_user_step2
            calling component._example_step2
            calling component._example_USER_step2
            """
            logging.info(80*"=")
            log_string = "working on " + phase.replace("_", " ") + " " + self.Name.replace("_", " ")
            logging.info(" ".join(log_string.split()).upper().center(80))
            logging.info("")
            for step in steps:
                logging.debug(" ".join(step.replace("_", " ").split()).upper().center(80))
                for order in ["user", "", "USER"]:
                    order_str = order if order else "default"
                    logging.debug(" ".join(order_str.split()).center(80))
                    thisstep = getattr(self, "_".join(["_", phase, order, step]).replace("__", "_"), None)
                    thisstep_args = getattr(self, "_".join(["_", phase, order, step, "args"]).replace("__", "_"), None)
                    thisstep_kwargs = getattr(self, "_".join(["_", phase, order, step, "kwargs"]).replace("__", "_"), None)

                    if thisstep_args is not None:
                        assert isinstance(thisstep_args, list)
                    if thisstep_kwargs is not None:
                        assert isinstance(thisstep_kwargs, dict)

                    logging.debug("%(step)s --> %(thisstep)s", {"step": step, "thisstep": thisstep})
                    logging.debug("%(step)s args --> %(thisstep_args)s", {"step": step, "thisstep_args": thisstep_args})
                    logging.debug("%(step)s kwargs --> %(thisstep_kwargs)s ", {"step": step, "thisstep_kwargs": thisstep_kwargs})

                    if order == "":
                        if not callable(thisstep):
                            raise NotImplementedError("A required step %s of %s is not implemented!" % (step, phase))

                    if callable(thisstep):
                        logging.debug("Calling %s...", thisstep)
                        if thisstep_args and thisstep_kwargs:
                            thisstep(*thisstep_args, **thisstep_kwargs)
                        elif thisstep_args:
                            thisstep(*thisstep_args)
                        elif thisstep_kwargs:
                            thisstep(**thisstep_kwargs)
                        else:
                            thisstep()
                logging.debug(40*"- ")
            logging.info(80*"=")


class ComponentFile(object):
    """
    ``ComponentFile`` are things that might be required as:
        1. **input** for a specific  component
        2. **output** of a specific component
        3. **restart** for a specific model state
        4. **config** a namelist, config_file, override file, or something
           similar
        5. **forcing** data which describes boundary or initial conditions
        6. **other** information which might be, somehow, relevant

    Currently, these objects always have the following attributes upon
    initialization:

    Attributes
    ----------
    src : str
        The source filepath, including the filename
    dest : str
        The destination, where the file will be copied/linked to.
    copy_method : callable
        One of ``os.symlink`` or ``shutil.copyfile``.
    """

    def __init__(self, src, dest=None, copy_method="copy"):
        """
        Initialization of a ``ComponentFile``: Note that if nothing else is provided, the
        default ``copy_method`` is ``copy`` which turns the call into ``shutil.copyfile``

        Parameters
        ----------
        src : str
            The source of the file
        dest : str, optional
            Default None, which turns to ``os.path.basename(self.src)``. The
            destination where the file should be linked/copied.
        copy_method : str, optional
            Default is "copy". Should be one of "link" or "copy"

        Raises
        ------
        ValueError
            raised if an incorrect option is passed to ``copy_method``
        """
        if dest is None:
            dest = os.path.basename(src)
        if copy_method == "copy":
            copy_method = shutil.copyfile
        elif copy_method == "link":
            copy_method = os.symlink
        else:
            raise ValueError("`copy_method` needs to be either `copy` or `link`")
        self.src, self.dest, self.copy_method = src, dest, copy_method

    def digest(self):
        """
        Uses the ``copy_method`` to copy or link ``src`` to ``dest``.
        """
        logging.debug("%s.digest() has been called:", __name__)
        if os.path.isdir(self.dest):
            self.dest += "/"+os.path.basename(self.src)
        logging.debug("%s".ljust(20), self)
        self.copy_method(self.src, self.dest)
        logging.debug("...done!")

    def __eq__(self, other):
        """An equality check method for ComponentFile. Tests if src, dest, and
        copy_method are all the same"""
        return bool(self.src == other.src and
                    self.dest == other.dest and
                    self.copy_method == other.copy_method)

    def __str__(self):
        """ A nice string printed for ComponentFile

        ``self.src`` -- ``verb`` --> ``self.dest``

        where ``verb`` is either "copied" or "linked"
        """
        if self.copy_method == os.symlink:
            verb = "linked"
        elif self.copy_method == shutil.copyfile:
            verb = "copied"
        return "%s -- %s --> %s" % (self.src, verb, self.dest)

    __repr__ = __str__

class TransformedDict(collections.MutableMapping):
    """A dictionary that only accepts ComponentFile as values for it's keys"""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = self._check_value(value)

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def _check_value(self, value):
        if not isinstance(value, ComponentFile):
            raise TypeError
        return value


class FileDict(TransformedDict):
    """
    A subclass of python's built-in dict, which
    only allows you to append values of the type component_file
    """

    def digest(self, flag=None, new_dest=None):
        """
        "digest" the list: perform the filesystem maniuplation specified
        to copy or link each ComponentFile in the FileDict.
        
        Parameters
        ----------
        flag : str, optional
            Determines what is done when the ``FileDict`` is digested. If flag
            is ``"prepare"``, the argument of ``new_dest`` is used. The current
            destination becomes the new source, and the ``new_dest`` becomes
            the new destination. If flag is ``"work"``, the each entry is
            popped out of the dictionary.
        new_dest : str, optional
            The new destination. If this stays ``None`` even if flag is ``"prepare"``, a ValueError is raised

        Raises
        ------
        ValueError
            Raised if flag is ``"prepare"`` and new_dest is ``None``
        """
        for key in self.keys():
            this_entry = self[key]
            this_entry.digest()
            if flag == "prepare":
                if new_dest is None:
                    raise ValueError("You must specify a new destination!")
                this_entry.src, this_entry.dest = this_entry.dest, new_dest
            elif flag == "work":
                # Empty out the dictionary during movement from prepare to work.
                # After the simulation, the cleanup phase will anyway need to use entirely
                # different files for restart and outdata
                self.pop(key)
