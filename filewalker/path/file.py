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

"""**Design Note**

On Linux, filenames are just a bunch of bytes, and are not necessarily encoded in a particular
encoding.  Python 3 tries to turn everything into Unicode strings, and implements a scheme to
translate byte strings to Unicode strings and back without loss, and without knowing the original
encoding.  Python3 uses partial surrogates to encode the 'bad' bytes, but the normal UTF8 encoder
can't handle them when printing to the terminal.

Example::

    # decode
    bad_utf8 = b'C\xc3N'.decode('utf8','surrogateescape')
    # encode
    bad_utf8.encode('utf8','surrogateescape')
    # but UnicodeEncodeError: 'utf-8' codec can't encode character ...
    print(bad_utf8)

"""

####################################################################################################

__all__ = ['File']

####################################################################################################

from pathlib import Path
from typing import AnyStr, Optional, Type
import hashlib
import logging
import os
import subprocess

import xattr

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

    _logger = _module_logger.getChild('File')

    ##############################################

    @classmethod
    def decode(cls, _: bytes) -> str:
        """decode path"""
        try:
            _ = _.decode('utf8')
        except UnicodeDecodeError:
            cls._logger.error(f"unicode error {_}")
            _ = _.decode('latin1')
        return _

    ##############################################

    @staticmethod
    def encode(_: str) -> bytes:
        return str(_).encode('utf-8')

    ##############################################

    @classmethod
    def from_str(cls, path: str | bytes) -> 'File':
        if isinstance(path, bytes):
            return cls.from_bytes(path)
        return cls.from_path(Path(path))

    ##############################################

    @classmethod
    def from_bytes(cls, path: bytes) -> 'File':
        _ = path.rfind(b'/')
        if _ != -1:
            parent = path[:_]
            name = path[_+1:]
        else:
            parent = b''
            name = bytes(path)
        return cls(parent, name)

    ##############################################

    @classmethod
    def from_path(cls, path: Path) -> 'File':
        return cls(cls.encode(path.parent), cls.encode(path.name))

    ##############################################

    def __init__(self, parent: bytes, name: bytes) -> None:
        # Fixme: design
        #  why bytes and not str or Path ???
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
    def parent(self) -> bytes:
        return self._parent

    @property
    def name(self) -> bytes:
        return self._name

    @property
    def stem(self) -> bytes:
        # return self.path.stem
        name = self._name
        _ = name.find(b'.')
        if _ != -1:
            return name[:_]
        else:
            return name

    @property
    def suffix(self) -> bytes:
        # return self.path.suffix
        # Fixme: duplicated
        name = self._name
        _ = name.find(b'.')
        if _ != -1:
            return name[_:]
        else:
            return b''

    @property
    def path_bytes(self) -> bytes:
        return os.path.join(self._parent, self._name)

    @property
    def path_str(self) -> str:
        return self.decode(self.path_bytes)

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

    def _read_content(self, size: Optional[int] = None) -> bytes:
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

    def partial_sha(self, size: Optional[int] = None) -> str:
        if self.is_empty:
            return ''
        if size is None:
            size = self.PARTIAL_SHA_BYTES
        data = self._read_content(size)
        return self.SHA_METHOD(data).hexdigest()

    ##############################################

    def first_bytes(self, size: Optional[int] = None) -> str:
        if size is None:
            size = self.SOME_BYTES_SIZE
        return self._read_content(size)

    ##############################################

    def last_bytes(self, size: Optional[int] = None) -> str:
        if size is None:
            size = self.SOME_BYTES_SIZE
        return self._read_content(-size)

    ##############################################

    def compare_with(self, other: 'File', posix: bool = False) -> bool:
        if posix:
            return self._compare_with_posix(other)
        return self._compare_with_py(other)

    ##############################################

    def _compare_with_posix(self, other: 'File') -> bool:
        # Fixme: portability
        command = ('/usr/bin/cmp', '--silent', self.path_bytes, other.path_bytes)
        # Fixme: check ?
        return subprocess.run(command).returncode == 0

    ##############################################

    def _compare_with_py(self, other: 'File') -> bool:
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

    def is_identical_to(self, other: 'File'):
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
            new_dst = parent / pattern.format(stem=stem, i=i, suffix=suffix)
            if not new_dst.exists():
                return new_dst

    ##############################################

    def rename(self, dst: Path | str,
               pattern: str = "{stem} ({i}){suffix}",
               rebuild: bool = False
               ) -> Type['File'] | None:
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

    def move_to(self, dst: Path | str) -> None:
        dst_path = Path(dst) / self.path.name
        self._logger.info(f"move {self.path_str} -> {dst_path}")
        self.rename(dst_path)

    ##############################################

    def write(self, data: bytes) -> None:
        with open(self.path_bytes, 'wb') as fh:
            fh.write(data)

    ##############################################

    USER_BALOO_RATING = 'user.baloo.rating'

    @property
    def rating(self) -> int:
        path = self.path_bytes
        if self.USER_BALOO_RATING in xattr.listxattr(path):
            _ = xattr.getxattr(path, self.USER_BALOO_RATING)
            return int(_)
        else:
            return -1

    @rating.setter
    def set_rating(self, rating: int) -> None:
        path = self.path_bytes
        _ = str(rating).encode('ascii')
        xattr.setxattr(path, self.USER_BALOO_RATING, _)
