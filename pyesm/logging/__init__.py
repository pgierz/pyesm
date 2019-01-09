"""
Logging Handles for pyesm

This modules controls where logging messages go and how they are formatted. 

TODO:

+ [ ] I need to find out how to inherit from the regular logging module without breaking anything

----

"""


import inspect
import logging
import os

# get all logging methods here as plain names:
from logging import *

THIS_PID = str(os.getpid())
PARENT_PID = str(os.getppid())



def set_logging_this_module():
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    logger = logging.getLogger(mod.__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')

    file_handler = logging.FileHandler("_".join([mod.__name__, THIS_PID])+".log")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger

def set_logging_main_output(expid=None, jobtype=None, date=None):
    """ Sets logging to a file for the 'main' (info) output """
    logfile_name = "_".join([expid, jobtype, date, THIS_PID]) + ".log"
    # TODO: Add a format and datefmt
    logging.basicConfig(filename=logfile_name, level=logging.INFO)
