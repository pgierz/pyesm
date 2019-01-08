.. _Dev_01:

#################
Dev: Introduction
#################

Before we get to any actual code, there are some definitions that need to be clarified.

:class:`SimElement <pyesm.helpers.SimElement>`
        The basic element of an ESM system is a :class:`SimElement
        <pyesm.helpers.SimElement>`. These objects should have clearly defined
        names and version numbers, and "type" descriptions (e.g.  atmosphere
        model, ocean model, coupler, etc...)

:class:`Component <pyesm.component.Component>`
        A component is a fully functional model, which could be run as is and
        produce interesting physical outputs. An ocean circulation model (e.g.
        ``FESOM``) is a Component.

:class:`SetUp <pyesm.setup.SetUp>`
        A collection of :class:`Component <pyesm.component.Component>` objects
        which run as one job on a supercomputer. These :class:`Component
        <pyesm.component.Component>` objects usually exchange information over
        some sort of coupling interface, for instance the ``OASIS3mct``
        library.

Both :class:`Component <pyesm.component.Component>` and :class:`SetUp
<pyesm.setup.SetUp>` are specialized types of :class:`SimElement
<pyesm.helpers.SimElement>`. In order to make life easier for simulation
scientists, the tools in this framework try to provide easy access to the
following tasks:

#. Downloading ESM code (usually in Fortran or C)
#. Compiling the ESM code for a specific supercomputer
#. Running a simulation
#. Archiving the results
#. Analysis of the output

Each of these tasks can be described by a specific object and methods connected
to it. The number of methods needed to fully describe a certain task may vary.

We will work through these steps to implement a dummy component
``random_clouds``, which randomly generates cuboids of up to 3x5x1 in a
20x20x50 matrix, and moves them along with a gentle wind. We will also
implement ``random_clouds_standalone`` as a :class:`SetUp <pyesm.setup.SetUp>`
to actually execute simulations using ``random_clouds``.

----

Previous: :ref:`index`

Next: :ref:`Dev_02`
