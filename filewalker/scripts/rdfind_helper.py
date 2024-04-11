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
from typing import Optional
import argparse
import logging
import os
# from pprint import pprint

from colorama import Fore
import colorama

from filewalker.cleaner.DuplicateFinder import DuplicateFinder
from filewalker.cleaner.DuplicateSet import DuplicateSet, Duplicate
from filewalker.common.logging import setup_logging
from filewalker.path.file import File
from filewalker.interface.rdfind import Rdfind

####################################################################################################

colorama.init()   # autoreset=True

####################################################################################################

logger = None

DRY_RUN = False

# FG_COLOR = Fore.BLACK
FG_COLOR = Fore.WHITE

####################################################################################################

class DuplicateCleaner:

    ##############################################

    def __init__(self, cleaner : 'Cleaner', dset: DuplicateSet) -> None:
        self._cleaner = cleaner
        self._dset = dset
        self._removed_counter = 0

    ##############################################

    def log(self, message: str) -> None:
        self._cleaner.log(message)

    ##############################################

    def rprint(self, *args) -> None:
        self._cleaner.rprint(*args)

    ##############################################

    def rename(self, file: File) -> None:
        """Interactive rename"""
        self.rprint(f"{Fore.RED}Rename: {Fore.BLUE}{file}")
        rc = input()
        if rc:
            file.rename(rc, rebuild=True)
            self.rprint(f"Renamed: {FG_COLOR}{rc}")

    ##############################################

    def cleanup(
        self,
        move: Optional[str] = None,
    ) -> None:
        # keeped = self._dset.first
        keeped = self._dset.unmarked

        # Sanity checks
        if len(keeped) > 1:
            raise NameError(f"More than one keeped files {keeped}")
        self._dset.check()
        self._dset.check_is_duplicate()
        keeped = keeped.pop()
        to_remove = set(self._dset) - set((keeped,))
        if len(to_remove) == self._dset.number_of_files:
            raise NameError("All files will be removed")

        keeped_rating = keeped.file.rating
        self.log(f"keeped    {keeped.path} *{keeped_rating}")
        self.rprint(f"{Fore.GREEN}Keep    {Fore.BLUE}{keeped}")
        rating = keeped_rating

        for _ in self._dset.duplicates:
            removed = _.path
            # self.rprint(f'{rating} vs {keeped_rating}')
            removed_rating = _.file.rating
            rating = max(removed_rating, rating)
            # try:
            self.log(f"  removed {removed} *{removed_rating}")
            self.rprint(f"{Fore.RED}Removed {FG_COLOR}{removed}")
            # except FileNotFoundError:
            #     self.rprint(f"{Fore.RED}Error {FG_COLOR}{removed}")
            self._removed_counter += 1
        if not DRY_RUN:
            if move:
                self._dset.move_duplicates(move, dry_run=DRY_RUN)
            else:
                self._dset.delete_duplicates(dry_run=DRY_RUN)
        if rating != keeped_rating and rating > 0:
            self.rprint(f"  copy rating {Fore.RED}{rating}{FG_COLOR} was {keeped_rating}")
            if not DRY_RUN:
                keeped.file.rating = rating

    ##############################################

    def print_intro(self) -> None:
        self.rprint()
        self.rprint(Fore.GREEN + '\u2500'*50)
        self.rprint(Fore.GREEN + f"Found {len(self._dset)} identical files")
        if self._dset.is_same_parent:
            self.rprint(f"  {Fore.RED}same parent")

    ##############################################

    def print_duplicates(self) -> None:
        for i, _ in enumerate(self._dset.pendings):
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

    ##############################################

    def on_same_parent(self, **kwargs) -> None:
        self.print_intro()
        self._dset.sort(sorting='name_length')
        for _ in self._dset.followings:
            _.mark()
        self._dset.commit()
        self.cleanup(**kwargs)

    ##############################################

    def get_index(self) -> Duplicate:
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
                    _ = self._dset[int(rc[1:])]
                    self.rename(_)
                else:
                    return self._dset[int(rc)]
            except (ValueError, IndexError):
                self.rprint(Fore.RED + "Bad index")

    ##############################################

    def interactive_cleanup(self, **kwargs) -> None:
        self.print_intro()
        reverse = False
        if self._dset.is_same_parent:
            sorting = 'name_length'
        else:
            sorting = 'parent_length'
            reverse = True
        self._dset.sort(sorting=sorting, reverse=reverse)
        self.print_duplicates()
        keeped = self.get_index()
        if keeped is not None:
            for _ in self._dset:
                if _ is not keeped:
                    _.mark()
            self._dset.commit()
            self.cleanup(**kwargs)
        else:
            self.rprint("skip")

    ##############################################

    def process(
        self,
        only: list[str] = None,
        same_parent: bool = False,
        **kwargs,
    ) -> int:
        """Process duplicates
        *only* is a list of suffixes
        """
        if only is not None:
            if True not in [_.suffix in only for _ in self._dset]:
                return 0
        if same_parent:
            if self._dset.is_same_parent:
                self.on_same_parent(**kwargs)
        else:
            self.interactive_cleanup(**kwargs)
        return self._removed_counter

####################################################################################################

class Cleaner:

    ##############################################

    def __init__(self, no_log: bool = False) -> None:
        # self._reset()
        self._path = None
        self._log = None
        self._no_log = bool(no_log)

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
        if not self._no_log:
            self.open_log()
            self._log.write(message + os.linesep)
            self._log.flush()

    ##############################################

    def rprint(self, *args) -> None:
        print(*args, FG_COLOR)

    ##############################################

    def scan(
        self,
        path: Path,
        use_rdfind: bool = False,
        **kwargs,
    ) -> None:
        """Run rdfind and process duplicates"""
        self._reset(path)
        self.rprint(Fore.RED + f"Scan directory {path} ...")
        if use_rdfind:
            rdfind = Rdfind(path)
            it = rdfind.duplicate_set_it
            # it = rdfind.to_duplicate_pool
        else:
            pool = DuplicateFinder.find_duplicate_set(path)
            it = pool
        removed_counter = 0
        for dset in it:
            _ = DuplicateCleaner(self, dset)
            removed_counter += _.process(**kwargs)
        self.rprint()
        self.rprint(Fore.RED + '\u2500'*50)
        self.rprint(Fore.RED + f"Removed {removed_counter} files")
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
    parser.add_argument(
        '--no-log',
        default=False,
        action='store_true',
        help="",
    )
    parser.add_argument(
        '--no-rdfind',
        default=False,
        action='store_true',
        help="",
    )
    parser.add_argument(
        '--move',
        default=None,
        help="Move to directory",
    )
    args = parser.parse_args()

    level = logging.WARNING
    # level = logging.DEBUG
    logger = setup_logging(level=level)
    logger.info("Start ...")

    if args.white:
        global FG_COLOR
        FG_COLOR = Fore.WHITE

    if args.dry_run:
        global DRY_RUN
        DRY_RUN = True
        print(f"Set to dry run")

    only = None
    if args.only:
        only = args.only.split(',')
        print(f"only = {only}")

    path = Path(args.path).resolve()

    cleaner = Cleaner(no_log=args.no_log)
    cleaner.scan(
        path,
        only=only,
        same_parent=args.same_parent,
        use_rdfind=not args.no_rdfind,
        move=args.move,
    )
