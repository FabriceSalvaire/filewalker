# mlocate

* Package **mlocate** https://fedorahosted.org/mlocate
* https://github.com/Aetf/plocate — Locate implementation with extra filtering features, compatible with mlocate.db format.
* https://github.com/salexan2001/pymlocate — A small library for python that reads an mlocate database

## Man Pages

```
locate(1)                                                  General Commands Manual                                                  locate(1)

NAME
       locate - find files by name

SYNOPSIS
       locate [OPTION]... PATTERN...

DESCRIPTION
       locate  reads  one  or  more databases prepared by updatedb(8) and writes file names matching at least one of the PATTERNs to standard
       output, one per line.

       If --regex is not specified, PATTERNs can contain globbing characters.  If any PATTERN contains no globbing characters, locate behaves
       as if the pattern were *PATTERN*.

       By  default, locate does not check whether files found in database still exist (but it does require all parent directories to exist if
       the database was built with --require-visibility no).  locate can never report files created after the most recent update of the rele‐
       vant database.

EXIT STATUS
       locate  exits  with status 0 if any match was found or if locate was invoked with one of the --limit 0, --help, --statistics or --ver‐
       sion options.  If no match was found or a fatal error was encountered, locate exits with status 1.

       Errors encountered while reading a database are not fatal, search continues in other specified databases, if any.

OPTIONS
       -A, --all
              Print only entries that match all PATTERNs instead of requiring only one of them to match.

       -b, --basename
              Match only the base name against the specified patterns.  This is the opposite of --wholename.

       -c, --count
              Instead of writing file names on standard output, write the number of matching entries only.

       -d, --database DBPATH

              Replace the default database with DBPATH.  DBPATH is a :-separated list of database file names.  If more  than  one  --database
              option is specified, the resulting path is a concatenation of the separate paths.

              An  empty  database  file name is replaced by the default database.  A database file name - refers to the standard input.  Note
              that a database can be read from the standard input only once.

       -e, --existing
              Print only entries that refer to files existing at the time locate is run.

       -L, --follow
              When checking whether files exist (if the --existing option is specified), follow trailing symbolic links.  This causes  broken
              symbolic links to be omitted from the output.

              This is the default behavior.  The opposite can be specified using --nofollow.

       -h, --help
              Write a summary of the available options to standard output and exit successfully.

       -i, --ignore-case
              Ignore case distinctions when matching patterns.

       -l, --limit, -n LIMIT
              Exit  successfully  after  finding  LIMIT  entries.  If the --count option is specified, the resulting count is also limited to
              LIMIT.

       -m, --mmap
              Ignored, for compatibility with BSD and GNU locate.

       -P, --nofollow, -H
              When checking whether files exist (if the --existing option is specified), do not follow trailing symbolic links.  This  causes
              broken symbolic links to be reported like other files.

              This is the opposite of --follow.

       -0, --null
              Separate  the entries on output using the ASCII NUL character instead of writing each entry on a separate line.  This option is
              designed for interoperability with the --null option of GNU xargs(1).

       -S, --statistics
              Write statistics about each read database to standard output instead of searching for files and exit successfully.

       -q, --quiet
              Write no messages about errors encountered while reading and processing databases.

       -r, --regexp REGEXP
              Search for a basic regexp REGEXP.  No PATTERNs are allowed if this option is used, but this option can  be  specified  multiple
              times.

       --regex
              Interpret all PATTERNs as extended regexps.

       -s, --stdio
              Ignored, for compatibility with BSD and GNU locate.

       -V, --version
              Write information about the version and license of locate on standard output and exit successfully.

       -w, --wholename
              Match only the whole path name against the specified patterns.

              This is the default behavior.  The opposite can be specified using --basename.

EXAMPLES
       To search for a file named exactly NAME (not *NAME*), use
              locate -b '\NAME'
       Because \ is a globbing character, this disables the implicit replacement of NAME by *NAME*.

FILES
       /var/lib/mlocate/mlocate.db
              The database searched by default.

              This is the default behavior.  The opposite can be specified using --basename.

EXAMPLES
       To search for a file named exactly NAME (not *NAME*), use
              locate -b '\NAME'
       Because \ is a globbing character, this disables the implicit replacement of NAME by *NAME*.

FILES
       /var/lib/mlocate/mlocate.db
              The database searched by default.

ENVIRONMENT
       LOCATE_PATH
              Path to additional databases, added after the default database or the databases specified using the --database option.

NOTES
       The order in which the requested databases are processed is unspecified, which allows locate to reorder the database path for security
       reasons.

       locate attempts to be compatible to slocate (without the options used for creating databases) and GNU locate, in that order.  This  is
       the reason for the impractical default --follow option and for the confusing set of --regex and --regexp options.

       The  short  spelling  of the -r option is incompatible to GNU locate, where it corresponds to the --regex option.  Use the long option
       names to avoid confusion.

       The LOCATE_PATH environment variable replaces the default database in BSD and GNU locate, but it is added to other databases  in  this
       implementation and slocate.
```

```
updatedb(8)                                                System Manager's Manual                                                updatedb(8)

NAME
       updatedb - update a database for mlocate

SYNOPSIS
       updatedb [OPTION]...

DESCRIPTION
       updatedb  creates  or  updates  a  database  used by locate(1).  If the database already exists, its data is reused to avoid rereading
       directories that have not changed.

       updatedb is usually run daily by cron(8) to update the default database.

EXIT STATUS
       updatedb returns with exit status 0 on success, 1 on error.

OPTIONS
       The PRUNE_BIND_MOUNTS, PRUNEFS, PRUNENAMES and PRUNEPATHS variables, which are modified by some of  the  options,  are  documented  in
       detail in updatedb.conf(5).

       -f, --add-prunefs FS
              Add entries in white-space-separated list FS to PRUNEFS.

       -n, --add-prunenames NAMES
              Add entries in white-space-separated list NAMES to PRUNENAMES.

       -e, --add-prunepaths PATHS
              Add entries in white-space-separated list PATHS to PRUNEPATHS.

       -U, --database-root PATH
              Store  only  results  of  scanning  the file system subtree rooted at PATH to the generated database.  The whole file system is
              scanned by default.

              locate(1) outputs entries as absolute path names which don't contain symbolic links, regardless of the form of PATH.

    --debug-pruning
              Write debugging information about pruning decisions to standard error output.

       -h, --help
              Write a summary of the available options to standard output and exit successfully.

       -o, --output FILE
              Write the database to FILE instead of using the default database.

       --prune-bind-mounts FLAG
              Set PRUNE_BIND_MOUNTS to FLAG, overriding the configuration file.

       --prunefs FS
              Set PRUNEFS to FS, overriding the configuration file.

       --prunenames NAMES
              Set PRUNENAMES to NAMES, overriding the configuration file.

       --prunepaths PATHS
              Set PRUNEPATHS to PATHS, overriding the configuration file.

       -l, --require-visibility FLAG
              Set the “require file visibility before reporting it” flag in the generated database to FLAG.

              If FLAG is 0 or no, or if the database file is readable by "others" or it is not owned by slocate, locate(1) outputs the  data‐
              base  entries  even if the user running locate(1) could not have read the directory necessary to find out the file described by
              the database entry.

              If FLAG is 1 or yes (the default), locate(1) checks the permissions of parent directories of each entry before reporting it  to
              the  invoking  user.   To  make  the file existence truly hidden from other users, the database group is set to slocate and the
              database permissions prohibit reading the database by users using other means than locate(1), which is set-gid slocate.

              Note that the visibility flag is checked only if the database is owned by slocate and it is not readable by "others".

       -v, --verbose
              Output path names of files to standard output, as soon as they are found.

              Note that the visibility flag is checked only if the database is owned by slocate and it is not readable by "others".

       -v, --verbose
              Output path names of files to standard output, as soon as they are found.

       -V, --version
              Write information about the version and license of locate on standard output and exit successfully.

EXAMPLES
       To create a private mlocate database as an user other than root, run
              updatedb -l 0 -o db_file -U source_directory
       Note that all users that can read db_file can get the complete list of files in the subtree of source_directory.

FILES
       /etc/updatedb.conf
              A configuration file.  See updatedb.conf(5).

       /var/lib/mlocate/mlocate.db
              The database updated by default.

SECURITY
       Databases built with --require-visibility no allow users to find names of files and directories of other users, which they  would  not
       otherwise be able to do.

NOTES
       The  accompanying  locate(1) utility was designed to be compatible to slocate and attempts to be compatible to GNU locate where possi‐
       ble.  This is not the case for updatedb.
```

```
updatedb.conf(5)                                             File Formats Manual                                             updatedb.conf(5)

NAME
       /etc/updatedb.conf - a configuration file for updatedb(8)

DESCRIPTION
       /etc/updatedb.conf  is  a  text  file.   Blank lines are ignored.  A # character outside of a quoted string starts a comment extending
       until end of line.

       Other lines must be of the following form:
              VARIABLE = "VALUE"

       White space between tokens is ignored.  VARIABLE is an alphanumeric string which does not start with a digit.  VALUE can  contain  any
       character except for ".  No escape mechanism is supported within VALUE and there is no way to write VALUE spanning more than one line.

       Unknown VARIABLE values are considered an error.  The defined variables are:

       PRUNEFS
              A  whitespace-separated  list of file system types (as used in /etc/mtab) which should not be scanned by updatedb(8).  The file
              system type matching is case-insensitive.  By default, no file system types are skipped.

              When scanning a file system is skipped, all file systems mounted in the subtree are skipped too, even if their  type  does  not
              match any entry in PRUNEFS.

       PRUNENAMES
              A  whitespace-separated  list  of  directory  names (without paths) which should not be scanned by updatedb(8).  By default, no
              directory names are skipped.

              Note that only directories can be specified, and no pattern mechanism (e.g.  globbing) is used.

       PRUNEPATHS
              A whitespace-separated list of path names of directories which should not be scanned by updatedb(8).  Each path  name  must  be
              exactly in the form in which the directory would be reported by locate(1).

              By default, no paths are skipped.

              A  whitespace-separated  list  of  directory  names (without paths) which should not be scanned by updatedb(8).  By default, no
              directory names are skipped.

              Note that only directories can be specified, and no pattern mechanism (e.g.  globbing) is used.

       PRUNEPATHS
              A whitespace-separated list of path names of directories which should not be scanned by updatedb(8).  Each path  name  must  be
              exactly in the form in which the directory would be reported by locate(1).

              By default, no paths are skipped.

       PRUNE_BIND_MOUNTS
              One  of  the  strings 0, no, 1 or yes.  If PRUNE_BIND_MOUNTS is 1 or yes, bind mounts are not scanned by updatedb(8).  All file
              systems mounted in the subtree of a bind mount are skipped as well, even if they are not bind mounts.  As  an  exception,  bind
              mounts of a directory on itself are not skipped.

              By default, bind mounts are not skipped.

NOTES
       When  a  directory is matched by PRUNEFS, PRUNENAMES or PRUNEPATHS, updatedb(8) does not scan the contents of the directory.  The path
       of the directory itself is, however, entered in the created database.  For example, if /tmp is in PRUNEPATHS, locate(1) will not  show
       any files stored in /tmp, but it can show the /tmp directory.  This behavior differs from traditional locate implementations.

       In  some  updatedb(8) implementations PRUNEPATHS can be used to exclude non-directory files.  This is not the case in this implementa‐
       tion.

       /etc/updatedb.conf is a shell script in some implementations, which allows much more flexibility in defining the  variables.   Equiva‐
       lent functionality can be achieved by using the command-line options to updatedb(8).
```

```
mlocate.db(5)                                                File Formats Manual                                                mlocate.db(5)

NAME
       mlocate.db - a mlocate database

DESCRIPTION
       A mlocate database starts with a file header: 8 bytes for a magic number ("\0mlocate" like a C literal), 4 bytes for the configuration
       block size in big endian, 1 byte for file format version (0), 1 byte for the “require visibility” flag (0 or 1), 2 bytes padding,  and
       a NUL-terminated path name of the root of the database.

       The  header  is  followed  by  a  configuration block, included to ensure databases are not reused if some configuration changes could
       affect their contents.  The size of the configuration block in bytes is stored in the file  header.   The  configuration  block  is  a
       sequence  of  variable assignments, ordered by variable name.  Each variable assignment consists of a NUL-terminated variable name and
       an ordered list of NUL-terminated values.  The value list is terminated by one more NUL character.  The ordering used  is  defined  by
       the strcmp () function.

       Currently defined variables are:

       prune_bind_mounts
              A single entry, the value of PRUNE_BIND_MOUNTS; one of the strings 0 or 1.

       prunefs
              The value of PRUNEFS, each entry is converted to uppercase.

       prunepaths
              The value of PRUNEPATHS.

       The  rest  of the file until EOF describes directories and their contents.  Each directory starts with a header: 8 bytes for directory
       time (seconds) in big endian, 4 bytes for directory time (nanoseconds) in big endian (0 if unknown, less than 1,000,000,000), 4  bytes
       padding, and a NUL-terminated path name of the the directory.  Directory contents, a sequence of file entries sorted by name, follow.

       Directory  time is the maximum of st_ctime and st_mtime of the directory.  updatedb(8) uses the original data if the directory time in
       the database and in the file system match exactly.  Directory time equal to 0 always causes rescanning of the directory: this is  nec‐
       essary to handle directories which were being updated while building the database.

       Each file entry starts with a single byte, marking its type:

       prune_bind_mounts
              A single entry, the value of PRUNE_BIND_MOUNTS; one of the strings 0 or 1.

       prunefs
              The value of PRUNEFS, each entry is converted to uppercase.

       prunepaths
              The value of PRUNEPATHS.

       The  rest  of the file until EOF describes directories and their contents.  Each directory starts with a header: 8 bytes for directory
       time (seconds) in big endian, 4 bytes for directory time (nanoseconds) in big endian (0 if unknown, less than 1,000,000,000), 4  bytes
       padding, and a NUL-terminated path name of the the directory.  Directory contents, a sequence of file entries sorted by name, follow.

       Directory  time is the maximum of st_ctime and st_mtime of the directory.  updatedb(8) uses the original data if the directory time in
       the database and in the file system match exactly.  Directory time equal to 0 always causes rescanning of the directory: this is  nec‐
       essary to handle directories which were being updated while building the database.

       Each file entry starts with a single byte, marking its type:

       0      A non-directory file.  Followed by a NUL-terminated file (not path) name.

       1      A subdirectory.  Followed by a NUL-terminated file (not path) name.

       2      Marks the end of the current directory.

       locate(1) only reports file entries, directory names are not reported because they are reported as an entry in their parent directory.
       The only exception is the root directory of the database, which is stored in the file header.
```
