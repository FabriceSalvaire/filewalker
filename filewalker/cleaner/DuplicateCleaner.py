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

__all__= [
    'AllFileMarked',
    'Duplicate',
    'DuplicateCleaner',
    'DuplicatePool',
    'DuplicateSet',
    'InconsistentDuplicateSet',
    'NonUniqFiles',
]

####################################################################################################

from operator import attrgetter
from pathlib import Path
from typing import AnyStr, Iterator, List, Set, Type, Union
import json
import logging

from filewalker.path.file import File
from filewalker.path.walker import WalkerAbc

####################################################################################################

_module_logger = logging.getLogger(__name__)

####################################################################################################

class MarkMixin:

    ##############################################

    def __init__(self) -> None:
        self._marked = False

    ##############################################

    def __bool__(self) -> bool:
        return self._marked

    @property
    def marked(self) -> bool:
        return self._marked

    def mark(self) -> None:
        self._logger.debug(f"Mark {self}")
        self._marked = True

    def unmark(self) -> None:
        self._marked = False

####################################################################################################

class Duplicate(MarkMixin):

    _logger = _module_logger.getChild("Duplicate")

    ##############################################

    def __init__(self, file_obj: File) -> None:
        super().__init__()
        self._file = file_obj
        self._path = self._file.path   # Fixme: ???

    ##############################################

    def __str__(self):
        # return str(self.path_bytes)
        return str(self.path_str)

    def __repr__(self):
        return str(self)

    ##############################################

    @property
    def path_bytes(self) -> bytes:
        return self._file.path_bytes

    @property
    def path_str(self) -> str:
        return self._file.path_str

    @property
    def path(self) -> Path:
        return self._path

    @property
    def exists(self) -> bool:
        return self._path.exists()

    @property
    def file(self) -> File:
        return self._file

    ##############################################

    def compare_with(self, other: Type["Duplicate"], posix: bool = False) -> bool:
        return self.file.compare_with(other.file, posix)

    ##############################################

    def delete(self, dry_run: bool = False) -> None:
        self._logger.info(f"Delete file {self.path}")
        # if not dry_run:
        #     self.path.unlink()

    ##############################################

    def link_to(self, to: Type["Duplicate"], dry_run: bool = False) -> None:
        self._logger.info(f"link file {self.path} to {to.path}")
        # if not dry_run:
        #     self.path.unlink()
        #     self.path.link_to(to.path)

    ##############################################

    def symlink_to(self, to: Type["Duplicate"],  dry_run: bool = False, ) -> None:
        self._logger.info(f"link file {self.path} to {to.path}")
        # if not dry_run:
        #     self.path.unlink()
        #     self.path.symlink_to(to.path)

####################################################################################################

class NonUniqFiles(ValueError):
    pass

class AllFileMarked(ValueError):
    pass

class InconsistentDuplicateSet(ValueError):
    pass

####################################################################################################

class DuplicateSet(MarkMixin):

    _logger = _module_logger.getChild("DuplicateSet")

    ##############################################

    def __init__(self, files: List[File]) -> None:
        super().__init__()
        # Check there is any duplicate file in the list
        if len(files) < 2:
            raise ValueError("Require more than one file")
        paths = [_.path_bytes for _ in files]
        self._input_paths = set(paths)
        if len(self._input_paths) != len(files):
            raise NonUniqFiles(f"Non-unique list of files: {paths}")
        self._pendings = [Duplicate(_) for _ in files]
        self._duplicates = []

    ##############################################

    def __str__(self) -> str:
        return str([str(_) for _ in self.paths])

    ##############################################

    def __len__(self) -> int:
        return len(self._pendings)

    @property
    def is_singleton(self) -> bool:
        return len(self._pendings) == 1

    @property
    def number_of_duplicates(self) -> int:
        return len(self._duplicates)

    ##############################################

    def __iter__(self) -> Iterator[Duplicate]:
        return iter(self._pendings)

    def __getitem__(self, _slice) -> Duplicate:
        return self._pendings[_slice]

    @property
    def first(self) -> Duplicate:
        return self._pendings[0]

    @property
    def second(self) -> Duplicate:
        return self._pendings[1]

    @property
    def followings(self) -> Iterator[Duplicate]:
        return iter(self._pendings[1:])

    @property
    def duplicates(self) -> Iterator[Duplicate]:
        return iter(self._duplicates)

    ##############################################

    @property
    def marked(self) -> List[File]:
        return [_ for _ in self if _]

    @property
    def unmarked(self) -> List[File]:
        return [_ for _ in self if not _]

    @property
    def number_of_marked(self) -> int:
        return sum([1 for _ in self if _])

    @property
    def number_of_unmarked(self) -> int:
        return sum([1 for _ in self if not _])

    ##############################################

    @property
    def paths_bytes(self) -> List[bytes]:
        return [_.path_bytes for _ in self]

    @property
    def paths_str(self) -> List[str]:
        return [_.path_str for _ in self]

    @property
    def paths(self) -> List[Path]:
        return [_.path for _ in self]

    @property
    def duplicated_paths(self) -> List[Path]:
        return [_.path for _ in self._duplicates]

    ##############################################

    def sort(self, key=None, reverse: bool = False) -> None:
        if key is None:
            key = lambda duplicate: duplicate.path_bytes
        self._pendings.sort(key=key, reverse=reverse)

    ##############################################

    @property
    def is_same_parent(self) -> bool:
        parents = set([str(_.parent) for _ in self.paths])
        return len(parents) == 1

    @property
    def common_parent(self) -> bool:
        parents = [_.parent.parts for _ in self.paths]
        parts = []
        i = 0
        try:
            while True:
                part = parents[0][i]
                for _ in parents[1:]:
                    if part != _[i]:
                        raise IndexError
                parts.append(part)
                i += 1
        except IndexError:
            pass
        return Path(*parts)

    ##############################################

    def commit(self) -> None:
        if self.number_of_marked:
            if not self.number_of_unmarked:
                raise AllFileMarked(f"All files are marked in duplicate set {self.paths_bytes}")
            self._duplicates.extend(self.marked)
            for _ in self.marked:
                self._pendings.remove(_)

    ##############################################

    def rollback(self, rollback_duplicates: bool = False) -> None:
        if rollback_duplicates:
            self._pendings += self._duplicates
            self._duplicates = []
        for _ in self._pendings:
            _.unmark()

    ##############################################

    def check(self) -> None:
        if not self._pendings:
            raise InconsistentDuplicateSet(f"pendings is empty")
        pendings = [_.path_bytes for _ in self._pendings]
        duplicates = [_.path_bytes for _ in self._duplicates]
        paths = set(pendings) | set(duplicates)
        if paths != self._input_paths:
            raise InconsistentDuplicateSet(f"Inconsistent duplicate set: {paths} != {self._input_paths}")

    ##############################################

    def delete_duplicates(self, dry_run: bool = False) -> None:
        self.check()
        for _ in self._duplicates:
            _.delete(dry_run)

####################################################################################################

class DuplicatePool:

    _logger = _module_logger.getChild("DuplicatePool")

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
        self._pool.sort(key=lambda duplicate_set: duplicate_set.first.path_bytes)

    ##############################################

    def sanity_check(self) -> bool:
        paths = {}
        for duplicate_set in self:
            for _ in duplicate_set:
                path = _.path
                paths.setdefault(path, 0)
                paths[path] += 1
        good = True
        for path, count in paths.items():
            if path.exists():
                if count > 1:
                    self._logger.error(f"{path} is duplicated {count} times")
                    good = False
                if path.is_symlink():
                    self._logger.error(f"{path} is a symlink")
                    good = False
                # number of hard links
                if path.stat().st_nlink > 1:
                    self._logger.warning(f"{path} as more than one hark links")
            else:
                self._logger.error(f"{path} doesn't exists")
                good = False
        return good

    ##############################################

    def remove_singleton(self) -> None:
        self._pool = [_ for _ in self if not _.is_singleton]

    ##############################################

    def to_json(self, exclude_singleton: bool = True) -> str:
        if exclude_singleton:
            data = [_.paths_str for _ in self if not _.is_singleton]
        else:
            data = [_.paths_str for _ in self]
        return json.dumps(data, indent=4)

    ##############################################

    def write_json(self, path: Union[AnyStr, Path], exclude_singleton: bool = True) -> None:
        with open(path, 'w', encoding="utf-8") as fh:
            fh.write(self.to_json(exclude_singleton))

    ##############################################

    def __eq__(self, other: Type['DuplicatePool']):
        self.sort()
        other.sort()
        if len(self) != len(other):
            return False
        for a, b in zip(self, other):
            if a.paths_bytes != b.paths_bytes:
                return False
        return True

    ##############################################

    def to_set(self) -> Set[bytes]:
        path_set = set()
        for _ in self:
            path_set |= set(_.paths_bytes)
        return path_set

    ##############################################

    def compare(self, ref: Type['DuplicatePool']):
        my_set = self.to_set()
        ref_set = ref.to_set()
        return ref_set - my_set # , my_set - ref_set

####################################################################################################

class DuplicateCleaner(WalkerAbc):

    _logger = _module_logger.getChild("DuplicateCleaner")

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

        # p = ""
        # print("Check: ", walker.has_path(p))

        old_file_count = walker.count()
        print(f"Now have {old_file_count} files in total.")
        # Total size is xxx bytes or xxx GiB

        def report(old_file_count):
            file_count = walker.count()
            print(f"removed {old_file_count - file_count} files from list. {file_count} files left.")
            return file_count

        walker.remove_unique_size()
        file_count = walker.count()
        print(f"Removed {old_file_count - file_count} files due to unique sizes from list. {file_count} files left.")
        old_file_count = file_count
        print("Check: ", walker.has_path(p))

        print("Now eliminating candidates based on first bytes:")
        walker.remove_different_first_byte(fast_io)
        old_file_count = report(old_file_count)
        print("Check: ", walker.has_path(p))

        print("Now eliminating candidates based on last bytes:")
        walker.remove_different_last_byte(fast_io)
        old_file_count = report(old_file_count)
        print("Check: ", walker.has_path(p))

        print("Now eliminating candidates based on sha1 checksum:")
        walker.remove_different_sha(fast_io)
        old_file_count = report(old_file_count)
        print("Check: ", walker.has_path(p))

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
        self._pool = None

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
        files = []
        for file_objs in self._pool:
            files += file_objs
        self._files = files

    ##############################################

    def count(self) -> int:
        count = 0
        for file_objs in self._pool:
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
