# Tools to find duplicated files on disk

## rdfind

* https://github.com/pauldreik/rdfind
* https://rdfind.pauldreik.se

**Algorithm**

Rdfind uses the following algorithm. If N is the number of files to search through, the effort
required is in worst case O(Nlog(N)). Because it sorts files on inodes prior to disk reading, it is
quite fast. It also only reads from disk when it is needed.

* Loop over each argument on the command line. Assign each argument a priority number, in increasing order.
* For each argument, list the directory contents recursively and assign it to the file list. Assign a directory depth number, starting at 0 for every argument.
* If the input argument is a file, add it to the file list.
* Loop over the list, and find out the sizes of all files.
* If flag -removeidentinode true: Remove items from the list which already are added, based on the combination of inode and device number. A group of files that are hardlinked to the same file are collapsed to one entry. Also see the comment on hardlinks under ”caveats below”!
* Sort files on size. Remove files from the list, which have unique sizes.
* Sort on device and inode(speeds up file reading). Read a few bytes from the beginning of each file (first bytes).
* Remove files from list that have the same size but different first bytes.
* Sort on device and inode(speeds up file reading). Read a few bytes from the end of each file (last bytes).
* Remove files from list that have the same size but different last bytes.
* Sort on device and inode(speeds up file reading). Perform a checksum calculation for each file.
* Only keep files on the list with the same size and checksum. These are duplicates.
* Sort list on size, priority number, and depth. The first file for every set of duplicates is considered to be the original.
* If flag ”-makeresultsfile true”, then print results file (default).
* If flag ”-deleteduplicates true”, then delete (unlink) duplicate files. Exit.
* If flag ”-makesymlinks true”, then replace duplicates with a symbolic link to the original. Exit.
* If flag ”-makehardlinks true”, then replace duplicates with a hard link to the original. Exit.

## fdupes

* https://github.com/adrianlopezroche/fdupes

It uses the following methods to determine duplicate files:

* Comparing partial md5sum signatures
* Comparing full md5sum signatures
* byte-by-byte comparison verification

## dupeGuru

## FSlint

