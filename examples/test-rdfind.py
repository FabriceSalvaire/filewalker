#! /usr/bin/env python3

####################################################################################################
#
# filewalker — ...
# Copyright (C) 2024 Fabrice Salvaire
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

import argparse
from pathlib import Path

import logging
from filewalker.common.logging import setup_logging
logger = setup_logging(level=logging.DEBUG)
logger.info("Start ...")

from filewalker.interface.rdfind import Rdfind

####################################################################################################

parser = argparse.ArgumentParser(
    prog='',
    description='',
    epilog='',
)

parser.add_argument(
    'path',
)

args = parser.parse_args()

rdfind = Rdfind(args.path)
# for duplicate_set in rdfind.to_duplicate_pool:
for duplicate_set in rdfind.duplicate_set_it:
    print('-'*50)
    for _ in duplicate_set:
        print(_)
    duplicate_set.check_is_duplicate()
