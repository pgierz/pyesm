.. _Dev_03:

##################
Dev: Basic Classes
##################

We will now look at the two classes that have been generated

``__init__.py``
===============

.. code-block:: python
   :linenos:
   :emphasize-lines: 21,22,23,24,26,30,31,32,33,34,35,36,37
   
   """
   random_clouds Component
   
   A Generic Model, Version: 0.1
   
   Please write some more documentation.
   
   Written by component_cookiecutter
   
   ----
   """

   import logging
   import os

   from component import Component


   class RandomClouds(Component):
           """ A docstring for your component """
           DOWNLOAD_ADDRESS = "http://some/address/of/a/project"
           NAME = "random_clouds"
           VERSION = "0.1"
           TYPE = "Generic"

           def _resolution(self, res_key=None):
               """
               Defines the resolution and generates the following attributes
               """
               Resolutions = {None:
                               {"LateralResolution": None,
                               "VerticalResolution": None,
                               "Timestep": None,
                               "_nx": None,
                               "_ny": None,
                               "_nz": None,
                               "_ngridpoints": None,
                               }
                             }
               for key, value in Resolutions[res_key].items():
                   setattr(self, key, value)

While the basic class might seem deceptively small, this is due to the fact
that a lot of the logic required to construct experiments is independent of the
actual name, type, and version. Going through what needs to be adapted:

+ The ``DOWNLOAD_ADDRESS`` points to the repository where the actual simulation
  code (Fortran or C) can be retrieved.  This needs to be filled in to allow
  users to easily download your model.
+ The ``NAME``, ``VERSION``, and ``TYPE`` are all attached to object instances
  as ``NAME``, ``Name``, and ``name`` (similarly for ``VERSION`` and ``TYPE``.
  While the standard convention is to use the ``Name`` formatting, the
  alternatives are also available.)
+ The hidden method ``_resolution`` should get the default resolution you want
  users to use when running simlations. If there is no obvious default, remove
  the ``=None`` in order to make the argument mandatory.
+ The ``Resolutions`` available to your model should be entered as dictionary
  keys, with appropriate values.

.. sidebar:: Naming Conventions

        Some of the magic behind the ``esm-tools`` relies on very specific
        naming "conventions" (or, to be a bit more brutal, "laws"). Since
        certain ``Component`` objects contained within a ``SetUp`` are loaded
        during runtime, specific patterns are necessary for everything to work.
        Therefore:

        + ``your_component`` should be the name of the directory for all code
          for a specific component.
        + ``YourComponent`` should be the base class, which **must** inherit
          from ``Component``. Notice that we use Capital for each seperate
          word, and underscores are replaced by direct word connections. 
        + ``YourComponentCompute`` should be the compute class, and **must**
          inherit from the following **in this order**:

          #. ``YourComponent``
          #. ``ComponentCompute``

That's it! All the other magic occurs in :class:`pyesm.helpers.SimElement` and
:class:`pyesm.component.Component`, so you can read the full documentation for
those objects if you are curious. Next we describe some of the methods and
attributes that ``RandomClouds`` inherited, and how you might want to use them.

When initializing a ``RandomClouds`` object, you will see that you
automatically get *attributes* representing the experiment id, ``expid``. This
can be passed in to the construction call as an argument ``expid``.
Furthermore, you get attributes describing the various directories that you
might need to access: :attr:`_parent_dir
<pyesm.helpers.SimElement._parent_dir>`, and one each for ``config``,
``forcing``, ``input``, ``log``, ``mon``, ``outdata``, ``restart`` as, e.g.
``_outdata_dir``. There is also a method which allows for the generation of
directories within the experiment tree, :meth:`_register_directory(dir_name,
use_Name=True) <pyesm.helpers.SimElement._register_directory>`. If given the
argument ``use_Name=True`` (this is the default value), a subdirectory is made
with the name of the component as stored under the attribute ``self.Name``,
with ``use_Name=False``, you only get the ``dir_name``. Additionally, this
method registers the directory to the object in a similar way as e.g.
``_outdata_dir``.

In addition to the experiment id, file directories, and resolution attributes,
perhaps the most-used attribute of your new component will be
:attr:`RandomClouds.files <pyesm.component.Component.files>`. If you
instantiate a new object of your ``RandomClouds``, you can do the following:

.. code-block:: python

   >>> from random_clouds import RandomClouds
   >>> my_random_clouds = RandomClouds()
   >>> my_random_clouds.files
   {'config': <helpers.FileDict at 0x101b37550>,
    'forcing': <helpers.FileDict at 0x101b37ed0>,
    'input': <helpers.FileDict at 0x101b377d0>,
    'log': <helpers.FileDict at 0x101b37f90>,
    'mon': <helpers.FileDict at 0x101b37cd0>,
    'outdata': <helpers.FileDict at 0x101b37a10>,
    'restart': <helpers.FileDict at 0x101b3a110>}

You can see how you have a dictionary, where each key represents one of the
main filetypes (These can also be listed out over the :attr:`_filetypes
<pyesm.helpers.SimElement._filetype>` attribute)

:class:`ComponentFile <pyesm.helpers.ComponentFile>` and :class:`FileDict <pyesm.helpers.FileDict>`
===================================================================================================

Notice that the values of the ``my_random_clouds.files`` dictionary have the
type :class:`pyesm.helpers.FileDict`. :class:`FileDict
<pyesm.helpers.FileDict>` are specialized dictionaries which have two important
differences from regular dictionaries:

#. They **only** accept values of type :class:`ComponentFile <pyesm.helpers.ComponentFile>`
#. They have a special :meth:`digest <pyesm.helpers.FileDict.digest>` method.

The :class:`pyesm.helpers.ComponentFile` object has three attributes, a
:attr:`src <pyesm.helpers.ComponentFile.src>` (where a file should be taken
from), a :attr:`dest <pyesm.helpers.ComponentFile.dest>` (where the file should
go) and a :attr:`copy_method <pyesm.helpers.ComponentFile.copy_method>`. When
initializing a :class:`ComponentFile <pyesm.helpers.ComponentFile>` all three
of these arguments are strings, and you can select either ``"link"`` or
``"copy"`` as ``copy_method``. The default is ``"copy"``. This is then
translated to an appropriate system call.  :class:`pyesm.helpers.ComponentFile`
objects, like the :class:`FileDict <pyesm.helpers.FileDict>` also have a
:meth:`digest <pyesm.helpers.ComponentFile.digest>` method, which uses the copy
method to manipulate the file system and also produce some logging output to
keep track of what is happening.  The :meth:`digest <pyesm.helpers.FileDict.digest>`
method of the :class:`FileDict <pyesm.helpers.FileDict>` takes all of the
:class:`ComponentFile <pyesm.helpers.ComponentFile>` objects and calls the
:meth:`digest <pyesm.helpers.ComponentFile.digest>` method for each of them,
manipulating all the files in one go. The keys of the :class:`FileDict
<pyesm.helpers.FileDict>` allow you to assign human-understandable
names to each of the files, therefore making looking them up and changing them
easier.  You can see how it might be easy to allocate files into this system,
e.g.

.. code-block:: python

   >>> from random_clouds import RandomClouds
   >>> from helpers import ComponentFile
   >>>
   >>> my_random_clouds = RandomClouds()
   >>>
   >>> my_random_clouds.files["input"]["first_input_file"] = ComponentFile(src="/some/input/file",
                                                                           dest="/should/go/here",
                                                                           copy_method="copy")

We will show an even easier way to do this for large numbers of files in the
next part.

:meth:`_call_steps <pyesm.helpers.SimElement._call_steps>`
============================================================

The last interesting method to discuss on the basic ``RandomClouds`` class is
:meth:`_call_steps <pyesm.helpers.SimElement._call_steps>`. This allows you
to call a series of work steps to perform, with hooks for user-defined
functions before and after each step. When using :meth:`_call_steps
<pyesm.helpers.SimElement._call_steps>`, two arguments must be given:

#. a ``phase`` (as a ``str``), which is common for all steps.
#. a ``steps`` ``list``, which names each of the steps in turn.

Let's say you define a few steps for a "diagnostics" phase:

.. code-block:: python

   def _diagnostics_determine_temperature(self):
       # ... some commands that average all your temperature output ...   

   def _diagnostics_determine_salinity(self):
       # ... some commands that average all your salinity output ...

You could now call all of these with the the command:

.. code-block:: python

   >>> from random_clouds import RandomClouds
   >>> my_random_clouds import RandomClouds()
   >>> my_random_clouds._call_steps("diagnostics", ["determine_temperature", "determine_salinity"])
   >>> # In logging.debug output:
   >>> # Calling my_random_clouds._diagnostics_determine_temperature()
   >>> # Calling my_random_clouds._diagnostics_determine_salinity()

However, the power of this is that a user can add steps before and after each.
Consider the following in addition to what we already have:

.. code-block:: python

   >>> def temperature_prep_function():
           # ...some commands which might prepare files to use ...
           print("Hi, the user function is now done!")
   >>>
   >>> RandomClouds._diagnostics_user_determine_temperature = temperature_prep_function
   >>> enhanced_random_clouds = RandomClouds()
   >>> enhanced_random_clouds._call_steps("diagnostics", ["determine_temperature", "determine_salinity"])
   >>> # Calling enhanced_random_clouds._diagnostics_user_determine_temperature()
   'Hi the user function is now done!'
   >>> # Calling enhanced_random_clouds._diagnostics_determine_temperature()
   >>> # Calling enhanced_random_clouds._diagnostics_determine_salinity()

In this way, users can attach self-defined functions before (with ``user`` in
the method name) and after (with ``USER`` in the method name) specific methods
to gain additional control. *Note* that this must happen before the object has
been initialized!

The :class:`ComponentCompute <pyesm.component.ComponentCompute>` Class and ``component_simulation.py``
======================================================================================================

Next, we will look at how to control the preparation, execution, and cleanup of
actual simulations. The functionally for these tasks are contained in
``random_clouds_simulation.py``:

.. code-block:: python
   :linenos:

   """
   Compute and Post-Processing Jobs for random_clouds
   
   Written by component_cookiecutter
   
   ----
   """
   
   from component.component_simulation import ComponentCompute
   from random_clouds import RandomClouds
   
   class RandomCloudsCompute(RandomClouds, ComponentCompute):
       """ A docstring. Please fill this out at least a little bit """
   
       def _compute_requirements(self):
           """ Compute requriments for random_clouds """
           self.executeable = None
           self.command = None
           self.num_tasks = None
           self.num_threads = None
  
As with the basic class, much of the functionality needed to run simulations is
inherited. In principle, we only need to specify the executable name, the
command used to start the executable (with applicable flags), and the number of
CPUs to use.

While there are several inherited methods from :class:`ComponentCompute
<pyesm.component.ComponentCompute>`, we will currently only introduce one, and
save the rest for later

The method :meth:`_read_filetables
<pyesm.compute.ComponentCompute._read_filetables>` allows you to quickly
populate the :class:`FileDict <pyesm.helpers.FileDict>` objects within the
:attr:`ComponentCompute.files <pyesm.component.files>` dictionary. This occurs
by reading a file table, where each of the entires is a dictionary, which in
turn contains dictionaries corresponding to valid :class:`ComponentFile
<pyesm.helpers.ComponentFile>` arguments. A complete example of this will be
shown in the next section.

----

Previous: :ref:`Dev_02`

Next: :ref:`Dev_04`
