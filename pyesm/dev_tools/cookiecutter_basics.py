#!/usr/bin/env python

import argparse
import subprocess

def parse_args_component():
    """ The argument parser: Gets the name of the component """
    parser = argparse.ArgumentParser()
    parser.add_argument("NAME", help="The name of the component you want to implement")
    parser.add_argument("VERSION", help="The version of the component you want to implement")
    parser.add_argument("TYPE", help="The type of the component you want to implement")
    parser.add_argument("-v", "--verbose", help="increase verbosity", action="store_true")
    return parser.parse_args()

def parse_args_setup():
    """ The argument parser: Gets the name of the component """
    parser = argparse.ArgumentParser()
    parser.add_argument("NAME", help="The name of the setup you want to implement")
    parser.add_argument("VERSION", help="The version of the setup you want to implement")
    parser.add_argument("TYPE", help="The type of the setup you want to implement")
    parser.add_argument("-v", "--verbose", help="increase verbosity", action="store_true")
    return parser.parse_args()

def initialize_git_repo(name):
    """ Initializes a git repository as a submodule in the main pyesm repo """
    print("\t Creating a git repository for %s" % name)
    print(subprocess.check_output(["git", "init", name]))
    print("\t Please make sure to add a remote to this repository!")
