# tidepool

A tiny log viewer for your terminal

tidepool reads plain-text log files and prints them in a clean, readable way.
It has no dependencies beyond the Python standard library.

## Install

```
pip install .
```

Python 3.8 or newer is required.

## Usage

View a whole file:

```
tidepool view app.log
```

View only the last 20 lines:

```
tidepool view app.log --lines 20
```

You can also run it as a module:

```
python -m tidepool view app.log
```

## Development

Run the tests from the repository root:

```
python -m unittest discover -s tests
```

## License

MIT
