"""
Echam Standalone Setup
"""
import os
from pkg_resources import resource_filename

from ruamel.yaml import YAML, yaml_object
import pyesm

from pyesm.core.setup.setup_compute import SetUpCompute

yaml = YAML()

MODULE_ROOT = os.path.dirname(pyesm.__file__)



@yaml_object(yaml)
class setup_standalone(SetUpCompute):
    def __init__(self, env):
        self.components = {
                self.NAME: {
                    'yaml_file': resource_filename('pyesm', '/components/'+self.NAME+'/'+self.NAME+'.yaml') 
                },
            }
        super(setup_standalone, self).__init__(env)
        for component in self.components:
            if 'include_submodules' in component._config:
                for submodule in component._config['include_submodules']:
                    setattr(submodule, component_compute(yaml_file=resource_filename(
                        'pyesm',
                        '/components/'+submodule+'/'+submodule+'.yaml')
                        )
