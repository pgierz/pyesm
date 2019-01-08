.. _Dev_04:

################
Dev: File Tables
################

To maximize the reusability of the actual infrastructure for running
simulations, all of the file manipulations to copy required inputs, forcings,
configurations, etc. around the filesystem occur via *file tables*. The Python
Standard Library provides a native interface to the ``JSON`` file format, which
has the added advantage of being a language agnostic format, so that the same
file tables can principly be used with other programming languages.

The component_cookiecutter program automatically generates three filetable
examples for you to use. The first one,
``random_clouds_0.1_prepare_default_files.json``, looks like this:

.. code-block:: python

   {
     "config": {
       "first_config": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/config/file", 
         "src": "/path/to/config/file"
       }, 
       "second_config": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/config/file", 
         "src": "/path/to/config/file"
       }, 
       "third_config": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/config/file", 
         "src": "/path/to/config/file"
       }
     }, 
     "forcing": {
       "first_forcing": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/forcing/file", 
         "src": "/path/to/forcing/file"
       }, 
       "second_forcing": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/forcing/file", 
         "src": "/path/to/forcing/file"
       }, 
       "third_forcing": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/forcing/file", 
         "src": "/path/to/forcing/file"
       }
     }, 
     "input": {
       "first_input": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/input/file", 
         "src": "/path/to/input/file"
       }, 
       "second_input": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/input/file", 
         "src": "/path/to/input/file"
       }, 
       "third_input": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/input/file", 
         "src": "/path/to/input/file"
       }
     }, 
     "restart": {
       "first_restart": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/restart/file", 
         "src": "/path/to/restart/file"
       }, 
       "second_restart": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/restart/file", 
         "src": "/path/to/restart/file"
       }, 
       "third_restart": {
         "copy_method": "copy", 
         "dest": "/path/to/destination/of/restart/file", 
         "src": "/path/to/restart/file"
       }
     }
   }


You can see that for most of the filetypes (the top level dictionaries, e.g.
``config``), you can declare a collection of files with unique identifiers,
followed by the ``src``, ``dest``, and ``copy_method`` seen earlier.

The second file, ``random_clouds_0.1_prepare_modify_files.json`` should contain
a subset of these files, with alternative sources, destinations, or copy
methods. In principle, you could also declare additional files there that are
not in the first file table.

One important thing to note is the unique identifier given to each file, e.g.
"first_input". Should an environmental variable exist with this name, the
``ComponentCompute`` object will use the value of that variable as the ``src``,
and override the information in both the default and modify filetables. This
should allow for already-implemented components, e.g. ``ECHAM6`` to use some of
their environmental variables to override the filetables. For example
``JAN_SURF_echam`` could be used as a file identifier in the new file table to
allow the old runscripts to maintain some of their functionality.

The last file table, ``random_clouds_0.1_cleanup_default_files``, contains a
list of files that should be moved *from* the work folder *to* the experiment
tree after a supercomputer job has finished. The example looks like this:

.. code-block:: python

   {
     "outdata": {
       "first_output": {
         "dest": "@EXPID@_@NAME@_name_of_output_file_@DATE@.nc", 
         "src": "name_of_output_file"
       }
     }, 
     "restart": {
       "first_restart": {
         "dest": "@EXPID@_@NAME_restart1_@DATE@.nc", 
         "src": "name_of_restart"
       }
     }
   }

Here, an important thing to note is the special string components ``@EXPID@``,
``@NAME@``, and ``@DATE@``, which are interpolated to the experiment id,
component name, and current experiment date, respectively. Note also that the
``src`` and ``dest`` do not specify a directory. It is assumed that ``src``
**always** is ``work_dir``, and ``dest`` is **always** ``outdata_dir``.

Next we will look at the actual phases of the simulation, and what occurs during each step.


----

Previous: :ref:`Dev_03`

Next: :ref:`Dev_05`
