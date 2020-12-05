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

####################################################################################################

import pathlib
import sys

import filewalker.common.path as PathTools # due to Path class

####################################################################################################

class OsFactory:

    ##############################################

    def __init__(self):

        if sys.platform.startswith('linux'):
            self._name = 'linux'
        elif sys.platform.startswith('win'):
            self._name = 'windows'
        elif sys.platform.startswith('darwin'):
            self._name = 'osx'

    ##############################################

    @property
    def name(self):
        return self._name

    @property
    def on_linux(self):
        return self._name == 'linux'

    @property
    def on_windows(self):
        return self._name == 'windows'

    @property
    def on_osx(self):
        return self._name == 'osx'

OS = OsFactory()

####################################################################################################

_this_file = pathlib.Path(__file__).resolve()

class Path:

    module_directory = _this_file.parents[1]
    config_directory = _this_file.parent

####################################################################################################

class Logging:

    # Used as default when the configuration is not yet available

    default_config_file_name = 'logging.yml'
    directories = (Path.config_directory,)

    ##############################################

    @classmethod
    def find(cls, config_file):
        return pathlib.Path(PathTools.find(config_file, cls.directories))

    ##############################################

    @classmethod
    def default_config_file(cls):
        return cls.find(cls.default_config_file_name)
