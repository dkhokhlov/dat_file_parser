# DAT file parser
- parses DAT files produced by Fab metrology Probers.
- outputs parsed data in JSON fomat.
```
Usage: dat_file_parser [OPTIONS]

  DAT file parser: parses DAT files produced by Fab metrology Probers, outputs
  parsed data in JSON fomat.

Options:
  --version       Show the version and exit.
  --in FILENAME   Input file. Default: <stdin>
  --out FILENAME  Output JSON file. Default: <stdout>
  --help          Show this message and exit.
```

# To run docker container
```
  ./mk.docker
  ./run.docker < test/data.dat > test/data.json
```

# To run py file
```
  ./mk.env
  ./run --in test/data.dat --out test/data.json
```


# Conda dependencies
```
channels:
  - defaults
dependencies:
  - click
  - pip
  - grok
```
