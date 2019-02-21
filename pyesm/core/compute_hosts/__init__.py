"""
Compute Hosts contains a class to load information about a specific supercomputer:

+ batch system
+ names of filesystems
+ names of queue partitions
+ operating system

A single class ``Host`` is defined, which automatically loads a Host
configuration file and sets up object attributes.

An example host configuration file is provided::

    {
            "hostnames": {"login": "ollie[01]",
                          "compute": "prod-[0-9]{3}",
                          "mini": "mini"},
            "nodetypes": ["login", "compute", "fat", "mini"],
            "batch_system": "slurm",
            "operating_system": {"linux": "centos"},
            "partitions": {"compute": "mpp", "post": "smp"},
            "cores": {"compute": 36},
            "cpus": {"compute": 2}
    }

----
"""
import glob
import importlib
import inspect
import json
import os
import socket
import sys
import zipfile

from ruamel.yaml import YAML, yaml_object
yaml = YAML()


@yaml_object(yaml)
class Host(object):
    def __init__(self, machine_name=None, batch_system=None):
        """ Determines hostname and sets up attributes

        Given a hostfile as defined above, an object my_host would be generated as follows:

        >>> myhost = Host()
        >>> dir(myhost)
        ['__doc__',
         '__init__',
         '__module__',
         u'batch_system',
         u'cores',
         u'cpus',
         u'hostnames',
         u'nodetypes',
         u'operating_system',
         u'partitions']
        >>> myhost.batch_system
        u'slurm'
        >>> myhost.hostnames
        {u'compute': u'prod-[0-9]{3}', u'login': u'ollie[01]', u'mini': u'mini'}

        Note that when possible, regular expressions are used if multiple
        options are possible. The hostname is automatically determined based
        upon ``socket.gethostname``
        """
        HOSTNAME = socket.gethostname()
        if machine_name is not None:
            HOSTNAME = machine_name
        module_file = inspect.getfile(Host)
        module_directory = os.path.dirname(module_file)
        # FIXME: This part is fragile and dependent on the repostory structure!!!
        parent_egg_module_directory = "/".join(os.path.dirname(module_file).split("/")[:-3])

        # NOTE: For binary install python packages, you can't just access the
        # JSON file, since it is in a "python egg" (this behaves like a zipped
        # directory). To get around this, we check if the module directory we
        # are currently in is a zipfile or not:
        #
        # Determine what kind of module_directory it actually is:
        regular_dir = os.path.isdir(module_directory)
        egg_dir = zipfile.is_zipfile(module_directory)
        parent_egg_dir = zipfile.is_zipfile(parent_egg_module_directory)

        if regular_dir:
            using_egg = False
            json_files = glob.glob(module_directory+"/*.json")
        else:
            using_egg = True
            if egg_dir:
                zipped_egg_file = zipfile.ZipFile(egg_dir, "r")
            elif parent_egg_dir:
                zipped_egg_file = zipfile.ZipFile(parent_egg_module_directory, "r")
            else:
                raise OSError("Could not find:", egg_dir, parent_egg_module_directory)
            json_files = []
            for thisfile in zipped_egg_file.namelist():
                json_files.append(thisfile)

        host_file = [f for f in json_files if os.path.basename(f).split(".")[0] in HOSTNAME]
        assert len(host_file) == 1
        host_file = host_file[0]

        if using_egg:
            host_json = json.loads(zipped_egg_file.read(host_file))
            self.__dict__.update(host_json)
        else:
            with open(host_file) as host_file:
                host_json = json.load(host_file)
                self.__dict__.update(host_json)

        # attach the batch system(s)
        if batch_system is None:
            batch_system = host_json["batch_system"]
        importlib.import_module("pyesm.core.batch_systems."+batch_system, batch_system.capitalize())
        this_batch_system = getattr(sys.modules["pyesm.core.batch_systems."+batch_system],
                                    batch_system.capitalize())
        self.batch_system = this_batch_system()
