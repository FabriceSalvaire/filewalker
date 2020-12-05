####################################################################################################
#
# filewalker — ...
# Copyright (C) 2020 Fabrice Salvaire
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

"""Define default configuration.

Theses defaults are overridden in the user configuration file via sub-classing instead of monkey
patching.  Consequently if a class depends of another one, refer to it as *ConfigFile_ClassName* so
as to bind to the ConfigFile space, i.e. to the user version.

"""

####################################################################################################

__all__ = [
    'Logging',
    'Path',
]

####################################################################################################

import pathlib
import os

####################################################################################################

class Path:

    home_directory = pathlib.Path(os.environ['HOME'])
    application_name = 'file-system-tool'

    config_directory = None

    ##############################################

    # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

    @classmethod
    def join_home_directory(cls, *args):
        return cls.home_directory.joinpath(*args)

    @classmethod
    def join_system_config_directory(cls, *args):
        return cls.join_home_directory('.config', *args)

    ##############################################

    @classmethod
    def join_config_directory(cls, *args):
        return cls.config_directory.joinpath(*args)

####################################################################################################

Path.config_directory = Path.join_system_config_directory(Path.application_name)

# hack to reset Path
ConfigFile_Path = Path

####################################################################################################

class Logging:

    ##############################################

    @classmethod
    def config_file(cls_file):
        return ConfigFile_Path.join_config_directory('logging.yml')
