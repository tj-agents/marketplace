#!/usr/bin/env python3
"""Check that every generic plugin's pinned source names no specific profile.

A specific profile ("profile": "specific" in plugins.json) holds everything particular
to one organization. A generic plugin must stay usable by anyone, so its source
repository must not name a specific profile anywhere in its tracked text, at the
revision this marketplace pins. The specific repository itself is private and is never
fetched; only generic repositories are checked.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import tarfile
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
HISTORY_DIRS = {"plans", "reviews", "plugins"}

type Plugin = dict[str, Any]


@dataclass(frozen=True, slots=True)
class Violation:
    repository: str
    path: str
    line: int
    name: str
    text: str


def load_roster(root: Path = ROOT) -> dict[str, Any]:
    content = (root / "plugins.json").read_text(encoding="utf-8")
    roster: dict[str, Any] = json.loads(content)
    return roster


def specific_profile_names(plugins: Iterable[Plugin]) -> list[str]:
    return sorted(
        {plugin["name"] for plugin in plugins if plugin.get("profile") == "specific"}
    )


def generic_repositories(plugins: Iterable[Plugin]) -> dict[str, str]:
    """Map each repository hosting only generic entries to its pinned revision.

    A repository with any specific entry is excluded entirely; it is never fetched.
    """
    profiles_by_repository: dict[str, set[object]] = {}
    revision_by_repository: dict[str, str] = {}
    for plugin in plugins:
        repository = plugin["repository"]
        profiles_by_repository.setdefault(repository, set()).add(plugin.get("profile"))
        revision_by_repository[repository] = plugin["revision"]
    return {
        repository: revision_by_repository[repository]
        for repository, profiles in profiles_by_repository.items()
        if profiles == {"generic"}
    }


def marketplace_source_id(root: Path = ROOT) -> str:
    """Return this marketplace's own owner/repository identity from its git remote."""
    url = subprocess.run(
        ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    path = urlparse(url).path if "://" in url else url.split(":", 1)[-1]
    return path.removeprefix("/").removesuffix(".git")


def is_history_path(path: str) -> bool:
    return PurePosixPath(path).parts[0] in HISTORY_DIRS


def is_catalog_generated(content: bytes, marketplace_source: str) -> bool:
    """True when content records this marketplace as its own catalog source."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False
    return isinstance(data, dict) and data.get("repository") == marketplace_source


def find_matches(name: str, text: str) -> list[tuple[int, str]]:
    pattern = re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
    return [
        (number, line.strip())
        for number, line in enumerate(text.splitlines(), start=1)
        if pattern.search(line)
    ]


def scan_tree(
    repository: str, tree: Path, specific_names: Sequence[str], marketplace_source: str
) -> list[Violation]:
    violations: list[Violation] = []
    for path in sorted(tree.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(tree).as_posix()
        if is_history_path(relative):
            continue
        content = path.read_bytes()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if is_catalog_generated(content, marketplace_source):
            continue
        for name in specific_names:
            violations.extend(
                Violation(repository, relative, number, name, line)
                for number, line in find_matches(name, text)
            )
    return violations


def fetch_tree(url: str, revision: str, workdir: Path) -> Path:
    """Shallow-fetch ``revision`` from ``url``; extract its tree under ``workdir``."""
    git_dir = workdir / "repo"
    tree_dir = workdir / "tree"
    subprocess.run(["git", "init", "-q", str(git_dir)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(git_dir), "fetch", "--depth", "1", url, revision],
        check=True,
        capture_output=True,
    )
    archive = subprocess.run(
        ["git", "-C", str(git_dir), "archive", "--format=tar", "FETCH_HEAD"],
        check=True,
        capture_output=True,
    ).stdout
    tree_dir.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree_dir, filter="data")
    return tree_dir


def check_repository(
    repository: str,
    revision: str,
    specific_names: Sequence[str],
    marketplace_source: str,
) -> list[Violation]:
    url = f"https://github.com/tj-agents/{repository}.git"
    with tempfile.TemporaryDirectory() as workdir:
        tree = fetch_tree(url, revision, Path(workdir))
        return scan_tree(repository, tree, specific_names, marketplace_source)


def main() -> int:
    roster = load_roster()
    plugins = roster["plugins"]
    names = specific_profile_names(plugins)
    if not names:
        print("No specific profiles are labelled; nothing to check")
        return 0
    marketplace_source = marketplace_source_id()
    repositories = generic_repositories(plugins)
    violations: list[Violation] = []
    for repository, revision in sorted(repositories.items()):
        print(f"Scanning {repository}@{revision} for {', '.join(names)}...")
        violations.extend(
            check_repository(repository, revision, names, marketplace_source)
        )
    if violations:
        print(f"Found {len(violations)} specific-profile mention(s):")
        for violation in violations:
            print(
                f"{violation.repository}:{violation.path}:{violation.line}: "
                f"{violation.name!r} - {violation.text}"
            )
        return 1
    print(f"No specific-profile mentions found across {len(repositories)} repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
