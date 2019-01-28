import logging
import mock
import os
import socket
import subprocess
import sys
import unittest

from pyesm.compute_hosts import Host
from pyesm.batch_systems import BatchSystem
from pyesm.batch_systems.slurm import Slurm


display_logging = False

if display_logging:
    logger = logging.getLogger()
    logger.level = logging.DEBUG
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)

class test_BatchSystem(unittest.TestCase):
    def test_BatchSystem_init(self):
        """ Check if a BatchSystem object can be correctly initialized """
        with mock.patch("socket.gethostname", return_value="ollie"):
            test_batch = BatchSystem()

    def test_BatchSystem_bad_init(self):
        """ Check if errors are raised at incorrect initialization """
        self.assertRaises(TypeError, BatchSystem, host="lala")

    def test_BatchSystem_not_implemented(self):
        """ Check if errors are raised at not implemented methods for the base class """
        with mock.patch("socket.gethostname", return_value="ollie"):
            test_batch = BatchSystem(host=Host())
        for method in ["check_full_queue", "check_my_queue", "construct_submitter_flags"]:
            this_method = getattr(test_batch, method)
            self.assertRaises(NotImplementedError, this_method)

class test_Slurm(unittest.TestCase):
    def test_Slurm_init(self):
        """ Check if Slurm can be correctly initialized """
        with mock.patch("socket.gethostname", return_value="ollie"):
            test_batch = Slurm(host=Host(), account="pgierz")
    
    def test_Slurm_check_queue(self):
        """ Checks if the staticmethods for queue checking return strings """
        old_call = subprocess.check_output
        def mocked_call(*a, **kw):
            return "mocked"
        subprocess.check_output = mocked_call
        self.assertEqual(Slurm.check_full_queue(), "mocked")
        self.assertEqual(Slurm.check_my_queue(), "mocked")
        subprocess.check_output = old_call

    def test_Slurm_submitter_flags(self):
        """ Checks if submitter flags are correctly assembled """
        with mock.patch("socket.gethostname", return_value="ollie"):
            test_batch = Slurm(host=Host(), account="pgierz")
        submitter_flag_args = {
                            "job_flag": "compute",
                            "job_time": "03:00:00",
                            "job_ntasks": "720",
                            "job_name": "test_exp",
                            "job_logfile": "out.$$",
                            "job_mailtype": "FAIL",
                            "exclusive": True
                            }
        submitter_flags = test_batch.construct_submitter_flags(**submitter_flag_args)
        expected_str = ["--output=out.$$", "--error=out.$$", "--partition=mpp", "--job-name=test_exp", "--exclusive", "--account=pgierz",
                        "--mail-type=FAIL", "--time=03:00:00", "--ntasks=720"]

        self.assertEqual(set(submitter_flags.split()), set(expected_str))

    def test_Slurm_construct_submit_command(self):
        """ Checks if submit command is correct assembled """
        with mock.patch("socket.gethostname", return_value="ollie"):
            test_batch = Slurm(host=Host(), account="pgierz")
        submitter_flag_args = {
                            "job_flag": "compute",
                            "job_time": "03:00:00",
                            "job_ntasks": "720",
                            "job_name": "test_exp",
                            "job_logfile": "out.$$",
                            "job_mailtype": "FAIL",
                            "exclusive": True
                            }
        submit_command = test_batch.construct_submit_command(**submitter_flag_args)
        expected_str = "sbatch --output=out.$$ --error=out.$$ --partition=mpp --job-name=test_exp --exclusive --account=pgierz --mail-type=FAIL --time=03:00:00 --ntasks=720" 
        self.assertEqual(set(submit_command.split()), set(expected_str.split()))

    def test_Slurm_construct_execution_command(self):
        """ Checks if execution command is correct assembled """
        with mock.patch("socket.gethostname", return_value="ollie"):
            test_batch = Slurm(host=Host(), account="pgierz")
        exec_list = ["echam6", "fesom"]
        exec_tasks = [240, 480]
        total_tasks = 720
        execution_command = test_batch.construct_execution_command(total_tasks, exec_list, exec_tasks) 
        print(execution_command)
        os.remove("hostfile_srun")

if __name__ == "__main__":
    stream_handler.stream = sys.stdout
    unittest.main()
