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

__all__ = ['find']

####################################################################################################

from pathlib import Path
import os

####################################################################################################

def find(file_name, directories):

    # Fixme: ???
    if isinstance(directories, bytes):
        directories = (directories,)

    for directory in directories:
        for directory_path, _, file_names in os.walk(directory):
            if file_name in file_names:
                return Path(directory_path).joinpath(file_name)

    raise NameError("File %s not found in directories %s" % (file_name, str(directories)))
