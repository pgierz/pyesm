import importlib
import os
import sys

from pyesm.compute_hosts import Host
from ruamel.yaml import YAML
yaml=YAML()

class loaded_env():
    def __init__(self):
        self.__dict__.update(dict(os.environ))



this_env = loaded_env() 
yaml.register_class(loaded_env)
yaml.dump(this_env, sys.stdout)
this_machine = Host(this_env.machine_name,
                    batch_system=this_env.__dict__.get("batch_system", None))

this_setup = this_env.setup_name
importlib.import_module("pyesm.setups."+this_setup, this_setup)
