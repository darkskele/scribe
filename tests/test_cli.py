import pytest

from scribe import __version__
from scribe.cli import main


def test_help_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as exit:
        main(["--help"])
    assert exit.value.code == 0
    assert "usage: scribe" in capsys.readouterr().out


def test_version_names_the_package(capsys):
    with pytest.raises(SystemExit) as exit:
        main(["--version"])
    assert exit.value.code == 0
    assert capsys.readouterr().out.strip() == f"scribe {__version__}"
