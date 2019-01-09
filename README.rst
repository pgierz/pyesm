.. _index:

``ESM Tools`` Documentation
===========================
|docs| |tests|

.. |docs| image:: https://readthedocs.org/projects/pyesm/badge/?version=latest 
   :target: https://pyesm.readthedocs.io/en/latest/?badge=latest 

.. |tests| image:: https://travis-ci.org/pgierz/pyesm.svg?branch=master 
    :target: https://travis-ci.org/pgierz/pyesm 


**esm-tools** are a small collection of tools to facilitate work with Earth System Models, written in Python

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
   :align: center
   
----

Installation Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^

Still to come...

----

For Users
^^^^^^^^^

**Note**: The commands shown below do not work yet, they are still under
development!

A basic workflow would look like this:

.. code-block:: shell

   $ pyesm install <Model_Name>

   Reading user configuration from ~/.config/pyesmrc...
   Downloading <Model_Name>...
   Configuring <Model_Name> for <Host>...
   Compiling...
   ...done!

   $ pyesm run <Config_Script>

   Initializing experiment <expid>
   ... more logging info ...
   Submitted batch job <expid> to compute queue

See the `documentation <https://pyesm.readthedocs.io/en/latest/#for-users>` for
more information.

----

For Developers
^^^^^^^^^^^^^^

**Note**: The command-line interface shown below does not work yet, it's still
under development:

You can get templates for a new component or setup with the following:

.. code-block:: shell

   $ pyesm develop component <Component Name>

   Generating git repository for infrastructure code for <Component Name>...
   Wrote <Component>/__init__.py
   Wrote <Component>/<component>_simulation.py
   Wrote <Component>/<component>_analysis.py
   Wrote <Component>/<component>_visualization.py

A similar command would be available for ``setup``.

See the development `quickstart
<https://pyesm.readthedocs.io/en/latest/#for-developers>`.

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

.. Links to external references:
.. _BUGS: https://gitlab.dkrz.de/esm-tools/esm-runscripts/issues/new?issue%5Bassignee_id%5D=&issue%5Bmilestone_id%5D=
__ BUGS_
