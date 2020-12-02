####################################################################################################
#
# FileSystemTool — ...
# Copyright (C) 2020 Fabrice Salvaire
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
####################################################################################################

####################################################################################################

from operator import attrgetter
from pathlib import Path
from typing import AnyStr, Iterator, Union, Type

from FileSystemTool.path.file import File
from FileSystemTool.path.walker import WalkerAbc

####################################################################################################

class DuplicateCleaner(WalkerAbc):

    ##############################################

    @classmethod
    def clean(
            cls,
            path: Union[AnyStr, Path],
            fast_io: bool = False,
    ) -> Type['Cleaner']:
        walker = cls(path)
        walker.run(topdown=False, sort=False, followlinks=False)
        walker.make_size_map()
        walker.remove_uniq_size()
        walker.remove_different_first_byte(fast_io)
        walker.remove_different_last_byte(fast_io)
        walker.remove_different_sha(fast_io)
        walker.join()
        return walker

    ##############################################

    def __init__(self, path: Union[AnyStr, Path]) -> None:
        super().__init__(path)
        self._files = []
        self._size_map = None

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

    def __len__(self) -> int:
        return len(self._files)

    def __iter__(self) -> Iterator[File]:
        return iter(self._files)

    ##############################################

    def sort_file_by_size(self) -> None:
        self._files.sort(key=attrgetter('size'))

    ##############################################

    def sort_file_by_inode(self) -> None:
        self._files.sort(key=lambda file_obj: (file_obj.device << 64) + file_obj.inode)

    ##############################################

    def make_size_map(self) -> None:
        size_map = {}
        for file_obj in self:
            size_map.setdefault(file_obj.size, [])
            size_map[file_obj.size].append(file_obj)
        self._size_map = size_map
        self._files = None

    ##############################################

    def join(self) -> None:
        files = []
        for file_objs in self._size_map.values():
            files.extend(file_objs)
        self._files = files

    ##############################################

    def remove_uniq_size(self) -> int:
        size_map = self._size_map
        to_remove = []
        for size, file_objs in size_map.items():
            if len(file_objs) == 1:
                to_remove.append(size)
        for size in to_remove:
            del size_map[size]
        return len(to_remove)

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
        remove_count = 0
        size_to_remove = []
        for size, file_objs in self._size_map.items():
            to_remove = []
            feature = method(file_objs[0])
            for i, file_obj in enumerate(file_objs[1:]):
                if method(file_obj) != feature:
                    to_remove.append(i)
            if len(to_remove) == len(file_objs) -1:
                size_to_remove.append(size)
                remove_count += len(file_objs)
            elif to_remove:
                remove_count += len(to_remove)
                for i in to_remove:
                    del file_objs[i]
        size_map = self._size_map
        for size in size_to_remove:
            del size_map[size]
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
