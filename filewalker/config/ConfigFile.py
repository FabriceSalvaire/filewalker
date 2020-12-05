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

from pathlib import Path
import importlib.util as importlib_util
import logging
import os
import shutil
import sys

import filewalker.Config.ConfigInstall as ConfigInstall
from . import DefaultConfig

####################################################################################################

class ConfigFile:

    _logger = logging.getLogger(__name__)

    @classmethod
    def default_path(cls):
        # cf. file-system-tool-setup
        return DefaultConfig.Path.join_config_directory('config.py')

    ##############################################

    @classmethod
    def create(cls, **kwargs):

        class args:
            config_directory = Path(kwargs['config_directory']).resolve()
            data_directory = Path(kwargs['data_directory']).resolve()

        template = '''
################################################################################
#
# filewalker Configuration
#
################################################################################

from pathlib import Path

import filewalker.Config.DefaultConfig as DefaultConfig

################################################################################

# class Path(DefaultConfig.Path):
#     config_directory = Path('{0.config_directory}')
'''

        path = args.config_directory.joinpath('config.py')
        if not path.exists():
            cls._logger.info('Create config file {}'.format(path))
            content = template.format(args).lstrip()
            cls.make_user_directory(args)
            with open(path, 'w') as fh:
                fh.write(content)
        else:
            cls._logger.error('config file {} exists'.format(path))

    ##############################################

    @classmethod
    def make_user_directory(cls, args):

        for directory in (
                args.config_directory,
                # args.data_directory,
        ):
            if not directory.exists():
                os.mkdir(directory)

        logging_config_file = ConfigInstall.Logging.default_config_file()
        dst_path = args.config_directory.joinpath(logging_config_file.name)
        if not dst_path.exists():
            shutil.copyfile(logging_config_file, dst_path)

    ##############################################

    def __init__(self, config_path=None):

        self._path = Path(config_path or self.default_path())
        message = 'Load config from {}'.format(self._path)
        sys.stderr.write(message + '\n') # Fixme: ???
        self._logger.info(message)

        if not self._path.exists():
            raise NameError("You must first create a configuration file using the init command")

        # This code as issue with code in class definition ???
        # with open(path) as fh:
        #     code = fh.read()
        # namespace = {'__file__': path}
        # # code_object = compile(code, path, 'exec')
        # exec(code, {}, namespace)
        # for key, value in namespace.items():
        #     setattr(self, key, value)

        # A factory function for creating a ModuleSpec instance based on the path to a file.
        spec = importlib_util.spec_from_file_location(name='Config', location=str(self._path))
        # Create a new module based on spec
        Config = importlib_util.module_from_spec(spec)
        # executes the module in its own namespace when a module is imported
        spec.loader.exec_module(Config)

        # Copy attributes from config or default
        for key in DefaultConfig.__all__:
            customised = hasattr(Config, key)
            if customised:
                src = Config
            else:
                src = DefaultConfig
            value = getattr(src, key)
            setattr(self, key, value)
            if customised:
                # Hack: reset ConfigFile_ClassName in DefaultConfig
                setattr(DefaultConfig, 'ConfigFile_' + key, value)

    ##############################################

    # Fixme: attribute clash ???
    # @property
    # def path(self):
    #     return self._path
