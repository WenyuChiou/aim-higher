# notecat

notecat is a tiny command line tool that prints your notes to the terminal.
It is meant for people who keep their notes in plain text files and want a
quick way to look at them without opening an editor.

## Installation

notecat has no dependencies. Copy the `notecat/` folder next to your scripts,
or run it straight from a checkout of this repository.

## Usage

    python -m notecat NOTES.txt

Each non-empty line of the file is treated as one note. Notes are printed in
the order they appear in the file.

### Options

- `--number` prefixes every note with its position, starting at 1.
- `--upper` prints the notes in upper case.

### Examples

    python -m notecat todo.txt
    python -m notecat --number todo.txt

## Note format

A note is a single line of text. Blank lines are skipped, and leading and
trailing spaces are removed before a note is printed. Lines that start with
a hash sign are comments and are never printed.

## Delivery guarantees

notecat reads the whole file once and prints the notes on standard output.
If you pipe the output into another program, that program will receive
exactly the lines you see on screen, one note per line.

## Running the tests

    python -m unittest discover -s tests

## Exit codes

- 0: the notes were printed.
- 2: the file could not be opened.

## License

MIT. Do whatever you like, but please keep the copyright notice.
