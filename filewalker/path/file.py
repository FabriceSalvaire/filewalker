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

__all__ = ["File"]

####################################################################################################

from pathlib import Path
from typing import Union, Type
import hashlib
import logging
import os
import subprocess

####################################################################################################

_module_logger = logging.getLogger(__name__)

####################################################################################################

class File:

    ST_NBLOCKSIZE = 512

    __slots__ = [
        '_parent',
        '_name',
        '_stat',
        '_allocated_size',
        '_sha',
        'user_data',
    ]

    SHA_METHOD = hashlib.sha1

    SOME_BYTES_SIZE = 64    # rdfind uses 64
    PARTIAL_SHA_BYTES = 10 * 1024

    _logger = _module_logger.getChild("File")

    ##############################################

    @staticmethod
    def to_bytes(_):
        return str(_).encode('utf-8')

    ##############################################

    @classmethod
    def from_str(cls, path: str) -> Type["File"]:
        return cls.from_path(Path(path))

    ##############################################

    @classmethod
    def from_path(cls, path: Path) -> Type["File"]:
        return cls(cls.to_bytes(path.parent), cls.to_bytes(path.name))

    ##############################################

    def __init__(self, parent: bytes, name: bytes) -> None:
        if not name:
            raise ValueError("name must be provided")
        self._parent = parent
        self._name = name
        self.vacuum()

    ##############################################

    def vacuum(self) -> None:
        self._stat = None
        self._allocated_size = None
        self._sha = None
        self.user_data = None

    ##############################################

    @property
    def path_bytes(self) -> bytes:
        return os.path.join(self._parent, self._name)

    @property
    def path_str(self) -> str:
        return self.path_bytes.decode('utf-8')

    @property
    def path(self) -> Path:
        # Fixme: cache ?
        return Path(self.path_str)

    ##############################################

    def __str__(self) -> str:
        return f"{self.path_bytes}"

    ##############################################

    @property
    def is_file(self) -> bool:
        return os.path.isfile(self.path_bytes)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.path_bytes)

    @property
    def is_symlink(self) -> bool:
        return os.path.islink(self.path_bytes)

    ##############################################

    @property
    def stat(self) -> os.stat_result:
        # if not hasattr(self, '_stat'):
        if self._stat is None:
            # does not follow symbolic links
            self._stat = os.lstat(self.path_bytes)
        return self._stat

    ##############################################

    @property
    def is_empty(self) -> bool:
        return self.stat.st_size == 0

    ##############################################

    @property
    def size(self) -> int:
        return self.stat.st_size

    @property
    def inode(self) -> int:
        return self.stat.st_ino

    @property
    def device(self) -> int:
        return self.stat.st_dev

    @property
    def mtime(self) -> int:
        return self.stat.st_mtime_ns

    @property
    def uid(self) -> int:
        return self.stat.st_uid

    @property
    def gid(self) -> int:
        return self.stat.st_gid

    ##############################################

    @property
    def allocated_size(self) -> int:
        # See https://raw.githubusercontent.com/coreutils/coreutils/master/src/du.c
        # https://github.com/rofl0r/gnulib/blob/master/lib/stat-size.h
        # define ST_NBLOCKSIZE 512
        # ST_NBLOCKS (*sb) * ST_NBLOCKSIZE
        # if not hasattr(self, '_allocated_size'):
        if self._allocated_size is None:
            self._allocated_size = self.stat.st_blocks * 512
        return self._allocated_size

    ##############################################

    def _read_content(self, size: Union[int, None] = None) -> bytes:
        # unlikely to happen
        # if self.is_empty:
        #     return b''
        with open(self.path_bytes, 'rb') as fh:
            if size is not None and size < 0:
                if abs(size) < self.size:
                    fh.seek(size, os.SEEK_END)
                    size = abs(size)
                else:
                    size = None
            data = fh.read(size)
        return data

    ##############################################

    @property
    def sha(self) -> str:
        if self._sha is None:
            if self.is_empty:
                self._sha = ''
            else:
                data = self._read_content()
                self._sha = self.SHA_METHOD(data).hexdigest()
        return self._sha

    ##############################################

    def partial_sha(self, size: Union[int, None] = None) -> str:
        if self.is_empty:
            return ''
        if size is None:
            size = self.PARTIAL_SHA_BYTES
        data = self._read_content(size)
        return self.SHA_METHOD(data).hexdigest()

    ##############################################

    def first_bytes(self, size: Union[int, None] = None) -> str:
        if size is None:
            size = self.SOME_BYTES_SIZE
        return self._read_content(size)

    ##############################################

    def last_bytes(self, size: Union[int, None] = None) -> str:
        if size is None:
            size = self.SOME_BYTES_SIZE
        return self._read_content(-size)

    ##############################################

    def compare_with(self, other: Type['File'], posix: bool = False) -> bool:
        if posix:
            return self._compare_with_posix(other)
        else:
            return self._compare_with_py(other)

    ##############################################

    def _compare_with_posix(self, other: Type['File']) -> bool:
        command = ('/usr/bin/cmp', '--silent', self.path_bytes, other.path_bytes)
        return subprocess.run(command).returncode == 0

    ##############################################

    def _compare_with_py(self, other: Type['File']) -> bool:
        size = self.size
        if size != other.size:
            return False

        # Fixme: check < CHUNK_SIZE, > CHUNK_SIZE, = CHUNK_SIZE +1, ...
        CHUNK_SIZE = 1024
        with open(self.path_bytes, 'rb') as fh1:
            with open(other.path_bytes, 'rb') as fh2:
                offset = 0
                while offset < size:
                    offset += CHUNK_SIZE
                    fh1.seek(offset)
                    fh2.seek(offset)
                    data1 = fh1.read(CHUNK_SIZE)
                    data2 = fh2.read(CHUNK_SIZE)
                    if data1 != data2:
                        return False
            return True

    ##############################################

    def is_identical_to(self, other: Type['File']):
        return (
            not self.is_empty
            and self.size == other.size
            and self.first_bytes == other.first_bytes
            and self.last_bytes == other.last_bytes
            and (self.size <= self.PARTIAL_SHA_BYTES or self.partial_sha() == other.partial_sha())
            and self.sha == other.sha
            and self.compare_with(other)
        )

    ##############################################

    def _find_rename_alternative(self, dst: Path, pattern: str) -> Path:
        parent = dst.parent
        stem = dst.stem
        suffix = dst.suffix
        i = 0
        while True:
            i += 1
            new_dst = parent.joinpath(pattern.format(stem=stem, i=i, suffix=suffix))
            if not new_dst.exists():
                return new_dst

    ##############################################

    def rename(self, dst: Union[Path, str],
               pattern: str = "{stem} ({i}){suffix}",
               rebuild: bool = False
               ) -> Union[Type["File"], None]:
        if isinstance(dst, str):
            dst = Path(dst)
        if dst == self.path:
            self._logger.warning(f"same destination{self.path}")
            return None
        if dst.exists():
            new_dst = self._find_rename_alternative(dst, pattern)
            self._logger.warning(f"{dst} exists, rename {self.path} to {new_dst}")
            dst = new_dst
        self.path.rename(dst)
        if rebuild:
            return self.from_path(dst)
        else:
            return dst

    ##############################################

    def move_to(self, dst: Union[Path, str]) -> None:
        dst_path = Path(dst).joinpath(self.path.name)
        self._logger.info(f"move {self.path_str} -> {dst_path}")
        self.rename(dst_path)
