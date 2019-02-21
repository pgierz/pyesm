"""
Compute and Post-Processing Jobs for Pism

Written by component_cookiecutter

----
"""

from pyesm.compute_hosts import Host
from pyesm.component.component_simulation import ComponentCompute
from pyesm.pism import Pism

class PismCompute(Pism, ComponentCompute):
    """ A docstring. Please fill this out at least a little bit """
    def __init__(self, host=None, **PismComputeArgs):
        super(PismCompute, self).__init__(**PismComputeArgs)
        if host and isinstance(host, Host):
                self.host = host
        else:
                self.host = Host()

        # TODO: Make a check for this
        self.POOL_DIR = "/work/ollie/pgierz/pool_pism"

    def _compute_requirements(self):
        """ Compute requirements for Pism """
        self.Executable = self.EXECUTEABLE = "pismr"
        self.COMMAND = 0
        self.NUM_TASKS = 0
        self.NUM_THREADS = 0

