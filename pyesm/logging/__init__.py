"""
Logging Handles for pyesm

This modules controls where logging messages go and how they are formatted. 

TODO:

----

"""


import inspect
import logging
import os

# get all logging methods here as plain names:
from logging import *

THIS_PID = str(os.getpid())
PARENT_PID = str(os.getppid())



def set_logging_this_module(log_dir=None, log_tag=None):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    logger = logging.getLogger(mod.__name__)
    logger.setLevel(logging.INFO)

    if log_tag:
        log_file_parts = [mod.__name__, log_tag, THIS_PID]
    else:
        log_file_parts = [mod.__name__, THIS_PID]
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
