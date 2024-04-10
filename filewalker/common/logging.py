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

__all__ = ['setup_logging']

####################################################################################################

import logging
import logging.config
import os

import yaml

import filewalker.config.ConfigInstall as ConfigInstall
default_config_file = ConfigInstall.Logging.default_config_file()

####################################################################################################

LOG_LEVEL_ENV = 'filewalkerLogLevel'

####################################################################################################

def _fix_formater(logging_config: logging.config) -> None:
    if ConfigInstall.OS.on_linux:
        # Fixme: \033 is not interpreted in YAML
        ansi = logging_config['formatters']['ansi']
        formatter_config = ansi['format']
        ansi['format'] = formatter_config.replace('<ESC>', '\033')
    if ConfigInstall.OS.on_linux:
        formatter = 'ansi'
    else:
        formatter = 'simple'
    logging_config['handlers']['console']['formatter'] = formatter

####################################################################################################

def setup_logging(
    config_file: str = default_config_file,
    level: int = None,
) -> logging.Logger:
    logging_config = yaml.load(
        open(str(config_file), 'r', encoding='utf8'),
        Loader=yaml.SafeLoader,
    )
    _fix_formater(logging_config)
    logging.config.dictConfig(logging_config)

    root_logger = logging.getLogger('filewalker')

    if level is not None:
        root_logger.setLevel(level)
    else:
        if LOG_LEVEL_ENV in os.environ:
            numeric_level = getattr(logging, os.environ[LOG_LEVEL_ENV], None)
            root_logger.setLevel(numeric_level)

    return root_logger
