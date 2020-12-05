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

####################################################################################################

from pathlib import Path
import json
import string

from filewalker.common.logging import setup_logging
logger = setup_logging()
logger.info("Start ...")

from filewalker.interface import rdfind
from filewalker.cleaner.DuplicateCleaner import DuplicateCleaner, DuplicatePool

####################################################################################################

def find_duplicate(path, json_pool_path):
    pool = DuplicateCleaner.find_duplicate_set(path)
    pool.write_json(json_pool_path)

####################################################################################################

def compare_duplicate_with_rdfind(json_pool_path, results_path):
    pool = DuplicatePool.new_from_json(json_pool_path)
    pool_ref = rdfind.load_to_duplicate_pool(results_path)
    print(pool == pool_ref)
    # print(pool.compare(pool_ref))

####################################################################################################

class Cleaner:

    ##############################################

    def __init__(self, json_pool_path):
        self.pool = DuplicatePool.new_from_json(json_pool_path)
        self.pool.sort()

    ##############################################

    def clean(self, callback, *args, **kwargs):
        for duplicate_set in self.pool:
            if not duplicate_set.is_singleton:
                callback(duplicate_set, *args, **kwargs)
                duplicate_set.commit()

    ##############################################

    def save(self, json_pool_path):
        self.pool.write_json(json_pool_path)

    ##############################################

    def explain(self, path):
        ROOT = "/home/..."
        def process(_):
            _ = str(_)
            if _.startswith(ROOT):
                return _[len(ROOT):]
            else:
                return _
        data = {
            process(duplicate_set.first.path): [process(_) for _ in duplicate_set.duplicated_paths]
            for duplicate_set in self.pool if duplicate_set.number_of_duplicates
        }
        with open(path, 'w', encoding="utf-8") as fh:
            json.dump(data, fh, indent=4)

    ##############################################

    # assert smallest.compare_with(_, posix=False)
    # assert smallest.compare_with(_, posix=True)
    # _.delete(dry_run=True)

####################################################################################################

def cleanup_by_stem(duplicate_set):
    if duplicate_set.is_same_parent:
        duplicate_set.sort(key=lambda duplicate: len(duplicate.path.name))
        # print([_.path.name for _ in duplicate_set])
        smallest = duplicate_set.first
        stem = smallest.path.stem
        for duplicate in duplicate_set.followings:
            if duplicate.path.name.startswith(stem):
                duplicate.mark()

def cleanup_by_directory(duplicate_set, directory):
    directory = str(directory)
    for duplicate in duplicate_set:
        # if duplicate.path.is_relative_to(directory):
        if str(duplicate.path).startswith(directory):
            duplicate.mark()
    if duplicate_set.number_of_unmarked:
        duplicate_set.commit()
    else:
        duplicate_set.rollback()

def cleanup_by_parent(duplicate_set, name):
    if duplicate_set.is_same_parent:
        return
    parents = {}
    for duplicate in duplicate_set:
        parent = duplicate.path.parent.name
        parents.setdefault(parent, [])
        parents[parent].append(duplicate)
    if name in parents and (len(parents[name]) < len(duplicate_set)):
        for duplicate in parents[name]:
            duplicate.mark()

def cleanup_by_depth(duplicate_set, excluded):
    common_parent = duplicate_set.common_parent
    if common_parent in excluded:
        return
    paths = {}
    duplicate_set.sort(key=lambda duplicate: duplicate.path.parent.relative_to(common_parent))
    for duplicate in duplicate_set.followings:
        duplicate.mark()

def count_letter(name):
    name = name.lower()
    return sum([1 for _ in name if _ in string.ascii_lowercase])

def cleanup_by_name(duplicate_set):
    if duplicate_set.is_same_parent:
        duplicate_set.sort(key=lambda duplicate: count_letter(duplicate.path.stem), reverse=True)
        for duplicate in duplicate_set.followings:
            duplicate.mark()

####################################################################################################

PATH = '/home/...'
JSON_POOL_PATH = 'results.json'

# find_duplicate(PATH, JSON_POOL_PATH)
# compare_duplicate_with_rdfind(JSON_POOL_PATH, "./results.txt")

cleaner = Cleaner(JSON_POOL_PATH)
cleaner.clean(cleanup_by_stem)
for _ in (
        "__a_trier__",
):
    cleaner.clean(cleanup_by_directory,  Path("/home/...",  _))
for _ in (
        "__a_trier__",
):
    cleaner.clean(cleanup_by_parent, _)
cleaner.clean(cleanup_by_name)
cleaner.clean(cleanup_by_depth, (
    Path("/home/..."),
))
cleaner.save('results-test.json')
cleaner.explain('explain.json')
