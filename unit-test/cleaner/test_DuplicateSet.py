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
from filewalker.cleaner.DuplicateSet import (
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
            dset = DuplicateSet([File.from_str(_) for _ in paths])

    ##############################################

    def test_mark(self):
        paths = (
            '/foo/bar/a',
            '/foo/a',
            '/foo/b',
            '/foo/bar/b',
        )

        print()

        # Initial tests
        dset = DuplicateSet([File.from_str(_) for _ in paths])
        self.assertEqual(dset.number_of_unmarked, len(paths))
        self.assertEqual(dset.number_of_marked, 0)

        # unchanged
        dset.commit()
        dset.check()

        # Mark all files
        for _ in dset:
            _.mark()
        self.assertEqual(dset.number_of_unmarked, 0)
        self.assertEqual(dset.number_of_marked, len(paths))
        with self.assertRaises(AllFileMarked):
            dset.commit()
        # commit aborded
        self.assertEqual(dset.number_of_duplicates, 0)
        self.assertEqual(dset.number_of_pendings, dset.number_of_files)
        dset.check()

        # Test rollback
        dset.rollback()
        self.assertEqual(dset.number_of_unmarked, len(paths))
        self.assertEqual(dset.number_of_marked, 0)
        dset.check()

        # Mark all files excepted the first one
        for _ in dset.followings:
            _.mark()
        self.assertEqual(dset.number_of_unmarked, 1)
        self.assertEqual(dset.number_of_marked, len(paths) -1)
        dset.commit()
        self.assertEqual(dset.number_of_marked, 0)
        self.assertEqual(dset.number_of_duplicates, len(paths) -1)
        dset.check()

        self.assertListEqual([_.path_str for _ in dset.pendings], list(paths[:1]))
        self.assertListEqual([_.path_str for _ in dset.duplicates], list(paths[1:]))

        # make invalid dset
        # alter pendings (pop)
        obj = dset._pendings.pop()
        with self.assertRaises(InconsistentDuplicateSet) as cm:
            dset.check()
        print(cm.exception)
        dset._pendings.append(obj)
        # alter duplicates (pop)
        obj = dset._duplicates.pop()
        with self.assertRaises(InconsistentDuplicateSet) as cm:
            dset.check()
        print(cm.exception)
        dset._duplicates.append(obj)
        # alter duplicates (add pendings)
        duplicates = list(dset._duplicates)
        dset._duplicates += dset.pendings
        with self.assertRaises(InconsistentDuplicateSet) as cm:
            dset.check()
        print(cm.exception)
        dset._duplicates = duplicates
        # alter path of first
        first = dset.first.file
        name = first._name
        first._name = b'...'
        with self.assertRaises(InconsistentDuplicateSet) as cm:
            dset.check()
        print(cm.exception)
        first._name = name
        # recheck restored
        dset.check()

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
