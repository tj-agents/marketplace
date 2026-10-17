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
        if not isinstance(plugin, dict):
            raise ValueError(f"Plugin entries must be objects: {plugin!r}")
        unknown = set(plugin) - {"name", "repository", "requires"}
        if unknown:
            raise ValueError(f"Unknown fields in plugin entry: {sorted(unknown)}")
        if "name" not in plugin or "repository" not in plugin:
            raise ValueError("Plugin entries require name and repository")
        name, repository = plugin["name"], plugin["repository"]
        if not isinstance(name, str) or not NAME.fullmatch(name) or not isinstance(repository, str) or not NAME.fullmatch(repository):
            raise ValueError(f"Invalid plugin or repository name: {plugin}")
        if name in names:
            raise ValueError(f"Duplicate plugin: {name}")
        names.add(name)
    graph: dict[str, list[str]] = {}
    claude_entries = []
    codex_entries = []
    for plugin in plugins:
        name, repository = plugin["name"], plugin["repository"]
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
            "ref": "main",
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
        raise ValueError("Required plugins form a cycle: " + " -> ".join(error.args[1])) from None
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
