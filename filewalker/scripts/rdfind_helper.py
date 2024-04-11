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

from datetime import datetime
from pathlib import Path
import argparse
import logging
import os
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

class Cleaner:

    ##############################################

    def __init__(self) -> None:
        # self._reset()
        self._path = None
        self._log = None

    ##############################################

    def _reset(self, path: str) -> None:
        self._path = path
        self._log = None

    ##############################################

    def open_log(self) -> None:
        if self._log is None:
            suffix = datetime.now().isoformat().replace(':', '-').replace('.', '_')
            log_path = Path(self._path).joinpath(f'cleaner-log-{suffix}.txt')
            if log_path.exists():
                raise NameError(f"log file {log_path} exists")
            self._log = open(log_path, 'w', encoding='utf8')

    ##############################################

    def close_log(self) -> None:
        if self._log is not None:
            self._log.close()

    ##############################################

    def log(self, message: str) -> None:
        self.open_log()
        self._log.write(message + os.linesep)
        self._log.flush()

    ##############################################

    def rprint(self, *args) -> None:
        print(*args, FG_COLOR)

    ##############################################

    def rename(self, file: File) -> None:
        """Interactive rename"""
        self.rprint(f"{Fore.RED}Rename: {Fore.BLUE}{file}")
        rc = input()
        if rc:
            file.rename(rc, rebuild=True)
            self.rprint(f"Renamed: {FG_COLOR}{rc}")

    ##############################################

    def get_index(self, dset: DuplicateSet) -> Duplicate:
        """Wait for index input
        Return keeped path
        """
        while True:
            self.rprint(Fore.RED + "Keep ?")
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
                    _ = dset[int(rc[1:])]
                    self.rename(_)
                else:
                    return dset[int(rc)]
            except (ValueError, IndexError):
                self.rprint(Fore.RED + "Bad index")

    ##############################################

    def cleanup(
        self,
        dset: DuplicateSet,
    ) -> None:
        # keeped = dset.first
        keeped = dset.unmarked

        # Sanity checks
        if len(keeped) > 1:
            raise NameError(f"More than one keeped files {keeped}")
        dset.check()
        # dset.check_is_duplicate()
        keeped = keeped.pop()
        to_remove = set(dset) - set((keeped,))
        if len(to_remove) == dset.number_of_files:
            raise NameError("All files will be removed")

        keeped_rating = keeped.file.rating
        self.log(f"keeped    {keeped.path} *{keeped_rating}")
        self.rprint(f"{Fore.GREEN}Keep    {Fore.BLUE}{keeped}")
        rating = keeped_rating

        for _ in dset.duplicates:
            removed = _.path
            # self.rprint(f'{rating} vs {keeped_rating}')
            removed_rating = _.file.rating
            rating = max(removed_rating, rating)
            # try:
            self.log(f"  removed {removed} *{removed_rating}")
            self.rprint(f"{Fore.RED}Removed {FG_COLOR}{removed}")
            # except FileNotFoundError:
            #     self.rprint(f"{Fore.RED}Error {FG_COLOR}{removed}")
        if not DRY_RUN:
            dset.delete_duplicates(dry_run=DRY_RUN)
        if rating != keeped_rating and rating > 0:
            self.rprint(f"  copy rating {Fore.RED}{rating}{FG_COLOR} was {keeped_rating}")
            if not DRY_RUN:
                keeped.file.rating = rating

    ##############################################

    def interactive_cleanup(
        self,
        dset: DuplicateSet,
    ) -> None:
        keeped = self.get_index(dset)
        if keeped is not None:
            for _ in dset:
                if _ is not keeped:
                    _.mark()
            dset.commit()
            self.cleanup(dset)
        else:
            self.rprint("skip")

    ##############################################

    def on_duplicate(
        self,
        dset: DuplicateSet,
        only: list[str] = None,
        same_parent: bool = False,
        **kwargs,
    ) -> None:
        """Process duplicates
        *only* is a list of suffixes
        """
        if only is not None:
            if True not in [_.suffix in only for _ in dset]:
                return
        self.rprint()
        self.rprint(Fore.GREEN + f"Found {len(dset)} identical files")
        if dset.is_same_parent:
            self.rprint(f"  {Fore.RED}same parent")
            dset.sort(sorting='name_length')
        else:
            # Fixme: ...
            dset.sort(sorting='name_length')
        for i, _ in enumerate(dset):
            BAD = False
            if 'duplicate' in str(_.parent):
                BAD = True
            if _.name.endswith('~'):
                BAD = True
            for k in range(1, 10):
                if _.stem.endswith(f'({k})'):
                    BAD = True
            color = FG_COLOR if BAD else Fore.BLUE
            self.rprint(f"  {Fore.RED}{i} {color}{_.parent}")
            self.rprint(f"      {color}{_.name} {Fore.RED}{i}")
        self.interactive_cleanup(dset, **kwargs)

    ##############################################

    def scan(
        self,
        path: Path,
        **kwargs,
    ) -> None:
        """Run rdfind and process duplicates"""
        self._reset(path)
        self.rprint(Fore.RED + f"Scan directory {path} ...")
        rdfind = Rdfind(path)
        # for duplicate_set in rdfind.to_duplicate_pool:
        for duplicate_set in rdfind.duplicate_set_it:
            self.on_duplicate(duplicate_set, **kwargs)
        self.close_log()

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
    parser.add_argument(
        '--same-parent',
        default=False,
        action='store_true',
        help="automatically remove duplicates if they lie in the same directory (keep shortest)",
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
    cleaner = Cleaner()
    cleaner.scan(path, only=only, same_parent=args.same_parent)
    # logging.info("Done")
