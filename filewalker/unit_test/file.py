####################################################################################################
#
# filewalker -
# Copyright (C) 2024 Fabrice Salvaire
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

__all__ = [
    'make_content256',
    'make_content1',
    'make_content2',
    'TemporaryDirectory',
    'TemporaryDirectoryWrapper',
]

####################################################################################################

from pathlib import Path
import os
import tempfile
import unittest
# from unittest import skip

####################################################################################################

from filewalker.path.file import *

####################################################################################################

def make_content256(size: int = 1) -> bytes:
    content1 = b''.join([bytes(chr(_), 'latin1') for _ in range(256)])
    return content1 * size

def make_content1(size: int = 1) -> bytes:
    content1 = make_content256()
    content2 = content1[128:128+62] + content1[64:128] + content1[:64] + content1[128+64:]
    return content2[:240] * size

def make_content2(size: int = 1) -> bytes:
    content1 = make_content256()
    content2 = content1[64:128] + content1[128+64:] + content1[128:128+62] + content1[:64]
    return content2[:250] * size

####################################################################################################

class TemporaryDirectoryWrapper:

    ##############################################

    def __init__(self, path: str) -> None:
        self._path = Path(path)

    ##############################################

    def joinpath(self, filename: str) -> Path:
        return self._path.joinpath(filename)

    ##############################################

    def make_file(self, filename: str, content: str | bytes = '') -> File:
        path = self.joinpath(filename)
        print(f"Make {path}")
        if isinstance(content, bytes):
            fh = open(path, 'wb')
        else:
            fh = open(path, 'w', encoding='utf8')
        fh.write(content)
        fh.close()
        return File.from_path(path), path

####################################################################################################

class TemporaryDirectory:

    ##############################################

    def __init__(self, *args, **kwargs) -> None:
        self._tmp_directory = tempfile.TemporaryDirectory()
        print('Created temporary directory', self._tmp_directory.name)
        self._chdir = kwargs.get('chdir', False)

    ##############################################

    def __enter__(self) -> TemporaryDirectoryWrapper:
        path = self._tmp_directory.name
        if self._chdir:
            os.chdir(path)
        return TemporaryDirectoryWrapper(path)

    ##############################################

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._tmp_directory.cleanup()
