"""
Echam Standalone Setup
"""
import sys

from ruamel.yaml import YAML, yaml_object

from pyesm.core.setup.setup_compute import SetUpCompute

yaml = YAML()


@yaml_object(yaml)
class echam_standalone(SetUpCompute):
    def __init__(self, env):
        self.NAME = "echam_standalone"
        self.components = {"echam": {
            "is_coupled": False,
            "resolution": env.get("RES_echam", "T63")
            },
                          }
        super(echam_standalone, self).__init__(env)

        yaml.dump(self, sys.stdout)
