# xpld-assembler

This is the assembler for the [XPLD project](https://github.com/friol/xpld-runtime).<br/>
An assembler reads a source file and outputs a binary that you can then load in the computer.<br/>

You need Python 3.7 or better to use this one.

Syntax:

```
python .\xpld.assembler.py [source file.xpld] [destination file.bin]
```

In the examples directory you can find (guess what) three examples:

- kernal.xpld: it's the kernal (aka "BIOS") file that XPLD uses at boot
- aoc01.xpld: it's a program that solves Advent of Code's problem 1/2020 (Advent of Code is a well known programming contest)
- maze.xpld: a simple program that draws a random "maze" with "\" and "/" characters
