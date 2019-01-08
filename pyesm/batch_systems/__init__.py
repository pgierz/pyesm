""" Batch Systems define a limited interface to various batch job systems (e.g.
`SLURM <https://slurm.schedmd.com>`_). Objects of this class can be used on
their own, or can be attached to other objects, e.g. a ``SetUp``

In the top-level of the module, a basic skeleton class which defines the
guarenteed interfaces offered by a ``BatchSystem`` object is defined. It needs
to have the following:

#. Attributes defining the:

    + The submitter (which command is needed to send a script to the queue)

    + Flags for the submitter

    + The launcher (which command is needed to start an executable on the compute node)

    + Flags for the launcher

    + The status command (which command is needed to check the queue)

    + The resource account (if you buy computer time, this is used to assign your simulation to a specific account)

#. Methods to check the full queue and your own jobs

#. Method to construct submitter and launcher commands and flags

Names of these attributes and methods are summarized below.

----

"""

from pyesm.compute_hosts import Host


class BatchSystem(object):
    """
    Skeleton class to define interface of a batch system
    """

    version = "0.1"

    def __init__(self, host=None):
       """
       Parameters
       ----------
       host : Host, optional
            Default ``None``. If the optional argument ``host`` remains
            ``None``, the configuration for the computing host you are
            currently working on is loaded. This is attached to the
            ``BatchSystem`` object as ``self._account``


       The following additional attributes are defined upon initialization:

       Attributes
       ----------
       submitter : str
            The command name used to submit jobs to the batch system.

       launcher : str
            The command used to run jobs

       status_command : str
            The command used to check the queue

       account : str
            The resource account

       submitter_flags : dict 
            Contains keys used to configure the ``submitter``. Values of type
            ``str``, ``int``, ``float`` are then put to ``str`` in the form:
            ``key=value``. Values of the type ``bool`` have their value removed
            and simply pass the key to the submitter_flags string which
            appended after the submitter command.

       launcher_flags : dict
            As ``submitter_flags``, but is sent to the ``launcher`` command.
       """
       self.submitter = None
       self.launcher = None
       self.status_command = None
       self.account = None
       self.submitter_flags = {}
       self.launcher_flags = {}

       try:
           if host is None:
               host = Host()
           assert isinstance(host, Host)
           self._host = host
       except AssertionError:
           raise TypeError("You gave %s. You must give a host object of type %s", host, Host)

    def check_full_queue(self):
        """ Checks the computing queue for this BatchSystem including **all** users """
        raise NotImplementedError("This method, check_full_queue, has not be implemented in the subclass!")

    def check_my_queue(self):
        """ Checks the computing queue for this BatchSystem including **only your** user """
        raise NotImplementedError("This method, check_my_queue, has not be implemented in the subclass!")

    def construct_submitter_flags(self):
        """ Constructs appropriate submitter flags for this BatchSystem """
        raise NotImplementedError("This method, construct_submitter_flags, has not be implemented in the subclass!")
