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

__all__ = ["find_nth"]

####################################################################################################

def find_nth(text: str, pattern: str, n: int) -> int:
    start = text.find(pattern)
    while start >= 0 and n > 1:
        start = text.find(pattern, start + len(pattern))
        n -= 1
    return start
