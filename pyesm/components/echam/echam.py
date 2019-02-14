"""
echam Component

A atmosphere Model, Version: 6.3.04p1

Please write some more documentation.

Written by component_cookiecutter

----
"""

from ruamel.yaml import YAML, yaml_object

from pyesm.core.component import Component


yaml = YAML()


@yaml_object(yaml)
class Echam(Component):
    """ A docstring for your component """
    DOWNLOAD_ADDRESS = "http://some/address/of/a/project"
    NAME = "echam"
    VERSION = "6.3.04p1"
    TYPE = "atmosphere"

    def __init__(self, is_coupled=True, oceanres=None, *args, **kwargs):
        self.is_coupled = is_coupled
        self.oceanres = oceanres

        self.Resolutions = {
                    "T31":
                        {
                            "res": "T31",
                            "levels": "L19",
                            "Timestep": 450,
                            "_nx": 96,
                            "_ny": 48,
                            "_ngridpoints": 96*48,
                            },

                    "T63":
                        {
                            "res": "T63",
                            "levels": "L47",
                            "Timestep": 450,
                            "_nx": 192,
                            "_ny": 96,
                            "_ngridpoints": 192*96,
                            },

                    "T127":
                        {
                            "res": "T127",
                            "levels": "L47",
                            "Timestep": 200,
                            "_nx": 384,
                            "_ny": 192,
                            "_ngridpoints": 384*192,
                            },
                      }

        super(Echam, self).__init__(*args, **kwargs)
