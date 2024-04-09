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

# from os import PathLike
from pathlib import Path
from typing import AnyStr, List, Union
import os

####################################################################################################

class WalkerAbc:

    """Base class to implement a walk in a file hierarchy."""

    ##############################################

    # def __init__(self, path : Union[AnyStr, PathLike[AnyStr]]) -> None:
    def __init__(self, path: Union[AnyStr, Path]) -> None:
        # Make the path absolute, resolving any symlinks.
        self._path = Path(path).expanduser().resolve()
        if not self._path.exists():
            raise ValueError(f"Path {self._path} doesn't exists")

    ##############################################

    @property
    def path(self) -> Path:
        return self._path

    ##############################################

    def run(self,
            top_down: bool = False,
            sort: bool = False,
            follow_links: bool = False,
            max_depth: int = -1,
            ) -> None:
        if max_depth >= 0:
            top_down = True
            depth = 0
        # to avoid UnicodeEncodeError: surrogates not allowed
        top = str(self._path).encode('utf-8')
        for dirpath, dirnames, filenames in os.walk(top, topdown=top_down, followlinks=follow_links):
            # dirnames and filenames are List[bytes]
            if top_down and sort:
                self.sort_dirnames(dirnames)
            if hasattr(self, 'on_directory'):
                for directory in dirnames:
                    self.on_directory(dirpath, directory)
            if hasattr(self, 'on_filename'):
                for filename in filenames:
                    self.on_filename(dirpath, filename)
            if max_depth >= 0:
                depth += 1
                if depth > max_depth:
                    break

    ##############################################

    def sort_dirnames(self, dirnames: List[bytes]) -> None:
        # Fixme: sort utf-8 bytes ???
        dirnames.sort()

    ##############################################

    # def on_directory(self, dirpath: bytes, dirname: bytes) -> None:
    #     raise NotImplementedError

    ##############################################

    # def on_filename(self, dirpath: bytes, filename: bytes) -> None:
    #     raise NotImplementedError
