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

####################################################################################################

from filewalker.path.file import File
from filewalker.cleaner.DuplicateCleaner import (
    DuplicateSet,
    NonUniqFiles, AllFileMarked, InconsistentDuplicateSet,
)
from filewalker.unit_test.file import TemporaryDirectory, make_content1, make_content2

####################################################################################################

class TestDuplicateSet(unittest.TestCase):

    ##############################################

    def test_ctor(self):
        paths = (
            '/foo/bar/a',
            '/foo/bar/a',
            '/foo/a',
        )
        with self.assertRaises(NonUniqFiles):
            duplicate_set = DuplicateSet([File.from_str(_) for _ in paths])

    ##############################################

    def test_mark(self):
        paths = (
            '/foo/bar/a',
            '/foo/a',
            '/foo/b',
            '/foo/bar/b',
        )

        duplicate_set = DuplicateSet([File.from_str(_) for _ in paths])
        self.assertEqual(duplicate_set.number_of_unmarked, len(paths))
        self.assertEqual(duplicate_set.number_of_marked, 0)

        # unchanged
        duplicate_set.commit()
        duplicate_set.check()

        for _ in duplicate_set:
            _.mark()
        self.assertEqual(duplicate_set.number_of_unmarked, 0)
        self.assertEqual(duplicate_set.number_of_marked, len(paths))
        with self.assertRaises(AllFileMarked):
            duplicate_set.commit()
        duplicate_set.check()

        duplicate_set.rollback()
        self.assertEqual(duplicate_set.number_of_unmarked, len(paths))
        self.assertEqual(duplicate_set.number_of_marked, 0)
        duplicate_set.check()

        for _ in duplicate_set.followings:
            _.mark()
        self.assertEqual(duplicate_set.number_of_unmarked, 1)
        self.assertEqual(duplicate_set.number_of_marked, len(paths) -1)
        duplicate_set.commit()
        self.assertEqual(duplicate_set.number_of_marked, 0)
        self.assertEqual(duplicate_set.number_of_duplicates, len(paths) -1)
        duplicate_set.check()

        self.assertListEqual([_.path_str for _ in duplicate_set], list(paths[:1]))
        self.assertListEqual([_.path_str for _ in duplicate_set.duplicates], list(paths[1:]))

        # make invalid duplicate_set
        # alter pendings
        obj = duplicate_set._pendings.pop()
        with self.assertRaises(InconsistentDuplicateSet):
            duplicate_set.check()
        duplicate_set._pendings.append(obj)
        # alter duplicates
        obj = duplicate_set._duplicates.pop()
        with self.assertRaises(InconsistentDuplicateSet):
            duplicate_set.check()
        duplicate_set._duplicates.append(obj)
        # alter path
        first = duplicate_set.first.file
        name = first._name
        first._name = b'...'
        with self.assertRaises(InconsistentDuplicateSet):
            duplicate_set.check()
        first._name = name
        duplicate_set.check()
        duplicate_set = None

    ##############################################

    def test_is_duplicate(self):
        with TemporaryDirectory() as directory:
            content1 = make_content1(987)
            content2 = make_content2(541)
            print(f"content1 {content1[:100]}")
            print(f"content2 {content2[:100]}")
            file1, path1 = directory.make_file('file1', content1)
            file2, path2 = directory.make_file('file2', content2)
            dupfile, dupfile_path = directory.make_file('dupfile1', content1)
            _ = DuplicateSet((file1, dupfile))
            self.assertTrue(_.check_is_duplicate())
            _ = DuplicateSet((file1, file2, dupfile))
            self.assertFalse(_.check_is_duplicate())

####################################################################################################

if __name__ == '__main__':
    unittest.main()
