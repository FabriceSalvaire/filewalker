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

import logging

from filewalker.path.file import File

####################################################################################################

_module_logger = logging.getLogger(__name__)

####################################################################################################

class MimeType:

    SUFFIX_TO_CLASS = {}
    HANDLE = ()

    _logger = _module_logger.getChild("File")

    ##############################################

    @classmethod
    def from_file(cls, file_obj: File):
        suffix = file_obj.path.suffix
        try:
            subcls = cls.SUFFIX_TO_CLASS[suffix.lower()]
            return subcls(file_obj)
        except KeyError:
            raise NotImplementedError

    ##############################################

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for suffix in cls.HANDLE:
            cls.SUFFIX_TO_CLASS[suffix] = cls
            cls._logger.info(f"register {suffix} -> {cls.__name__}")

    ##############################################

    def __init__(self, file_obj: File):
        self._file = file_obj

####################################################################################################

class FileError(NameError):
    pass

####################################################################################################

class ImageMimeType(MimeType):

    HANDLE = (
        '.jpg',
        '.png',
        '.tiff',
        '.webp',
    )

    ##############################################

    def __init__(self, file_obj: File):
        super().__init__(file_obj)
        from PIL import Image, UnidentifiedImageError
        try:
            self._image = Image.open(self._file.path_str)
        except UnidentifiedImageError:
            raise FileError

    ##############################################

    @property
    def dimension(self):
        width, height = self._image.size
        return width, height, width * height
