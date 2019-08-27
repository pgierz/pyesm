"""
jsbach Component

A vegetation Model, Version 3.20


----
"""

from ruamel.yaml import YAML, yaml_object

from pyesm.components.echam import Echam


yaml = YAML()


@yaml_object(yaml)
class Jsbach(Echam):
    """
    Basic class for JSBACH; contains defaults needed by all compute, post-processing, and coupling jobs
    """
    NAME = "jsbach"
    VERSION = "3.20"
    TYPE = "vegetation"

    def __init__(self, dynveg=False, *args, **kwargs):
        self.using_dynveg = dynveg
        super(Jsbach, self).__init__(*args, **kwargs)
