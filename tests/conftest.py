from pathlib import Path

import pytest


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(
        '[sleeper]\nusername = "eli"\n\n[sources]\nurls = ["https://a.test/feed"]\n',
        encoding="utf-8",
    )
    return path
