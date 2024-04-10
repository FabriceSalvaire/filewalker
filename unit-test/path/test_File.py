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

import unittest
# from unittest import skip

####################################################################################################

from filewalker.path.file import File
from filewalker.unit_test.file import TemporaryDirectory, make_content1, make_content2

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

            # rename to self
            self.assertIsNone(file_obj.rename(file_obj.path))

            with self.assertRaises(FileNotFoundError):
                file_obj.rename(directory.joinpath('nowhere/foo.txt'))

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

    ##############################################

    def test_equal(self):
        with TemporaryDirectory() as directory:
            content1 = make_content1(987)
            content2 = make_content2(541)
            print(f"content1 {content1[:100]}")
            print(f"content2 {content2[:100]}")
            file1, path1 = directory.make_file('file1', content1)
            file2, path2 = directory.make_file('file2', content2)
            dupfile, dupfile_path = directory.make_file('dupfile1', content1)
            self.assertNotEqual(file1.sha, file2.sha)
            self.assertEqual(file1.sha, dupfile.sha)
            for posix in (True, False):
                self.assertFalse(file1.compare_with(file2, posix=posix))
                self.assertTrue(file1.compare_with(dupfile, posix=posix))

####################################################################################################

if __name__ == '__main__':
    unittest.main()
