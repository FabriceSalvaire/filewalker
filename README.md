# Some File System Tools implemented in Python

## Purposes

* provides tools to scan a file system, to find duplicated file on disk, to implement a mlocate like tool
* highly and easily customisable
* not so optimised, should be able to run with a low IO / memory footprint
  i.e. never freeze a computer like do many desktop file indexers (Baloo, etc.)
  i.e. more sleeping than thread spanning
* thus could be implemented with asyncio or better in Go but ... cf. infra

## Features

* a module to get mounted file systems on Linux
* a base module to scan a file system
* an improved OO File API to get: stat, allocated size on disk, sha1 checksum; a method to check if two files are identical ...
* a module to find duplicated files on disk, inspired by the C++ command line tool [rdfind](https://github.com/pauldreik/rdfind)
  It also implements a **rdfind** `results.txt` loader and can cross-check it.
  Dump and load a JSON result file.
