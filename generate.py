#!/usr/bin/env python3
"""Generate host marketplaces from one canonical TJ Agents plugin roster."""

from __future__ import annotations

import argparse
import graphlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
VERSION = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
REVISION = re.compile(rf"main|v{VERSION}|[0-9a-f]{{40}}")
RELEASE = re.compile(rf"[a-z][a-z0-9-]*@{VERSION}")
OUTPUTS = {
    "claude": ROOT / ".claude-plugin" / "marketplace.json",
    "codex": ROOT / ".agents" / "plugins" / "marketplace.json",
}
IGNORED_DIRS = {".git", ".worktrees", "node_modules", "bin", "obj", "dist"}


def validate_instruction_pairs() -> None:
    def included(path: Path) -> bool:
        return not IGNORED_DIRS.intersection(path.relative_to(ROOT).parts[:-1])

    agents = {path.parent for path in ROOT.rglob("AGENTS.md") if included(path)}
    claude = {path.parent for path in ROOT.rglob("CLAUDE.md") if included(path)}
    for directory in sorted(agents | claude):
        relative = directory.relative_to(ROOT)
        if directory not in agents:
            raise ValueError(f"{relative}/CLAUDE.md needs a sibling AGENTS.md")
        if directory not in claude:
            raise ValueError(f"{relative}/AGENTS.md needs a sibling CLAUDE.md")
        if (directory / "CLAUDE.md").read_text(encoding="utf-8").strip() != "@AGENTS.md":
            raise ValueError(f"{relative}/CLAUDE.md must contain only @AGENTS.md")


def build() -> dict[str, bytes]:
    validate_instruction_pairs()
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    if catalog["name"] != "tj-agents":
        raise ValueError("The shared marketplace identity must remain tj-agents")
    if not catalog["description"] or not catalog["owner"]:
        raise ValueError("Marketplace description and owner are required")
    plugins = catalog["plugins"]
    if not plugins:
        raise ValueError("The marketplace has no plugins")
    names: set[str] = set()
    for plugin in plugins:
        name, repository = plugin["name"], plugin["repository"]
        if not NAME.fullmatch(name) or not NAME.fullmatch(repository):
            raise ValueError(f"Invalid plugin or repository name: {plugin}")
        if name in names:
            raise ValueError(f"Duplicate plugin: {name}")
        names.add(name)
    repositories: dict[str, tuple[str | None, str]] = {}
    graph: dict[str, list[str]] = {}
    claude_entries = []
    codex_entries = []
    for plugin in plugins:
        name, repository = plugin["name"], plugin["repository"]
        revision = plugin.get("revision")
        if not revision or not REVISION.fullmatch(revision):
            raise ValueError(f"Invalid revision in {name}: {revision!r}")
        release = plugin.get("release")
        if release is not None and not RELEASE.fullmatch(release):
            raise ValueError(f"Invalid release in {name}: {release!r}")
        if release is not None and revision == "main":
            raise ValueError(f"release is not allowed with revision main: {plugin}")
        if release is not None and revision.startswith("v"):
            if revision[1:] != release.split("@", 1)[1]:
                raise ValueError(f"revision {revision!r} does not match release version in {release!r}")
        pair = (release, revision)
        if repository in repositories and repositories[repository] != pair:
            raise ValueError(f"repository {repository!r} has mismatched release/revision: {plugin}")
        repositories[repository] = pair
        requires = plugin.get("requires", [])
        if not isinstance(requires, list) or any(not isinstance(required, str) for required in requires):
            raise ValueError(f"requires must be a list of plugin names in {name}")
        for required in requires:
            if required == name:
                raise ValueError(f"Plugin cannot require itself: {name}")
            if required not in names:
                raise ValueError(f"Unknown required plugin: {required!r}")
        graph[name] = requires
        source = {
            "source": "git-subdir",
            "url": f"https://github.com/tj-agents/{repository}.git",
            "path": f"./plugins/{name}",
            "ref": revision,
        }
        claude_entries.append({"name": name, "source": source})
        codex_entries.append({
            "name": name,
            "source": source,
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        })
    try:
        graphlib.TopologicalSorter(graph).prepare()
    except graphlib.CycleError as error:
        raise ValueError("Required plugins form a cycle: " + ", ".join(dict.fromkeys(error.args[1]))) from None
    manifests = {
        "claude": {
            "name": catalog["name"],
            "description": catalog["description"],
            "owner": {"name": catalog["owner"]},
            "plugins": claude_entries,
        },
        "codex": {
            "name": catalog["name"],
            "interface": {"displayName": "TJ Agents"},
            "plugins": codex_entries,
        },
    }
    return {
        host: (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
        for host, manifest in manifests.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    for host, path in OUTPUTS.items():
        expected = outputs[host]
        if args.check:
            if not path.is_file() or path.read_bytes() != expected:
                print(f"STALE: {path.relative_to(ROOT)}")
                return 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    print(f"{'checked' if args.check else 'generated'} {len(outputs)} host marketplaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
