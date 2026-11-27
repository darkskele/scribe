"""scribe.toml: the repo's name, the code root its docs mirror, the schema version they are written against."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from scribe import schema

FILE = "scribe.toml"
KEYS = ("repo", "code", "schema")


class ConfigError(Exception):
    """scribe.toml is missing or does not match its form. The message says which."""


@dataclass(frozen=True)
class Config:
    repo: str  # the repo's name, the prefix of its IDs
    code: str  # the code root, relative to the repo, in posix form
    schema: int


def load(root: Path) -> Config:
    path = root / FILE
    if not path.is_file():
        raise ConfigError("missing")
    try:
        raw = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"not TOML: {e}") from None

    unknown = sorted(set(raw) - set(KEYS))
    if unknown:
        raise ConfigError(f"unknown key {', '.join(unknown)}")
    missing = [k for k in KEYS if k not in raw]
    if missing:
        raise ConfigError(f"missing {', '.join(missing)}")

    repo, code, version = raw["repo"], raw["code"], raw["schema"]
    if not isinstance(repo, str) or not re.fullmatch(schema.NAME, repo):
        raise ConfigError(f"repo {repo!r} is not {schema.NAME}")
    if not isinstance(version, int) or version != schema.SCHEMA:
        raise ConfigError(f"schema {version!r}, this scribe checks schema {schema.SCHEMA}")
    if not isinstance(code, str) or Path(code).is_absolute() or ".." in Path(code).parts:
        raise ConfigError(f"code {code!r} is not a path inside the repo")
    if not (root / code).is_dir():
        raise ConfigError(f"code {code!r} is not a directory")
    return Config(repo, Path(code).as_posix(), version)
