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

__all__ = ['setup_logging']

####################################################################################################

import logging
import logging.config
import os

import yaml

import FileSystemTool.config.ConfigInstall as ConfigInstall
default_config_file = ConfigInstall.Logging.default_config_file()

####################################################################################################

def fix_formater(logging_config):

    if ConfigInstall.OS.on_linux:
        # Fixme: \033 is not interpreted in YAML
        formatter_config = logging_config['formatters']['ansi']['format']
        logging_config['formatters']['ansi']['format'] = formatter_config.replace('<ESC>', '\033')

    if ConfigInstall.OS.on_linux:
        formatter = 'ansi'
    else:
        formatter = 'simple'
    logging_config['handlers']['console']['formatter'] = formatter

####################################################################################################

def setup_logging(config_file=default_config_file):

    logging_config = yaml.load(
        open(str(config_file), 'r'),
        Loader=yaml.SafeLoader,
    )
    fix_formater(logging_config)
    logging.config.dictConfig(logging_config)

    root_logger = logging.getLogger('FileSystemTool')

    log_level_env = 'FileSystemToolLogLevel'
    if log_level_env in os.environ:
        numeric_level = getattr(logging, os.environ[log_level_env], None)
        root_logger.setLevel(numeric_level)

    return root_logger
