"""
This module is magical. It allows you to dynamically load classes from modules
and initialize them.



                   DO NOT TOUCH ANYTHING HERE UNLESS YOU KNOW

                              ***E X A C T L Y***

                             WHAT YOU ARE DOING!!!



                            YOU HAVE BEEN WARNED!!!

Otherwise, you will suffer the consequences of badly traceable failures, and I
will feel very sorry for you.

Good luck,
PG
"""
import importlib
import sys


def dynamically_load_and_initialize_setup(setup_name, *setup_args, **setup_kwargs):
    """
    Dynamically loads a setup and initializes it.

    Given a setup with ``setup_name``, this function will dynamically import
    it, under the assumption that the setup's module file is found under
    ``pyesm.setups.<setup_name>``, and the class is named ``setup_name``.
    Further arguments and keyword arguments are passed to the constructor of
    the class.

    Parameters
    ----------
    setup_name : str
        The name of the setup you are trying to import
    *args :
        All positional arguments you need to construct ``setup_name``'s class.
    **kwargs:
        All keyword arguments you need to construct ``setup_name``'s class.

    Returns
    -------
    initialized_setup :
        An initialized model setup for ``setup_name``

    Examples
    --------
    Suppose you want to import a setup named echam_standalone, and initialize
    it's compute class. From a regular script, you would write

    >>> pyesm.setups.echam_standalone import echam_standalone
    >>> my_echam_standalone = echam_standalone()

    Assuming this class **does not** need any constructor arguments, you can
    instead do this:

    >>> my_echam_standalone = dynamically_load_and_initialize_setup("echam_standalone")
    """
    importlib.import_module("pyesm.setups."+setup_name)
    setup = getattr(sys.modules["pyesm.setups."+setup_name], setup_name)
    initialized_setup = setup(*setup_args, **setup_kwargs)
    return initialized_setup


def dynamically_load_and_initialize_component(component_name, job, *component_args, **component_kwargs):
    """
    Dynamically loads a component and initializes it.

    Given a component with ``component_name``, this function will dynamically
    import it, under the assumption that the component's module file is found under
    ``pyesm.components.<component_name>``, and the class is named
    ``component_name``. Further arguments and keyword arguments are passed to
    the constructor of the class.

    Parameters
    ----------
    component_name : str
        The name of the setup you are trying to import
    job : str
        The job that the component should do, e.g. compute, post_process, couple
    *component_args :
        All positional arguments you need to construct ``component_name``'s
        class.
    **component_kwargs:
        All keyword arguments you need to construct ``component_name``'s class.

    Returns
    -------
    initialized_component :
        An initialized component for ``component_name``

    Examples
    --------
    Suppose you want to import a component named echam, and initialize
    it's compute class. From a regular script, you would write

    >>> from pyesm.components.echam_compute import EchamCompute
    >>> my_echam = EchamCompute()

    Assuming this class **does not** need any constructor arguments, you can
    instead do this:

    >>> my_echam = dynamically_load_and_initialize_component("echam", "compute")
    """
    importlib.import_module("pyesm.components."+component_name+"."+component_name+"_"+job)
    component_class_name = "".join([component_name_part.capitalize() for
                                    component_name_part in
                                    component_name.split("_")]) + \
                           job.capitalize()
    component = getattr(sys.modules["pyesm.components."+component_name+"."+component_name+"_"+job],
                        component_class_name)
    print(component, component_args, component_kwargs)
    initialized_component = component(*component_args, **component_kwargs)
    return initialized_component


def list_all_loaded_modules():
    """ Prints all loaded modules to stdout """
    key_list = sorted(sys.modules.keys())
    maxlen = 3+len(max(key_list, key=len))
    debug_str = "{:<"+str(maxlen)+"}{:<"+str(maxlen)+"}{:<}"
    for key_a, key_b, key_c in zip(key_list[::3], key_list[1::3], key_list[2::3]):
        print(debug_str.format(key_a, key_b, key_c))
