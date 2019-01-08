.. _index:

``ESM Tools`` Documentation
===========================
.. image:: https://readthedocs.org/projects/pyesm/badge/?version=latest
   :target: https://pyesm.readthedocs.io/en/latest/?badge=latest
         :alt: Documentation Status
----

The `esm-tools` aim at simplifing the construction of experiments with Earth
System Models. Presented here is a unified framework which will allow
scientists to:

   1. Download numerical **Earth System Models** code, which may represent
      physical processes of the atmosphere, ocean, cryosphere, solid earth,
      or other components of Earth's physical environment
   2. **Compile** these models on a variety of supercomputing platforms
   3. Design **self-documenting experiments** which these models.
   4. Perform **reproducable analysis** on the results of such experiments
   5. Archive the utilized data, enabling the scientist to subconsciously
      comply with **good scientific practice**
   6. Get *out of the way*, so you can do science and not worry about:
        a. Batch Systems
        b. Compiler Optimization
        c. Documenting the analysis
        d. Archiving your results
        e. Sharing the analysis in an easy, reproducable manner

To accomplish this goal, the ESM Team has developed a toolkit which allows all
of the above six steps to be accomplished with relatively little overhead for
the user. It's written in ``python``.

You should be able to minimize days like this when using the tools (at least partially):

.. image:: https://imgs.xkcd.com/comics/computer_problems.png

----

Installation Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^

Still to come...

----

For Users
^^^^^^^^^
If you only want to run a model and aren't aiming to implement a new system
into this framework, you should be read the documentation and then be able to:

1. Select and download a model
2. Compile the model for your platform
3. Generate an experiment

Start Here: :ref:`User_01` (Nothing yet, sorry...)

----

For Developers
^^^^^^^^^^^^^^
What follows in this documentation is a generic outline of the philosophy
behind the tools. Upon reading this document and the accompanying example, you
should be able to:

1. Implement an example, dummy model
2. Extend this dummy model to an actual ESM you might want to run on a
   supercomputer
3. Have a solid grasp on where you need to implement model-specifics to
   enable you to share your model with other scientists.

Start Here: :ref:`Dev_01`

Unit and Integration Tests
""""""""""""""""""""""""""

There are a few unit and integration tests that are shipped with the code. You
can use a python test runner of your choice to run the test suite. The tester
built-in to the standard library can be run like this, assuming you are in the
top level directory of the python implementation:

.. code-block:: shell

   $ python -m unittest discover -s tests

Alternatively, if you prefer color in your tests, you can install the `green
<https://github.com/CleanCut/green>`_ tester and then use the command:

.. code-block:: shell

   $ green -rvvv

----

Other Notes
^^^^^^^^^^^

This software is still under active development, with a full release planned
for end of winter 2019 (Feb/March). It is a re-implementation of the esm-tools
written in ``ksh``. Therefore, if you run into any problems, *please let the
development team know!* While the end-goal is a smoother experience for
everyone, this probably won't be immediate and we will need to iron out some
wrinkles at the beginning.

Why Re-Implement already functionional ``ksh``?
"""""""""""""""""""""""""""""""""""""""""""""""

We chose to re-do everything in ``python`` since it's a significantly more
modern language, is easier to maintain, and is less daunting to new developers.
Plus, it's been fun to re-write some of this stuff, and the code-base has
shrunken significantly.

----

Regardless of your purpose, you should please `report bugs and request new
features for future implementation.`__

----

Table of Contents
^^^^^^^^^^^^^^^^^

**User Documentation**

Nothing yet, sorry...

**Developer Documentation**

.. toctree::
   :maxdepth: 1

   usage/dev/Dev_01_Intro
   usage/dev/Dev_02_ComponentLayout
   usage/dev/Dev_03_Basic_Classes
   usage/dev/Dev_04_FileTables
   usage/dev/Dev_05_SimCycle

**Technical Documentation**

.. toctree::
   :maxdepth: 1

   source/batch_systems
   source/component
   source/compute_hosts
   source/database
   source/downloader
   source/helpers
   source/setup
   source/time_control


Indices and tables
^^^^^^^^^^^^^^^^^^

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. Links to external references:
.. _BUGS: https://gitlab.dkrz.de/esm-tools/esm-runscripts/issues/new?issue%5Bassignee_id%5D=&issue%5Bmilestone_id%5D=
__ BUGS_
