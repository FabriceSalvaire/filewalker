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

"""
rdfind results.txt format:


.. code-block::

    # Automatically generated
    # duptype id depth size device inode priority name
    DUPTYPE_FIRST_OCCURRENCE 6574 3 43 64770 7631248 3 /home/...
    DUPTYPE_WITHIN_SAME_TREE -6574 3 43 64770 7631376 3 /home/...

"""

####################################################################################################

from pathlib import Path
from typing import AnyStr, List, Union

# from filewalker.path.file import File
from filewalker.common.string import find_nth
from filewalker.cleaner.DuplicateCleaner import DuplicatePool

####################################################################################################

def load(path: Union[AnyStr, Path]) -> List[List[str]]:
    path = Path(path).expanduser().resolve()
    duplicate_set = []
    with open(path) as fh:
        paths = []
        for line in fh.readlines():
            if line.startswith('#'):
                continue
            elif line.startswith('DUPTYPE_FIRST_OCCURRENCE'):
                if paths:
                    duplicate_set.append(paths)
                paths = []
            elif line.startswith('DUPTYPE_WITHIN_SAME_TREE'):
                pass
            else:
                raise ValueError(line)
            # file path are printed with space !
            path_start = find_nth(line, ' ', 7)
            paths.append(line[path_start+1:-1])
        if paths:
            duplicate_set.append(paths)
    return duplicate_set

####################################################################################################

def load_to_duplicate_pool(path: Union[AnyStr, Path]) -> DuplicatePool:
    paths = load(path)
    return DuplicatePool.new_from_paths(paths)
