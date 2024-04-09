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

# Fixme: purpose ???

"""Linux tools

see also https://psutil.readthedocs.io/en/latest/#psutil.disk_partitions

* /usr/bin/mount
* /proc/partitions
* /proc/mounts -> /proc/self/mounts   see PROC(5) use fstab format

"""

####################################################################################################

# from os import PathLike
# import subprocess
from pathlib import Path
from typing import AnyStr, Iterator, Union

####################################################################################################

class MountPoint:

    ##############################################

    def __init__(self, mount_point: str, device: str, type_: str) -> None:
        self._mount_point = mount_point
        self._device = device
        self._type = type_

    ##############################################

    @property
    def mount_point(self) -> str:
        return self._mount_point

    @property
    def device(self) -> str:
        return self._device

    @property
    def type(self) -> str:
        return self._type

    def __str__(self) -> str:
        return f"{self._mount_point} -> {self._device} {self._type}"

####################################################################################################

class MountPoints:

    # MOUNT_COMMAND = ('/usr/bin/mount')
    PROC_MOUNTS = ('/proc/self/mounts')

    SYSTEM_TYPES = (
        'autofs',
        'bpf',
        'cgroup2',
        'configfs',
        'debugfs',
        'devpts',
        'devtmpfs',
        'efivarfs',
        'fuse.gvfsd-fuse',
        'fusectl',
        'hugetlbfs',
        'mqueue',
        'proc',
        'pstore',
        'rpc_pipefs',
        'securityfs',
        'selinuxfs',
        'sysfs',
        'tmpfs',
        'tracefs',
    )

    ##############################################

    def __init__(self) -> None:
        self._mounts = []
        self._read_mount_points()
        self._map = {_.mount_point: _ for _ in self._mounts}

    ##############################################

    def _read_mount_points(self) -> None:

        # process = subprocess.run(self.MOUNT_COMMAND, capture_output=True)
        # for line in process.stdout.decode('utf-8').splitlines():
        #     device, _, mount_point, _, type_, mount_options = line.split(' ')
        #     if type_ not in self.SYSTEM_TYPES:
        #         mount = MountPoint(mount_point, device, type_)
        #         self._mounts.append(mount)

        with open(self.PROC_MOUNTS) as fh:
            for line in fh:
                device, mount_point, type_, mount_options, _, _ = line.split(' ')
                if type_ not in self.SYSTEM_TYPES:
                    mount = MountPoint(mount_point, device, type_)
                    self._mounts.append(mount)

    ##############################################

    def __len__(self) -> int:
        return len(self._mounts)

    def __iter__(self) -> Iterator[MountPoint]:
        return iter(self._mounts)

    def __getitem__(self, mount_point: str) -> MountPoint:
        return self._map[mount_point]

    ##############################################

    # def is_mount(self, path: Union[AnyStr, PathLike[AnyStr]]) -> bool:
    def is_mount(self, path: Union[AnyStr, Path]) -> bool:
        return str(path) in self._map
