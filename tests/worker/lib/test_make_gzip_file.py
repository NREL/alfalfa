from unittest import TestCase

from alfalfa_worker.lib.make_gzip_file import make_gzip_file

import os


class TestHttpRequests(TestCase):
    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.output_dir = os.path.join(os.path.dirname(__file__), 'output')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def test_make_gzip(self):
        file_outname = 'a-file'
        if os.path.exists(os.path.join(self.output_dir, f'{file_outname}.tar.gz')):
            os.remove(os.path.join(self.output_dir, f'{file_outname}.tar.gz'))

        current_dir = os.getcwd()
        try:
            os.chdir(self.output_dir)
            make_gzip_file(file_outname, self.data_dir)
        finally:
            os.chdir(current_dir)

        self.assertTrue(os.path.exists(os.path.join(self.output_dir, f'{file_outname}.tar.gz')))
