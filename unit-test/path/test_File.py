####################################################################################################
#
# filewalker -
# Copyright (C) 2020 Fabrice Salvaire
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
####################################################################################################

####################################################################################################

from pathlib import Path
import os
import tempfile
import unittest
from unittest import skip

####################################################################################################

from filewalker.path.file import *

####################################################################################################

class TemporaryDirectory:

    ##############################################

    def __init__(self, *args, **kwargs):
        self._tmp_directory = tempfile.TemporaryDirectory()
        print('Created temporary directory', self._tmp_directory.name)
        self._chdir = kwargs.get('chdir', False)

    ##############################################

    def __enter__(self):
        path = self._tmp_directory.name
        if self._chdir:
            os.chdir(path)
        return TemporaryDirectoryWrapper(path)

    ##############################################

    def __exit__(self, exc_type, exc_value, traceback):
        self._tmp_directory.cleanup()

####################################################################################################

class TemporaryDirectoryWrapper:

    ##############################################

    def __init__(self, path: str):
        self._path = Path(path)

    ##############################################

    def joinpath(self, filename: str):
        return self._path.joinpath(filename)

    ##############################################

    def make_file(self, filename: str, content: str = ""):
        path = self.joinpath(filename)
        print(f"{path}")
        with open(path, 'w') as fh:
            fh.write(content)
        return File.from_path(path), path

####################################################################################################

class TestFile(unittest.TestCase):

    ##############################################

    def test_ctor(self):

        filename = "test.txt"
        content = "hello" * 100
        sha1sum = "a6fbdf72b1c923162bc17158b51bfb154fd900b2"

        with TemporaryDirectory() as directory:
            file_obj, path = directory.make_file(filename, content)
            # print(file_obj.sha)
            # input()
            self.assertEqual(str(file_obj.path), str(path))
            self.assertEqual(file_obj.sha, sha1sum)
            self.assertEqual(file_obj.size, len(content))

    ##############################################

    def test_rename(self):
        with TemporaryDirectory() as directory:
            filename = "test.txt"
            file_obj, path = directory.make_file(filename)
            dst_path = directory.joinpath("test-2.txt")
            effective_dst_path = file_obj.rename(dst_path)
            self.assertEqual(effective_dst_path, directory.joinpath(f"test-2.txt"))
            for i in range(1, 3):
                file_obj, path = directory.make_file(filename)
                effective_dst_path = file_obj.rename(dst_path)
                self.assertEqual(effective_dst_path, directory.joinpath(f"test-2 ({i}).txt"))
            file_obj, path = directory.make_file("test-2 (4).txt")
            effective_dst_path = file_obj.rename(dst_path)
            self.assertEqual(effective_dst_path, directory.joinpath(f"test-2 (3).txt"))
            # with self.assertRaises():
            self.assertIsNone(file_obj.rename(file_obj.path))

####################################################################################################

if __name__ == '__main__':
    unittest.main()
