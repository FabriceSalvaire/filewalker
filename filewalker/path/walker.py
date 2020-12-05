####################################################################################################
#
# filewalker — ...
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

from pathlib import Path
# from os import PathLike
from typing import AnyStr, List, Union
import os

####################################################################################################

class WalkerAbc:

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

    def run(self, topdown: bool = False, sort: bool = False, followlinks: bool = False) -> None:
        # to avoid UnicodeEncodeError: surrogates not allowed
        top = str(self._path).encode('utf-8')
        for dirpath, dirnames, filenames in os.walk(top, topdown=topdown, followlinks=followlinks):
            # dirnames and filenames are List[bytes]
            if topdown and sort:
                self.sort_direnames(dirnames)
            if hasattr(self, 'on_directory'):
                for directory in dirnames:
                    self.on_directory(dirpath, directory)
            if hasattr(self, 'on_filename'):
                for filename in filenames:
                    self.on_filename(dirpath, filename)

    ##############################################

    def sort_direnames(self, dirnames: List[bytes]) -> None:
        # Fixme: sort utf-8 bytes ???
        dirnames.sort()

    ##############################################

    # def on_directory(self, dirpath: bytes, dirname: bytes) -> None:
    #     pass

    ##############################################

    # def on_filename(self, dirpath: bytes, filename: bytes) -> None:
    #     pass
