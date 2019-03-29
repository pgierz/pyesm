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
import pkg_resources
import socket
import sys
import zipfile

from ruamel.yaml import YAML, yaml_object
yaml = YAML()


@yaml_object(yaml)
class Host(object):
    def __init__(self, machine_name=None, batch_system=None):
        """ 
        Determines hostname and sets up attributes

        Parameters
        ----------
        machine_name : str
            Default is ``None``; in this case the hostname will be determined automatically. 
        batch_system : str
            Default is ``None``; in this case the batch_system associated with
            the host is read from the JSON file.

        Example
        -------
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
        HOSTNAME = machine_name or socket.gethostname()
        module_file = inspect.getfile(Host)
        # NOTE: For binary installed Python packages, you can't just access the
        # JSON file, since it is in a "python egg" (this behaves like a zipped
        # directory). I guess the core Python dev team was trying to make a
        # clever joke. Snakes lay eggs. Ok then...
        #
        # To get around this, we can use ``pkg_resources`` library; which ships
        # with the standard library. I had written an ad-hoc solution before in
        # Potsdam; but using the standard library's version has benefits:
        #
        # 1. It's well documented (see here: LINK)
        # 2. It doesn't use zipfile, which has a confusingly named method
        #    ``namelist`` which could induce a mixup between a ``ZipFile``'s "list
        #    of names in the file" and a FORTRAN namelist; which we use all the
        #    time for models...
        #
        # Note on the NOTE: should this go into the class's docstring? Or is it
        # sufficient to keep this info here?
        json_files = [f for f in pkg_resources.resource_listdir(__name__, os.path.dirname(__name__)) if f.endswith(".json")]
        host_file = [f for f in json_files if os.path.basename(f).split(".")[0] in HOSTNAME]
        assert len(host_file) == 1
        host_file = host_file[0]
        host_file = pkg_resources.resource_stream(__name__, host_file)
        host_json = json.load(host_file)
        self.__dict__.update(host_json)
        # attach the batch system
        if batch_system is None:
            batch_system = host_json["batch_system"]
        # NOTE: This next line is fragile and depends on the repository layout:
        importlib.import_module("pyesm.core.batch_systems."+batch_system, batch_system.capitalize())
        this_batch_system = getattr(sys.modules["pyesm.core.batch_systems."+batch_system],
                                    batch_system.capitalize())
        self.batch_system = this_batch_system()
