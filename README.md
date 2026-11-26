# scribe

Takes a module from idea to published design, tracks the work the design turns into, presents the system as a site, and sets up each coding chat with exactly the context one milestone needs. One tool for every repo, nothing copied into each.

## Setup

Needs conda or micromamba.

```bash
./setup.sh
```

Builds the `scribe` environment and installs scribe into it, editable, with the dependencies `pyproject.toml` pins.

```bash
~/miniconda3/envs/scribe/bin/scribe --help
```

## Tests

```bash
~/miniconda3/envs/scribe/bin/python -m pytest
```
