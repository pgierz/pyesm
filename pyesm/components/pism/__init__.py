"""
Pism Component

Am Ice Model, Version: 1.1

Please write some more documentation.

Written by component_cookiecutter

----
"""

import logging
import os

from pyesm.core.component import Component


__all__ = ["Pism"]
__authors__ = ("Dr. Paul Gierz",)
# NOTE: The __version__ refers the version of the pyesm control infrastructure,
# not the version of the PISM ice sheet model.
__version__ = "0.1.0"


class Pism(Component):
    """ A docstring for your component """
    # NOTE: Currently, we default to the "official" ``PISM`` repo.
    DOWNLOAD_ADDRESS = "https://github.com/pism/pism.git"
    NAME = "pism"
    VERSION = "1.1"
    TYPE = "ice"

    def _resolution(self, res_key=()):
        """
        Defines the resolution and generates the following attributes

        + LateralResolution
        + VerticalResolution
        + Timestep
        + _nx
        + _ny
        + _nz
        + _ngridpoints

        For the ``PISM`` method ``_resolution``, we also set the attributes:

        + domain

        Parameters
        ----------
        res_key : tuple of (str, int)
                A tuple describing the domain (as a ``str``), and the lateral
                resolution of a grid cell edge (as an `int``, in kilometers)
        """
        Resolutions = {None:
                {
                    "LateralResolution": None,
                    "VerticalResolution": None,
                    "Timestep": None,
                    "_nx": None,
                    "_ny": None,
                    "_nz": None,
                    "_ngridpoints": None,
                },
               "nhem":
                {20:
                    {"LateralResolution": "20km",
                     "VerticalResolution": None,
                     "Timestep": None,
                     "_nx": None,
                     "_ny": None,
                     "_nz": None,
                     "_ngridpoints": None,
                    },
                }
              }
        domain, resolution = res_key
        setattr(self, "Domain", domain)
        for key, value in Resolutions[domain][resolution].items():
            setattr(self, key, value)
