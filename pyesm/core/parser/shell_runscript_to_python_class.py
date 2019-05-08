"""
Main wrapper to get an old-style esm runscript going with the python backend.
"""
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

from ruamel.yaml import YAML, yaml_object

from pyesm.core.setup.setup_compute import SetUpCompute

yaml = YAML()


def main():
    """
    Starts a model simulation.

    This contains new functionality to:
    + Load the environment passed from the shell

    This also contains all the functionality previously found in the esm-runscripts
    to:
    + Load the appropriate information describing the machine
    + Determine the setup that should be simulated
    + Dynamically loads and initializes this setup
    """
    setup = SetUpCompute()    
    print(80*"*")
    setup.dump_yaml_to_stdout() 
    
    # print('#'*80)
    # this_setup.echam._prepare_files_from_restart_in()
    # for thisfile in this_setup.echam.files['restart']:
    #    print(thisfile)
    # this_setup.echam.files['restart'].digest()
    # print('Calling all PREPARE steps')
    # this_setup._call_phase('prepare')
    # print('done')

if __name__ == '__main__':
    main()
