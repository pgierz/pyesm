#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='pyesm',
      version='2.0',
      description='Python-based Earth System Model Infrastructure Tools',
      author='D. Barbi, P. Gierz, N. Wieters',
      author_email='pgierz@awi.de',
      url='https://github.com/pgierz/pyesm',
      packages=find_packages(), 
      install_requires=["pendulum", "cdo", "f90nml"],
     )
