from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ff_briefing.errors import BriefingError


class MissingInputError(BriefingError):
    pass


@dataclass(frozen=True)
class RunDir:
    path: Path

    @property
    def sleeper_json(self) -> Path:
        return self.path / "sleeper.json"

    @property
    def sources_json(self) -> Path:
        return self.path / "sources.json"

    @property
    def briefing_md(self) -> Path:
        return self.path / "briefing.md"

    @property
    def briefing_html(self) -> Path:
        return self.path / "briefing.html"

    def require(self, file: Path, produced_by: str) -> Path:
        if not file.exists():
            raise MissingInputError(
                f"missing input {file.name} in {self.path}; run the {produced_by} stage first"
            )
        return file


def run_dir_for(data_dir: Path, day: date) -> RunDir:
    path = data_dir / day.isoformat()
    path.mkdir(parents=True, exist_ok=True)
    return RunDir(path)
