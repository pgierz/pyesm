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
import inspect
import json
import logging
import os
import socket

class Host(object):
    def __init__(self):
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
        logging.debug(80*"*")
        HOSTNAME = socket.gethostname()
        logging.debug("\nInitializing a Host object with attributes for %s", HOSTNAME)
        module_file = inspect.getfile(Host)
        module_directory = os.path.dirname(module_file)

        json_files = glob.glob(module_directory+"/*.json")
        logging.debug("Found these host configuration files:")
        for json_file in json_files:
            logging.debug("\t\t - %s", json_file)

        host_file = [f for f in json_files if os.path.basename(f).split(".")[0] in HOSTNAME]
        assert len(host_file) == 1

        logging.info("\n\t\t - Loading: %s ", *host_file)
        with open(*host_file) as host_file:
            host_json = json.load(host_file)
            self.__dict__.update(host_json)
