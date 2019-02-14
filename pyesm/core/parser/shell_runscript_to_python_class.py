"""
Main wrapper to get an old-style esm runscript going with the python backend.
"""
import os
import sys

from ruamel.yaml import YAML, yaml_object

from pyesm.core.dark_magic import dynamically_load_and_initialize_setup

yaml = YAML()


# NOTE: Not sure why this is needed, since we have os.environ available to us
# anyway...
@yaml_object(yaml)
class LoadedEnv():
    """ Loads the environment and stores all keys as attributes of a LoadedEnv instance """
    def __init__(self):
        self.__dict__.update(dict(os.environ))


def main():
    """
    Starts a model simulation.

    This contains all the functionality previously found in the esm-runscripts
    to:
    + Load the environment passed from the shell
    + Load the appropriate table describing the machine
    + Determine the setup that should be simulated
    + Dynamically loads and initializes this setup
    """
    this_env = LoadedEnv()

    yaml.dump(this_env, sys.stdout)

    this_setup = os.environ.get("setup_name")
    this_setup = dynamically_load_and_initialize_setup(this_setup, this_env.__dict__)
    print("#"*80)
    this_setup.echam._prepare_read_from_dataset()
    yaml.dump(this_setup.echam.files, sys.stdout)

if __name__ == "__main__":
    main()
