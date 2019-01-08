.. _Dev_02:

#####################
Dev: Component Layout
#####################

To start implementing a new component, we can use the provided cookiecutter.
There's a hidden directory in the project root, ``${PYESM}/.dev_tools``. It
contains a few tools to help get set up. Assuming you are currently in the
project root, you can start like this:

.. code-block:: shell

        $ ./.dev_tools/component_cookiecutter \
                ${COMP_NAME} \
                ${COMP_VERSION} \
                ${COMP_TYPE}

For our example, we will do the following:

.. code-block:: shell

        $ ./.dev_tools/component_cookiecutter random_clouds 0.1 Generic

The file tree you have just created should look like this:

.. code-block:: shell

        random_clouds
        ├── .git
        ├── __init__.py
        ├── random_clouds_0.1_cleanup_default_files.json
        ├── random_clouds_0.1_prepare_default_files.json
        ├── random_clouds_0.1_prepare_modify_files.json
        └── random_clouds_simulation.py 

Examining the output of this command, you can see that:

1. A new ``git`` repository has been initialized for you, ``random_clouds``.
   You should add a remote to this, and add it as a ``git submodule`` to the
   main ``PYESM`` project:

.. code-block:: shell 
        
        # Set up a remote and address somewhere, e.g. GitHub, GitLab, ...
        $ cd random_clouds
        $ git remote add ${REMOTE_NAME:-origin} ${ADDRESS:-ERR}
        $ cd ..
        $ git submodule add ${ADDRESS} random_clouds

2. We have files for ``__init__py`` and ``random_clouds_simulation.py``
3. Filetables have been generated with example entries. These will absolutely
   not work, since they point to paths that are not on your computer.

.. NOTE::

        Certain other files probably need to be added at some point,
        specifically those that implement classes dealing with archiving,
        analysis, and visualization. These are still to come...

Next, we will look at the classes implemented in ``__init__.py`` and ``random_clouds_simulation.py``.

----

Previous: :ref:`Dev_01`

Next: :ref:`Dev_03`
