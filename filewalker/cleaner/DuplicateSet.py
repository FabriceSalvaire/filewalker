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

__all__ = [
    'AllFileMarked',
    'Duplicate',
    'DuplicatePool',
    'DuplicateSet',
    'InconsistentDuplicateSet',
    'NonUniqFiles',
]

####################################################################################################

from pathlib import Path
from typing import AnyStr, Iterator, List, Set, Union, Generator
import json
import logging
import os

from filewalker.path.file import File

####################################################################################################

_module_logger = logging.getLogger(__name__)

LINESEP = os.linesep

####################################################################################################

type StrList = list[str]
type ByteList = list[bytes]
type AnyStrList = Union[StrList, ByteList]
type ByteListIt = Generator[ByteList, None, None]   # or Iterator[ByteList]

####################################################################################################

class MarkMixin:

    """Mixin to mark an object."""

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

    """Class to implements a duplicated file."""

    _logger = _module_logger.getChild('Duplicate')

    ##############################################

    def __init__(self, file_obj: File) -> None:
        super().__init__()
        self._file = file_obj
        self._path = self._file.path   # Fixme: ???

    ##############################################

    def __str__(self) -> str:
        # return str(self.path_bytes)
        return str(self.path_str)

    def __repr__(self) -> str:
        return str(self)

    ##############################################

    @property
    def file(self) -> File:
        return self._file

    @property
    def path_bytes(self) -> bytes:
        return self._file.path_bytes

    @property
    def path_str(self) -> str:
        return self._file.path_str

    ##############################################

    @property
    def path(self) -> Path:
        return self._path

    @property
    def parent(self) -> Path:
        return self._path.parent

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def stem(self) -> str:
        return self._path.stem

    @property
    def suffix(self) -> str:
        return self._path.suffix

    @property
    def exists(self) -> bool:
        return self._path.exists()

    ##############################################

    def compare_with(self, other: 'Duplicate', posix: bool = False) -> bool:
        return self.file.compare_with(other.file, posix)

    ##############################################

    def delete(self, dry_run: bool = False) -> None:
        self._logger.info(f"Delete file {self.path}")
        # Fixme: DISABLED
        # if not dry_run:
        #     self.path.unlink()

    ##############################################

    def link_to(self, to: 'Duplicate', dry_run: bool = False) -> None:
        self._logger.info(f"link file {self.path} to {to.path}")
        # Fixme: DISABLED
        # if not dry_run:
        #     self.path.unlink()
        #     self.path.link_to(to.path)

    ##############################################

    def symlink_to(self, to: 'Duplicate', dry_run: bool = False, ) -> None:
        self._logger.info(f"link file {self.path} to {to.path}")
        # Fixme: DISABLED
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

    """Class to implements a set of duplicated files."""

    _logger = _module_logger.getChild('DuplicateSet')

    ##############################################

    @classmethod
    def new_from_str(cls, paths: AnyStrList) -> None:
        paths = [File.from_str(_) for _ in paths]
        return cls(paths)

    ##############################################

    def __init__(self, files: List[File]) -> None:
        super().__init__()

        # Sanity checks
        if len(files) < 2:
            raise ValueError("Require more than one file")
        paths = [_.path_bytes for _ in files]
        self._input_paths = set(paths)
        if len(self._input_paths) != len(files):
            raise NonUniqFiles(f"Non-unique list of files: {paths}")

        # immutable list of input files
        self._files = tuple([Duplicate(_) for _ in files])
        # files to be proceed and finally kept
        self._pendings = list(self._files)
        # duplicated files to be removed
        self._duplicates = []

    ##############################################

    # Fixme: confusing
    def __len__(self) -> int:
        """Return number of files"""
        return len(self._files)

    @property
    def number_of_files(self) -> int:
        """Return number of files"""
        # return len(self._input_paths)
        return len(self._files)

    @property
    def number_of_pendings(self) -> int:
        """Return number of pendings"""
        return len(self._pendings)

    @property
    def number_of_duplicates(self) -> int:
        """Return number of duplicates"""
        return len(self._duplicates)

    @property
    def is_singleton(self) -> bool:
        """Return True if only one pending"""
        return len(self._pendings) == 1

    ##############################################

    # Fixme: confusing
    def __iter__(self) -> Iterator[Duplicate]:
        """Iterate on files"""
        return iter(self._files)

    # Fixme: confusing
    def __getitem__(self, _slice) -> Duplicate:
        """Get file"""
        return self._files[_slice]

    @property
    def pendings(self) -> Iterator[Duplicate]:
        """Iterate on pendings"""
        return iter(self._pendings)

    @property
    def first(self) -> Duplicate:
        """Return first pending"""
        return self._pendings[0]

    @property
    def second(self) -> Duplicate:
        """Return second pending"""
        return self._pendings[1]

    @property
    def followings(self) -> Iterator[Duplicate]:
        """Iterate on pendings after first"""
        return iter(self._pendings[1:])

    @property
    def duplicates(self) -> Iterator[Duplicate]:
        """Iterate on duplicates"""
        return iter(self._duplicates)

    ##############################################

    @property
    def marked(self) -> List[File]:
        """Return list of marked in pendings"""
        return [_ for _ in self._pendings if _]

    @property
    def unmarked(self) -> List[File]:
        """Return list of unmarked in pendings"""
        return [_ for _ in self._pendings if not _]

    @property
    def number_of_marked(self) -> int:
        """Count marked in pendings"""
        return sum([1 for _ in self._pendings if _])

    @property
    def number_of_unmarked(self) -> int:
        """Count unmarked in pendings"""
        return sum([1 for _ in self._pendings if not _])

    ##############################################

    @property
    def paths_bytes(self) -> ByteList:
        return [_.path_bytes for _ in self]

    @property
    def paths_str(self) -> List[str]:
        return [_.path_str for _ in self]

    @property
    def paths(self) -> List[Path]:
        return [_.path for _ in self]

    def __str__(self) -> str:
        return str([str(_) for _ in self.paths])

    @property
    def duplicated_paths(self) -> List[Path]:
        return [_.path for _ in self._duplicates]

    ##############################################

    def sort(self, key=None, reverse: bool = False, sorting: str = None) -> None:
        # Fixme: sort utf-8 bytes ?
        def by_path(_):
            return _.path_bytes

        def by_name_length(_):
            return len(_.name)

        if sorting is not None:
            match sorting:
                case 'path':
                    key = by_path
                case 'name_length':
                    key = by_name_length
                case _:
                    raise ValueError(f"unknow sorting '{sorting}'")
        elif key is None:
            key = by_path
        self._pendings.sort(key=key, reverse=reverse)

    ##############################################

    @property
    def is_same_parent(self) -> bool:
        if not hasattr(self, '_is_same_parent'):
            parents = set([str(_.parent) for _ in self.paths])
            self._is_same_parent = len(parents) == 1
        return self._is_same_parent

    @property
    def common_parent(self) -> Path:
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
        """Move marked files to duplicate list"""
        if self.number_of_marked:
            if not self.number_of_unmarked:
                raise AllFileMarked(f"All files are marked in duplicate set {self.paths_bytes}")
            self._duplicates.extend(self.marked)
            for _ in self.marked:
                self._pendings.remove(_)

    ##############################################

    def rollback(self, rollback_duplicates: bool = False) -> None:
        """
        - if *rollback_duplicates* move duplicates in pending mist
        - unmark pendings
        """
        # Fixme: API ???
        if rollback_duplicates:
            self._pendings += self._duplicates
            self._duplicates = []
        for _ in self._pendings:
            _.unmark()

    ##############################################

    def check(self) -> None:
        """Perform some sanity checks
        - pendings is not empty
        - pendings + duplicates = input
        """
        if not self._pendings:
            raise InconsistentDuplicateSet("pendings is empty")
        pendings = [_.path_bytes for _ in self._pendings]
        duplicates = [_.path_bytes for _ in self._duplicates]
        # compare set to avoid issue with sorting
        paths = set(pendings) | set(duplicates)
        # we recheck for non-unique path
        print(paths)

        # files to be proceed and finally kept
        self._pendings = list(self._files)
        # duplicated files to be removed
        self._duplicates = []

    ##############################################

    # Fixme: confusing
    def __len__(self) -> int:
        """Return number of files"""
        return len(self._files)

    @property
    def number_of_files(self) -> int:
        """Return number of files"""
        # return len(self._input_paths)
        return len(self._files)

    @property
    def number_of_pendings(self) -> int:
        """Return number of pendings"""
        return len(self._pendings)

    @property
    def number_of_duplicates(self) -> int:
        """Return number of duplicates"""
        return len(self._duplicates)

    @property
    def is_singleton(self) -> bool:
        """Return True if only one pending"""
        return len(self._pendings) == 1

    ##############################################

    # Fixme: confusing
    def __iter__(self) -> Iterator[Duplicate]:
        """Iterate on files"""
        return iter(self._files)

    @property
    def pendings(self) -> Iterator[Duplicate]:
        """Iterate on pendings"""
        return iter(self._pendings)

    # Fixme: confusing
    def __getitem__(self, _slice) -> Duplicate:
        """Get pendings"""
        return self._pendings[_slice]

    @property
    def first(self) -> Duplicate:
        """Return first pending"""
        return self._pendings[0]

    @property
    def second(self) -> Duplicate:
        """Return second pending"""
        return self._pendings[1]

    @property
    def followings(self) -> Iterator[Duplicate]:
        """Iterate on pendings after first"""
        return iter(self._pendings[1:])

    @property
    def duplicates(self) -> Iterator[Duplicate]:
        """Iterate on duplicates"""
        return iter(self._duplicates)

    ##############################################

    @property
    def marked(self) -> List[File]:
        """Return list of marked in pendings"""
        return [_ for _ in self._pendings if _]

    @property
    def unmarked(self) -> List[File]:
        """Return list of unmarked in pendings"""
        return [_ for _ in self._pendings if not _]

    @property
    def number_of_marked(self) -> int:
        """Count marked in pendings"""
        return sum([1 for _ in self._pendings if _])

    @property
    def number_of_unmarked(self) -> int:
        """Count unmarked in pendings"""
        return sum([1 for _ in self._pendings if not _])

    ##############################################

    @property
    def paths_bytes(self) -> ByteList:
        return [_.path_bytes for _ in self]

    @property
    def paths_str(self) -> List[str]:
        return [_.path_str for _ in self]

    @property
    def paths(self) -> List[Path]:
        return [_.path for _ in self]

    def __str__(self) -> str:
        return str([str(_) for _ in self.paths])

    @property
    def duplicated_paths(self) -> List[Path]:
        return [_.path for _ in self._duplicates]

    ##############################################

    def sort(self, sorting: str = None, key=None, reverse: bool = False) -> None:
        # Fixme: sort utf-8 bytes ?
        def by_path(_):
            return _.path_str

        def by_path_length(_):
            return len(_.path_str)

        def by_name_length(_):
            return len(_.name)

        def by_parent_length(_):
            n = by_name_length(_)
            SCALE = 1000
            if n > SCALE:
                raise NameError(f"Name length {_} > {SCALE}")
            return len(str(_.parent)) * SCALE + n

        if sorting is not None:
            match sorting:
                case 'path':
                    key = by_path
                case 'path_length':
                    key = by_path_length
                case 'name_length':
                    key = by_name_length
                case 'parent_length':
                    key = by_parent_length
                case _:
                    raise ValueError(f"unknow sorting '{sorting}'")
        elif key is None:
            key = by_path
        self._pendings.sort(key=key, reverse=reverse)

    ##############################################

    @property
    def is_same_parent(self) -> bool:
        parents = set([str(_.parent) for _ in self.paths])
        return len(parents) == 1

    @property
    def common_parent(self) -> Path:
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
        """Move marked files to duplicate list"""
        if self.number_of_marked:
            if not self.number_of_unmarked:
                raise AllFileMarked(f"All files are marked in duplicate set {self.paths_bytes}")
            self._duplicates.extend(self.marked)
            for _ in self.marked:
                self._pendings.remove(_)

    ##############################################

    def rollback(self, rollback_duplicates: bool = False) -> None:
        """
        - if *rollback_duplicates* move duplicates in pending mist
        - unmark pendings
        """
        # Fixme: API ???
        if rollback_duplicates:
            self._pendings += self._duplicates
            self._duplicates = []
        for _ in self._pendings:
            _.unmark()

    ##############################################

    def check(self) -> None:
        """Perform some sanity checks
        - pendings is not empty
        - any pendings in duplicates
        - pendings + duplicates = input
        """
        if not self._pendings:
            raise InconsistentDuplicateSet("pendings is empty")
        pendings = [_.path_bytes for _ in self._pendings]
        duplicates = [_.path_bytes for _ in self._duplicates]
        for _ in duplicates:
            if _ in pendings:
                raise InconsistentDuplicateSet(f"Inconsistent duplicate set: duplicate {_} is also in pendings")
        if (len(pendings) + len(duplicates)) != len(self._files):
            raise InconsistentDuplicateSet(f"Inconsistent duplicate set length: {pendings} + {duplicates} != {self._input_paths}")
        # compare set to avoid issue with sorting
        paths = set(pendings) | set(duplicates)
        if paths != self._input_paths:
            raise InconsistentDuplicateSet(f"Inconsistent duplicate set: {paths} != {self._input_paths}")

    ##############################################

    def check_is_duplicate(self) -> bool:
        ref = self.first
        for _ in self.followings:
            self._logger.debug(f"{LINESEP}{ref}{LINESEP}{_}")
            if not ref.compare_with(_):
                return False
        return True

    ##############################################

    def delete_duplicates(self, dry_run: bool = False) -> None:
        self.check()
        for _ in self._duplicates:
            _.delete(dry_run)


type DuplicateSetIt = Iterator[DuplicateSet]

####################################################################################################

class DuplicatePool:

    # Fixme: naming...
    """Class to implements a pool of set of duplicated files (DuplicateSet)."""

    _logger = _module_logger.getChild('DuplicatePool')

    ##############################################

    @classmethod
    def new_from_json(cls, path: AnyStr | Path) -> 'DuplicatePool':
        pool = cls()
        with open(path, 'r', encoding="utf-8") as fh:
            data = json.load(fh)
            for _ in data:
                pool.add_from_paths(_)
        return pool

    ##############################################

    @classmethod
    def new_from_paths(cls, paths: ByteListIt) -> 'DuplicatePool':
        pool = cls()
        for _ in paths:
            pool.add_from_paths(_)
        return pool

    ##############################################

    def __init__(self, it: DuplicateSetIt = None) -> None:
        self._pool = []
        if it is not None:
            self.fill(it)

    ##############################################

    def fill(self, it: DuplicateSetIt) -> None:
        self._pool.extend(it)

    def add(self, duplicate: DuplicateSet) -> None:
        self._pool.append(duplicate)

    def add_from_paths(self, paths: ByteList) -> None:
        self.add(DuplicateSet.new_from_paths(paths))

    ##############################################

    def __len__(self) -> int:
        return len(self._pool)

    def __iter__(self) -> DuplicateSetIt:
        return iter(self._pool)

    ##############################################

    # def number_of_duplicates

    ##############################################

    def sort(self) -> None:
        """Sort by path"""
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

    def __eq__(self, other: 'DuplicatePool'):
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

    def compare(self, ref: 'DuplicatePool'):
        my_set = self.to_set()
        ref_set = ref.to_set()
        return ref_set - my_set   # , my_set - ref_set
