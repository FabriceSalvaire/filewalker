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

__all__ = ['Rdfind']

####################################################################################################

from pathlib import Path
from typing import Generator
import logging
import subprocess
import tempfile

from filewalker.common.string import find_nth
from filewalker.cleaner.DuplicateCleaner import DuplicatePool, DuplicateSet, DuplicateSetIt

####################################################################################################

type ByteList = list[bytes]
type ByteListIt = Generator[ByteList, None, None]   # or Iterator[ByteList]

_module_logger = logging.getLogger(__name__)

####################################################################################################

class Rdfind:

    _logger = _module_logger.getChild('Rdfind')

    ##############################################

    def __init__(self, paths: list[str | Path]) -> None:
        if isinstance(paths, (str, bytes, Path)):
            paths = (paths,)
        self._paths = [
            Path(str(_)).resolve()
            for _ in paths
        ]

    ##############################################

# Usage: rdfind [options] FILE ...
#
# Finds duplicate files recursively in the given FILEs (directories),
# and takes appropriate action (by default, nothing).
#
# Directories listed first are ranked higher, meaning that if a file
# is found on several places, the file found in the directory first
# encountered on the command line is kept, and the others are
# considered duplicate.
#
# options are (default choice within parentheses)
#
# -ignoreempty      (true)| false  ignore empty files (true implies -minsize 1, false implies -minsize 0)
# -minsize N        (N=1)          ignores files with size less than N bytes
# -maxsize N        (N=0)          ignores files with size N bytes and larger (use 0 to disable this check).
# -followsymlinks    true |(false) follow symlinks
# -removeidentinode (true)| false  ignore files with nonunique device and inode
# -checksum           md5 |(sha1)| sha256 | sha512 checksum type
# -deterministic    (true)| false  makes results independent of order from listing the filesystem
# -makesymlinks      true |(false) replace duplicate files with symbolic links
# -makehardlinks     true |(false) replace duplicate files with hard links
# -makeresultsfile  (true)| false  makes a results file
# -outputname  name  sets the results file name to "name" (default results.txt)
# -deleteduplicates  true |(false) delete duplicate files
# -sleep              Xms          sleep for X milliseconds between file reads.
#                                  Default is 0. Only a few values
#                                  are supported; 0,1-5,10,25,50,100
# -dryrun|-n         true |(false) print to stdout instead of changing anything
# -h|-help|--help                  show this help and exit
# -v|--version                     display version number and exit

    def _call_rdfind(self, output: str) -> None:
        """Run rdfind"""
        command = [
            '/usr/bin/rdfind',
            '-followsymlinks', 'false',
            '-checksum', 'sha256',
            '-outputname', output,
            '-dryrun', 'true',
        ]
        command += self._paths
        self._logger.debug(f'Rund rdfind {command}')
        subprocess.check_call(command)

    ##############################################

    def _process_rdfind_output(self, output: str) -> ByteListIt:
        """Yield duplicates from rdfind ouput"""

        def split_line(line: bytes) -> bytes:
            # DUPTYPE_FIRST_OCCURRENCE 3203 3 1 64769 12716788 9 /home
            # filename could have spaces
            # parts = line.split()
            # return b' '.join(parts[7:])
            path_start = find_nth(line, b' ', 7)
            _ = line[path_start+1:]   # -1 unless strip
            # self._logger.info(f"{_}")
            return _

        with open(output, 'rb') as fh:
            duplicates = None
            for line in fh.readlines():
                line = line.strip()
                # rprint(f'>{line}')
                # if line.startswith(b'DUPTYPE_FIRST'):   # _OCCURRENCE
                #     if duplicates:
                #         yield duplicates
                #     duplicates = [split_line(line)]
                # elif line.startswith(b'DUPTYPE_WITHIN'):   # _SAME_TREE
                #     duplicates.append(split_line(line))
                if line.startswith(b'#'):
                    continue
                # if line.startswith(b'DUPTYPE_'):
                #     line = line[8:]
                if line.startswith(b'DUPTYPE_FIRST'):   # _OCCURRENCE
                    if duplicates:
                        yield duplicates
                    duplicates = []
                elif line.startswith(b'DUPTYPE_WITHIN'):   # _SAME_TREE
                    pass
                else:
                    raise ValueError(line)
                duplicates.append(split_line(line))
            if duplicates:
                yield duplicates

    ##############################################

    def run(self) -> ByteListIt:
        # Fixme: mandatory ???
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._logger.debug(f'Created temporary directory {tmp_dir}')
            output = tmp_dir + '/results.txt'
            self._call_rdfind(output)
            yield from self._process_rdfind_output(output)

    ##############################################

    @property
    def duplicate_pool(self) -> DuplicatePool:
        return DuplicatePool.new_from_paths(self.run())

    ##############################################

    @property
    def duplicate_set_it(self) -> DuplicateSetIt:
        for _ in self.run():
            yield DuplicateSet.new_from_str(_)
