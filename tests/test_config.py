from pathlib import Path

import pytest

from ff_briefing.config import Config, ConfigError, load_config
from ff_briefing.errors import BriefingError


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_file_yields_config_with_username_and_source_urls(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        '[sleeper]\nusername = "eli"\n\n[sources]\nurls = ["https://a.test/x", "https://b.test/y"]\n',
    )

    assert load_config(path) == Config(
        sleeper_username="eli", source_urls=["https://a.test/x", "https://b.test/y"]
    )


def test_unknown_keys_are_ignored(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        '[sleeper]\nusername = "eli"\nextra = 1\n\n[sources]\nurls = []\n\n[future]\nx = 2\n',
    )

    assert load_config(path).source_urls == []


def test_nonexistent_file_error_names_the_path(tmp_path: Path) -> None:
    missing = tmp_path / "nope.toml"

    with pytest.raises(ConfigError, match="nope.toml"):
        load_config(missing)


def test_invalid_toml_error_names_the_file(tmp_path: Path) -> None:
    path = write(tmp_path, "[sleeper\nusername = ")

    with pytest.raises(ConfigError, match="config.toml"):
        load_config(path)


def test_missing_username_error_names_the_key(tmp_path: Path) -> None:
    path = write(tmp_path, "[sleeper]\n\n[sources]\nurls = []\n")

    with pytest.raises(ConfigError, match="sleeper.username"):
        load_config(path)


def test_empty_username_error_names_the_key(tmp_path: Path) -> None:
    path = write(tmp_path, '[sleeper]\nusername = ""\n\n[sources]\nurls = []\n')

    with pytest.raises(ConfigError, match="sleeper.username"):
        load_config(path)


@pytest.mark.parametrize("urls", ['"https://a.test"', "[1, 2]"])
def test_source_urls_that_are_not_a_list_of_strings_error_names_the_key(
    tmp_path: Path, urls: str
) -> None:
    path = write(tmp_path, f'[sleeper]\nusername = "eli"\n\n[sources]\nurls = {urls}\n')

    with pytest.raises(ConfigError, match="sources.urls"):
        load_config(path)


def test_missing_source_urls_error_names_the_key(tmp_path: Path) -> None:
    path = write(tmp_path, '[sleeper]\nusername = "eli"\n')

    with pytest.raises(ConfigError, match="sources.urls"):
        load_config(path)


def test_config_error_is_a_briefing_error() -> None:
    assert issubclass(ConfigError, BriefingError)
