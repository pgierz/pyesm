"""
Logging Handles for pyesm

This modules controls where logging messages go and how they are formatted. 

TODO:

----

"""

import inspect
import logging
from logging import *
import os

from ruamel.yaml import YAML, yaml_object


THIS_PID = str(os.getpid())
PARENT_PID = str(os.getppid())
yaml = YAML()


yaml.register_class(Logger)

def set_logging_this_module(log_dir=None, log_tag=None):
    """ Sets logging for whatever calls this function to Modulename_<log_tag>_<PID>.log
    
    Parameters
    ----------
    log_dir : str, optional
        The directory where the log file should be written
    log_tag : str, optional
        Default is None. This can be a string used to identify the logfile

    Returns
    -------
    logger : logging.Logger
        A logger object is returned with the specified filename.
    """
    file_name_of_calling_function = inspect.stack()[1]
    mod = inspect.getmodule(file_name_of_calling_function[0])
    try:
        logger = logging.getLogger(mod.__name__)
    except AttributeError:
        print("Sorry, no specific logging possible...")
        return
    logger.setLevel(logging.INFO)

    log_file_parts = [x for x in [mod.__name__, log_tag, THIS_PID] if x !=None]
    log_file = "_".join(log_file_parts)+".log"

    if log_dir:
        log_file = "/".join([log_dir, log_file])
    file_handler = logging.FileHandler(log_file)

    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger


def set_logging_main_output(expid=None, jobtype=None, date=None):
    """ Sets logging to a file for the 'main' (info) output """
    logfile_name = "_".join([expid, jobtype, date, THIS_PID]) + ".log"
    # TODO: Add a format and datefmt
    logging.basicConfig(filename=logfile_name, level=logging.INFO)
