# Stat

st_mode
  File mode: file type and file mode bits (permissions).
st_ino
  Platform dependent, but if non-zero, uniquely identifies the file for a given value of st_dev. Typically:
  the inode number on Unix,
  the file index on Windows
st_dev
  Identifier of the device on which this file resides.
st_nlink
  Number of hard links.
st_uid
  User identifier of the file owner.
st_gid
 Group identifier of the file owner.
st_size
  Size of the file in bytes, if it is a regular file or a symbolic link.
  The size of a symbolic link is the length of the pathname it contains, without a terminating null byte.
st_atime
  Time of most recent access expressed in seconds.
st_mtime
  Time of most recent content modification expressed in seconds.
st_ctime
  Platform dependent:
    the time of most recent metadata change on Unix,
    the time of creation on Windows, expressed in seconds.
st_atime_ns
  Time of most recent access expressed in nanoseconds as an integer.
st_mtime_ns
  Time of most recent content modification expressed in nanoseconds as an integer.
st_ctime_ns
  Platform dependent:
    the time of most recent metadata change on Unix,
    the time of creation on Windows, expressed in nanoseconds as an integer.

On some Unix systems (such as Linux), the following attributes may also be available:
st_blocks
  Number of 512-byte blocks allocated for file. This may be smaller than st_size/512 when the file has holes.
st_blksize
  “Preferred” blocksize for efficient file system I/O. Writing to a file in smaller chunks may cause an inefficient read-modify-rewrite.
st_rdev
  Type of device if an inode device.
st_flags
  User defined flags for file.

On Mac OS systems, the following attributes may also be available:
st_rsize
  Real size of the file.
st_creator
  Creator of the file.
st_type
  File type.

On Windows systems, the following attributes are also available:
st_file_attributes
 Windows file attributes: dwFileAttributes member of the BY_HANDLE_FILE_INFORMATION structure returned by GetFileInformationByHandle().
st_reparse_tag
  When st_file_attributes has the FILE_ATTRIBUTE_REPARSE_POINT set, this field contains the tag identifying the type of reparse point.
