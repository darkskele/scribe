#!/bin/bash
# Builds scribe's environment, scribe, from environment.yml with micromamba or conda, replacing
# any earlier one, then installs scribe into it editable with the dependencies pyproject.toml pins.
# Safe to rerun.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

if command -v micromamba >/dev/null; then
    tool=micromamba
elif [[ -x ~/.local/bin/micromamba ]]; then
    tool=~/.local/bin/micromamba
elif command -v conda >/dev/null; then
    tool=conda
else
    echo "setup: needs micromamba or conda" >&2
    exit 1
fi

if [[ $tool == conda ]]; then
    conda env create -y -n scribe -f "$here/environment.yml"
else
    "$tool" create -y -n scribe -f "$here/environment.yml"
fi
"$tool" run -n scribe python -m pip install --no-build-isolation -e "$here"
"$tool" run -n scribe scribe --version
