####################################################################################################
#
# filewalker — ...
# Copyright (C) 2020 Fabrice Salvaire
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
####################################################################################################

__all__ = ['DuplicateFinder']

####################################################################################################

from operator import attrgetter
from pathlib import Path
from typing import AnyStr, Type, Union
import logging

from filewalker.path.file import File
from filewalker.path.walker import WalkerAbc
from .DuplicateSet import DuplicateSet, DuplicateSetIt, DuplicatePool

####################################################################################################

_module_logger = logging.getLogger(__name__)

####################################################################################################

class DuplicateFinder(WalkerAbc):

    """
    Find duplicate

    Algorithm:
    - sort files by size
    - eliminate singleton
    - eliminate candidates based on first bytes
    - eliminate candidates based on last bytes
    - eliminate candidates based on sha1
    """

    _logger = _module_logger.getChild('DuplicateFinder')

    ##############################################

    # Fixme: cleaner

    @classmethod
    def find_duplicate(
            cls,
            path: Union[AnyStr, Path],
            fast_io: bool = False,
    ) -> Type['Cleaner']:
        obj = cls(path)
        print(f'Now scanning "{obj.path}"')
        obj.run(top_down=False, sort=False, follow_links=False)

        obj.make_size_map()

        #! p = ""
        #! print("Check: ", obj.has_path(p))

        old_file_count = obj.count()
        print(f"Now have {old_file_count} files in total.")
        # Total size is xxx bytes or xxx GiB

        def report(old_file_count):
            file_count = obj.count()
            print(f"removed {old_file_count - file_count} files from list. {file_count} files left.")
            return file_count

        obj.remove_unique_size()
        file_count = obj.count()
        print(f"Removed {old_file_count - file_count} files due to unique sizes from list. {file_count} files left.")
        old_file_count = file_count

        # Fixme: ok ??? same size, same first bytes but followings...
        print("Now eliminating candidates based on first bytes:")
        obj.remove_different_first_byte(fast_io)
        old_file_count = report(old_file_count)

        print("Now eliminating candidates based on last bytes:")
        obj.remove_different_last_byte(fast_io)
        old_file_count = report(old_file_count)

        print("Now eliminating candidates based on sha1 checksum:")
        obj.remove_different_sha(fast_io)
        old_file_count = report(old_file_count)

        print(f"It seems like you have {old_file_count} files that are not unique")
        # Totally, 822 MiB can be reduced.

        return obj

    ##############################################

    @classmethod
    def find_duplicate_set(
            cls,
            path: Union[AnyStr, Path],
            fast_io: bool = False,
    ) -> DuplicatePool:
        obj = cls.find_duplicate(path, fast_io)
        return DuplicatePool(it=obj.duplicate_iter())

    ##############################################

    def __init__(self, path: Union[AnyStr, Path]) -> None:
        super().__init__(path)
        self._files = []   # : [File]
        self._pool = None   # : [[File]] grouped by size

    ##############################################

    def on_filename(self, dirpath: bytes, path: bytes) -> None:
        file_obj = File(dirpath, path)
        if self.register_file(file_obj):
            self._files.append(file_obj)

    ##############################################

    def register_file(self, file_obj: File) -> bool:
        return (
            not file_obj.is_symlink
            and not file_obj.is_empty
        )

    ##############################################

    # def __len__(self) -> int:
    #     return len(self._files)

    # def __iter__(self) -> Iterator[File]:
    #     return iter(self._files)

    def duplicate_iter(self) -> DuplicateSetIt:
        return iter([DuplicateSet(_) for _ in self._pool])

    ##############################################

    def sort_file_by_size(self) -> None:
        self._files.sort(key=attrgetter('size'))

    ##############################################

    def sort_file_by_inode(self) -> None:
        self._files.sort(key=lambda file_obj: (file_obj.device << 64) + file_obj.inode)

    ##############################################

    def make_size_map(self) -> None:
        size_map = {}
        for file_obj in self._files:
            size_map.setdefault(file_obj.size, [])
            size_map[file_obj.size].append(file_obj)
        self._pool = size_map.values()
        self._files = None

    ##############################################

    def join(self) -> None:
        # used by .feature_fast_io
        files = []
        for file_objs in self._pool:
            files += file_objs
        self._files = files

    ##############################################

    def count(self) -> int:
        count = 0
        for file_objs in self._pool:
            # Fixme: len is ambiguous
            count += len(file_objs)
        return count

    ##############################################

    def remove_unique_size(self) -> int:
        new_pool = []
        remove_count = 0
        for file_objs in self._pool:
            if len(file_objs) > 1:
                new_pool.append(file_objs)
            else:
                remove_count += 1
        self._pool = new_pool
        return remove_count

    ##############################################

    def remove_nonunique_inode(self) -> int:
        raise NotImplementedError

    ##############################################

    def feature_fast_io(self, method) -> None:
        """Sort files on disk and load feature in memory"""
        self.join()
        self.sort_file_by_inode()
        for file_obj in self._files:
            file_obj.user_data = method(file_obj)
        self._files = None

    ##############################################

    def clean_user_data(self, method) -> None:
        for file_obj in self._files:
            file_obj.user_data = None

    ##############################################

    def _remove_different_feature_impl(self, method) -> int:
        new_pool = []
        remove_count = 0
        for file_objs in self._pool:
            # We split the file set to uniq feature sets and remove singletons
            features = [method(_) for _ in file_objs]
            unique_features = tuple(set(features))
            # Fixme: perf ! feature is hashed x4
            #   some bytes test => 64-bytes
            #   use a feature hash to speedup ???
            counts = {_: features.count(_) for _ in unique_features}
            pool = {_: [] for _ in unique_features}
            for file_obj, feature in zip(file_objs, features):
                if counts[feature] > 1:
                    pool[feature].append(file_obj)
                else:
                    remove_count += 1
            for _ in pool.values():
                if _:
                    new_pool.append(_)
        self._pool = new_pool
        return remove_count

    ##############################################

    def remove_different_feature(self, method, fast_io: bool = False) -> int:
        if fast_io:
            self.feature_fast_io(method)
            return self._remove_different_feature_impl(lambda file_obj: file_obj.user_data)
        else:
            return self._remove_different_feature_impl(method)

    ##############################################

    def remove_different_first_byte(self, fast_io: bool = False) -> int:
        return self.remove_different_feature(File.first_bytes, fast_io)

    def remove_different_last_byte(self, fast_io: bool = False) -> int:
        return self.remove_different_feature(File.last_bytes, fast_io)

    def remove_different_sha(self, fast_io: bool = False) -> int:
        return self.remove_different_feature(lambda file_obj: file_obj.sha, fast_io)

    ##############################################

    def has_path(self, path: str) -> bool:
        for file_objs in self._pool:
            if path in [_.path_str for _ in file_objs]:
                return True
        return False
