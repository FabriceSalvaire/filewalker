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
import hashlib
import os
import subprocess

from FileSystemTool.path.walker import WalkerAbc

####################################################################################################

class File:

    ST_NBLOCKSIZE = 512

    __slots__ = [
        '_dirpath',
        '_path',
        '_stat',
        '_allocated_size',
        '_sha',
    ]

    SHA_METHOD = hashlib.sha1

    SOME_BYTES = 64
    PARTIAL_SHA_BYTES = 10 * 1024

    ##############################################

    def __init__(self, dirpath: bytes, path: bytes) -> None:
        self._dirpath = dirpath
        self._path = path
        self._stat = None
        self._allocated_size = None
        self._sha = None

    ##############################################

    @property
    def absolut_path_bytes(self) -> bytes:
        return os.path.join(self._dirpath, self._path)

    ##############################################

    def __str__(self) -> str:
        return f"{self.absolut_path_bytes}"

    ##############################################

    @property
    def is_symlink(self) -> bool:
        return os.path.islink(self.absolut_path_bytes)

    ##############################################

    @property
    def stat(self) -> os.stat_result:
        # if not hasattr(self, '_stat'):
        if self._stat is None:
            # does not follow symbolic links
            self._stat = os.lstat(self.absolut_path_bytes)
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
        with open(self.absolut_path_bytes, 'rb') as fh:
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
            size = self.SOME_BYTES
        return self._read_content(size)

    ##############################################

    def last_bytes(self, size: Union[int, None] = None) -> str:
        if size is None:
            size = self.SOME_BYTES
        return self._read_content(-size)

    ##############################################

    def compare_with(self, other: Type['File']):
        # Fixme: Posix only
        # command = ('/usr/bin/cmp', '--silent', self.absolut_path_bytes, other.absolut_path_bytes)
        # return subprocess.run(command).returncode == 0

        size = self.size
        if size != other.size:
            return False

        # Fixme: check < CHUNK_SIZE, > CHUNK_SIZE, = CHUNK_SIZE +1, ...
        CHUNK_SIZE = 1024
        with open(self.absolut_path_bytes, 'rb') as fh1:
            with open(other.absolut_path_bytes, 'rb') as fh2:
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

####################################################################################################

class Walker(WalkerAbc):

    ##############################################

    @classmethod
    def walk(cls, path: Union[AnyStr, Path]) -> Type['Walker']:
        walker = Walker(path)
        walker.run(topdown=True, sort=True, followlinks=False)
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

    def _remove_different_feature(self, method) -> int:
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

    def remove_different_first_byte(self) -> int:
        self._remove_different_feature(File.first_bytes)

    def remove_different_last_byte(self) -> int:
        self._remove_different_feature(File.last_bytes)

    def remove_different_sha(self) -> int:
        self._remove_different_feature(lambda file_obj: file_obj.sha)

    ##############################################

    def join(self) -> None:
        files = []
        for file_objs in self._size_map.values():
            files.extend(file_objs)
        self._files = files
