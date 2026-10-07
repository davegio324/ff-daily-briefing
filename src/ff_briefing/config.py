import tomllib
from dataclasses import dataclass
from pathlib import Path

from ff_briefing.errors import BriefingError


class ConfigError(BriefingError):
    pass


@dataclass(frozen=True)
class Config:
    sleeper_username: str
    source_urls: list[str]


def load_config(path: Path) -> Config:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigError(f"cannot read config file {path}: {exc.strerror}") from exc
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}") from exc

    username = _section(data, "sleeper").get("username")
    if not isinstance(username, str) or not username:
        raise ConfigError(f"{path}: sleeper.username must be a non-empty string")

    urls = _section(data, "sources").get("urls")
    if not isinstance(urls, list) or not all(isinstance(u, str) for u in urls):
        raise ConfigError(f"{path}: sources.urls must be a list of strings")

    return Config(sleeper_username=username, source_urls=list(urls))


def _section(data: dict[str, object], name: str) -> dict[str, object]:
    section = data.get(name)
    return section if isinstance(section, dict) else {}
