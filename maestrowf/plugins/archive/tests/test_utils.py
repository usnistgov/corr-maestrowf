import unittest
import os
from maestrowf.interfaces.archive import utils

class TestUtils(unittest.TestCase):

    def test_get_file_path(self):
        file_path = 'tests/corr-test.yaml'
        self.assertEqual(os.path.abspath(file_path), utils.get_file_path(file_path))
