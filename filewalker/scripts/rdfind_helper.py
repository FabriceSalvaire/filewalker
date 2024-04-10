####################################################################################################
#
# DuplicateFinder -
# Copyright (C) 2024 Salvaire Fabrice
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

# Fixme: check start user_attr !!!

####################################################################################################

from pathlib import Path
import argparse
import logging
# from pprint import pprint

from colorama import Fore
import colorama

from filewalker.cleaner.DuplicateSet import DuplicateSet, Duplicate
from filewalker.common.logging import setup_logging
from filewalker.path.file import File
from filewalker.interface.rdfind import Rdfind

####################################################################################################

colorama.init()   # autoreset=True

logger = setup_logging(level=logging.DEBUG)
logger.info("Start ...")

####################################################################################################

DRY_RUN = False

# FG_COLOR = Fore.BLACK
FG_COLOR = Fore.WHITE

####################################################################################################

def rprint(*args) -> None:
    print(*args, FG_COLOR)

####################################################################################################

def rename(file: File) -> None:
    """Interactive rename"""
    rprint(f"{Fore.RED}Rename: {Fore.BLUE}{file}")
    rc = input()
    if rc:
        file.rename(rc, rebuild=True)
        rprint(f"Renamed: {FG_COLOR}{rc}")

####################################################################################################

def get_index(duplicates: DuplicateSet) -> Duplicate:
    """Wait for index input
    Return keeped path
    """
    while True:
        rprint(Fore.RED + "Keep ?")
        rc = input().lower()
        # Skip ?
        if not rc:
            return None
        # Exit ?
        if rc == 'q':
            exit(0)
        try:
            # Rename action r<int>
            if rc.startswith('r'):
                _ = duplicates[int(rc[1:])]
                rename(_)
            else:
                return duplicates[int(rc)]
        except (ValueError, IndexError):
            rprint(Fore.RED + "Bad index")

####################################################################################################

def cleanup(duplicates: DuplicateSet) -> None:
    keeped = get_index(duplicates)
    if keeped is not None:
        keeped_rating = keeped.file.rating
        rprint(f"{Fore.GREEN}Keep    {Fore.BLUE}{keeped}")
        to_remove = set(duplicates) - set((keeped,))
        # Fixme: use mark ?
        if len(to_remove) == len(duplicates):
            raise NameError("All files will be removed")
        rating = keeped_rating
        if not DRY_RUN:
            for _ in to_remove:
                removed = _.path
                # rprint(f'{rating} vs {keeped_rating}')
                rating = max(_.file.rating, rating)
                try:
                    #!!! removed.unlink()
                    rprint(f"{Fore.RED}Removed {FG_COLOR}{removed}")
                except FileNotFoundError:
                    rprint(f"{Fore.RED}Error {FG_COLOR}{removed}")
        if rating != keeped_rating and rating > 0:
            rprint(f"  copy rating {Fore.RED}{rating}{FG_COLOR} was {keeped_rating}")
            keeped.file.rating = rating
    else:
        rprint("skip")

####################################################################################################

# class DuplicateSorter:
#
#     ##############################################
#
#     def __init__(self, duplicates: list[str]) -> None:
#         self._duplicates = list(duplicates)
#         names = [_.name for _ in duplicates]
#         parents = [_.parent for _ in duplicates]
#         uniq_parents = set(parents)
#         self._same_parent = len(uniq_parents) == 1
#
#     ##############################################
#
#     @property
#     def same_parent(self) -> bool:
#         return self._same_parent
#
#     ##############################################
#
#     @property
#     def by_name_length(self) -> list[str]:
#         return sorted(self._duplicates, key=lambda _ : len(_.name))

####################################################################################################

def on_duplicate(
    duplicates: DuplicateSet,
    only: list[str] = None,
) -> None:
    """Process duplicates
    *only* is a list of suffixes
    """
    if only is not None:
        if True not in [_.suffix in only for _ in duplicates]:
            return
    rprint()
    rprint(Fore.GREEN + f"Found {len(duplicates)} identical files")
    # Fixme:
    #   if same parent, keep shortest
    # sorter = DuplicateSorter(duplicates)
    if duplicates.is_same_parent:
        rprint(f"  {Fore.RED}same parent")
    # # duplicates gives order !
    # duplicates = sorter.by_name_length
    for i, _ in enumerate(duplicates):
        BAD = False
        if 'duplicate' in str(_.parent):
            BAD = True
        if _.name.endswith('~'):
            BAD = True
        for k in range(1, 10):
            if _.stem.endswith(f'({k})'):
                BAD = True
        color = FG_COLOR if BAD else Fore.BLUE
        rprint(f"  {Fore.RED}{i} {color}{_.parent}")
        rprint(f"      {color}{_.name} {Fore.RED}{i}")
    cleanup(duplicates)

####################################################################################################

def scan(
    path: Path,
    **kwargs,
) -> None:
    """Run rdfind and process duplicates"""
    rprint(Fore.RED + f"Scan directory {path} ...")
    rdfind = Rdfind(path)
    # for duplicate_set in rdfind.to_duplicate_pool:
    for duplicate_set in rdfind.duplicate_set_it:
        on_duplicate(duplicate_set, **kwargs)

####################################################################################################

def main() -> None:
    """main"""
    parser = argparse.ArgumentParser(
        prog='rdfind helper',
        description='',
        epilog='',
    )

    parser.add_argument(
        'path',
        # Fixme: default='.',
    )
    parser.add_argument(
        '-w',
        '--white',
        default=False,
        action='store_true',
        help="setup white fg",
    )
    # Fixme: black
    parser.add_argument(
        '--dry-run',
        default=False,
        action='store_true',
        help="",
    )
    parser.add_argument(
        '--only',
        default=None,
        help="a list of suffixes separated by a comma to only process for duplicates",
    )
    args = parser.parse_args()

    if args.white:
        global FG_COLOR
        FG_COLOR = Fore.WHITE
    if args.dry_run:
        global DRY_RUN
        DRY_RUN = True
        print(f"Set to dry run")
    # logging.info("Start...")
    path = Path(args.path).resolve()
    only = None
    if args.only:
        only = args.only.split(',')
        print(f"only = {only}")
    scan(path, only=only)
    # logging.info("Done")
