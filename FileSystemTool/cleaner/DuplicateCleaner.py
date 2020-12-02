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
from typing import AnyStr, Iterator, List, Union, Type
import json

from FileSystemTool.path.file import File
from FileSystemTool.path.walker import WalkerAbc

####################################################################################################

class Duplicate:

    ##############################################

    def __init__(self, file_obj: File) -> None:
        self._file = file_obj
        self._marked = False

    ##############################################

    @property
    def path(self) -> File:
        return self._file.absolut_path_bytes

    @property
    def path_str(self) -> File:
        return self._file.absolut_path_str

    @property
    def file(self) -> File:
        return self._file

    @property
    def marked(self) -> bool:
        return self._marked

    def __bool__(self) -> bool:
        return self._marked

    def mark(self) -> None:
        self._marked = True

####################################################################################################

class DuplicateSet:

    ##############################################

    def __init__(self, files: List[File]) -> None:
        self._files = [Duplicate(_) for _ in files]

    ##############################################

    def __len__(self) -> int:
        return len(self._files)

    def __iter__(self) -> Iterator[File]:
        return iter(self._files)

    @property
    def first(self) -> File:
        return self._files[0]

    ##############################################

    @property
    def paths(self) -> List[bytes]:
        return [_.path for _ in self]

    @property
    def paths_str(self) -> List[bytes]:
        return [_.path_str for _ in self]

    ##############################################

    def sort(self) -> None:
        self._files.sort(key=lambda duplicate: duplicate.path)

    ##############################################

    def to_be_cleaned(self) -> List[File]:
        duplicate = [_ for _ in self if _]
        if len(duplicate) == len(self):
            raise NameError(f"All files are marked in duplicate set {self.paths}")
        return duplicate

####################################################################################################

class DuplicatePool:

    ##############################################

    @classmethod
    def new_from_json(cls, path: Union[AnyStr, Path]) -> Type['DuplicatePool']:
        with open(path, 'r', encoding="utf-8") as fh:
            data = json.load(fh)
        pool = cls()
        for paths in data:
            pool.add_from_paths(paths)
        return pool

    ##############################################

    @classmethod
    def new_from_paths(cls, paths: List[List[str]]) -> Type['DuplicatePool']:
        pool = cls()
        for paths in paths:
            pool.add_from_paths(paths)
        return pool

    ##############################################

    def __init__(self, it: Iterator[DuplicateSet] = None) -> None:
        self._pool = []
        if it is not None:
            self.fill(it)

    ##############################################

    def fill(self, it: Iterator[DuplicateSet]) -> None:
        self._pool.extend(it)

    def add(self, duplicate: DuplicateSet) -> None:
        self._pool.append(duplicate)

    def add_from_paths(self, paths: List[str]) -> None:
        paths = [File.from_str(_) for _ in paths]
        self.add(DuplicateSet(paths))

    ##############################################

    def __len__(self) -> int:
        return len(self._pool)

    def __iter__(self) -> Iterator[DuplicateSet]:
        return iter(self._pool)

    ##############################################

    def sort(self) -> None:
        for _ in self:
            _.sort()
        self._pool.sort(key=lambda duplicate_set: duplicate_set.first.path)

    ##############################################

    def to_json(self) -> str:
        data = [_.paths_str for _ in self]
        return json.dumps(data)

    ##############################################

    def write_json(self, path: Union[AnyStr, Path]) -> None:
        with open(path, 'w', encoding="utf-8") as fh:
            fh.write(self.to_json())

    ##############################################

    def __eq__(self, other: Type['DuplicatePool']):
        self.sort()
        other.sort()
        if len(self) != len(other):
            return False
        for a, b in zip(self, other):
            if a.paths != b.paths:
                return False
        return True

####################################################################################################

class DuplicateCleaner(WalkerAbc):

    ##############################################

    @classmethod
    def find_duplicate(
            cls,
            path: Union[AnyStr, Path],
            fast_io: bool = False,
    ) -> Type['Cleaner']:
        walker = cls(path)
        print(f'Now scanning "{walker.path}"')
        walker.run(topdown=False, sort=False, followlinks=False)

        walker.make_size_map()

        old_file_count = walker.count()
        print(f"Now have {old_file_count} files in total.")
        # Total size is xxx bytes or xxx GiB

        walker.remove_unique_size()
        file_count = walker.count()
        print(f"Removed {old_file_count - file_count} files due to unique sizes from list. {file_count} files left.")
        old_file_count = file_count

        def report(old_file_count):
            file_count = walker.count()
            print(f"removed {old_file_count - file_count} files from list. {file_count} files left.")
            return file_count

        print("Now eliminating candidates based on first bytes:")
        walker.remove_different_first_byte(fast_io)
        old_file_count = report(old_file_count)

        print("Now eliminating candidates based on last bytes:")
        walker.remove_different_last_byte(fast_io)
        old_file_count = report(old_file_count)

        print("Now eliminating candidates based on sha1 checksum:")
        walker.remove_different_sha(fast_io)
        old_file_count = report(old_file_count)

        print(f"It seems like you have {old_file_count} files that are not unique")
        # Totally, 822 MiB can be reduced.

        return walker

    @classmethod
    def find_duplicate_set(
            cls,
            path: Union[AnyStr, Path],
            fast_io: bool = False,
    ) -> DuplicatePool:
        walker = cls.find_duplicate(path, fast_io)
        return DuplicatePool(it=walker.duplicate_iter())

    ##############################################

    def __init__(self, path: Union[AnyStr, Path]) -> None:
        super().__init__(path)
        self._files = []
        self._map = None

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

    def duplicate_iter(self) -> Iterator[DuplicateSet]:
        return iter([DuplicateSet(_) for _ in self._map.values()])

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
        self._map = size_map
        self._files = None

    ##############################################

    def join(self) -> None:
        files = []
        for file_objs in self._map.values():
            files.extend(file_objs)
        self._files = files

    ##############################################

    def count(self) -> int:
        count = 0
        for file_objs in self._map.values():
            count += len(file_objs)
        return count

    ##############################################

    def remove_unique_size(self) -> int:
        size_map = self._map
        to_remove = []
        for size, file_objs in size_map.items():
            if len(file_objs) == 1:
                to_remove.append(size)
        for size in to_remove:
            del size_map[size]
        return len(to_remove)

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
        remove_count = 0
        size_to_remove = []
        size_map = self._map
        for size, file_objs in size_map.items():
            to_remove = []
            feature = method(file_objs[0])
            for i, file_obj in enumerate(file_objs[1:]):
                if method(file_obj) != feature:
                    to_remove.append(id(file_obj))
            if len(to_remove) == len(file_objs) -1:
                size_to_remove.append(size)
                remove_count += len(file_objs)
            elif to_remove:
                remove_count += len(to_remove)
                # wrong !
                # Fixme: mark obj ? use set ?
                # for i in to_remove:
                #     del file_objs[i]
                size_map[size] = [_ for _ in file_objs if id(_) not in to_remove]
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
