#!/usr/bin/env python3
"""Generate host marketplaces from one canonical TJ Agents plugin roster.

Each plugin's dependencies are read from its own `.claude-plugin/plugin.json` at the revision the roster
pins, so the catalog always declares what the pinned plugin itself requires.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from enum import StrEnum
import graphlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
OUTPUTS = {
    "claude": ROOT / ".claude-plugin" / "marketplace.json",
    "codex": ROOT / ".agents" / "plugins" / "marketplace.json",
}
IGNORED_DIRS = {".git", ".worktrees", "node_modules", "bin", "obj", "dist"}
MARKETPLACE = "tj-agents"
GIT_TIMEOUT_SECONDS = 120

type DependencyReader = Callable[[str, str, Sequence[str]], Mapping[str, list[str]]]


class Kind(StrEnum):
    SHARED = "shared"
    PROFILE = "profile"
    ORGANIZATION = "organization"


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


def _git(directory: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(directory), *arguments],
        capture_output=True, timeout=GIT_TIMEOUT_SECONDS, check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise ValueError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def manifest_dependency_names(document: object, name: str, repository: str) -> list[str]:
    if not isinstance(document, dict) or document.get("name") != name:
        raise ValueError(f"tj-agents/{repository} plugins/{name}/.claude-plugin/plugin.json must name {name}")
    dependencies = document.get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ValueError(f"{name} manifest dependencies must be a list")
    names = []
    for dependency in dependencies:
        if not isinstance(dependency, str):
            raise ValueError(f"{name} manifest dependency must be a plugin identity: {dependency!r}")
        plugin, _, marketplace = dependency.partition("@")
        if marketplace not in ("", MARKETPLACE):
            raise ValueError(f"{name} depends on {dependency}, which is outside the {MARKETPLACE} marketplace")
        if not NAME.fullmatch(plugin) or dependency.endswith("@"):
            raise ValueError(f"{name} manifest dependency is not a plugin identity: {dependency!r}")
        if plugin in names:
            raise ValueError(f"{name} manifest repeats dependency: {plugin}")
        names.append(plugin)
    return names


def read_manifest_dependencies(repository: str, revision: str, names: Sequence[str]) -> dict[str, list[str]]:
    """Return each named plugin's declared dependencies at one pinned producer revision."""
    with tempfile.TemporaryDirectory(prefix="tj-agents-marketplace-") as directory:
        root = Path(directory)
        _git(root, "init", "--quiet", "--bare")
        _git(root, "remote", "add", "origin", f"https://github.com/tj-agents/{repository}.git")
        _git(root, "fetch", "--quiet", "--depth=1", "--filter=blob:none", "origin", revision)
        found = {}
        for name in names:
            path = f"plugins/{name}/.claude-plugin/plugin.json"
            try:
                document = json.loads(_git(root, "cat-file", "blob", f"FETCH_HEAD:{path}").decode("utf-8-sig"))
                dependencies = manifest_dependency_names(document, name, repository)
            except ValueError as error:
                raise ValueError(f"tj-agents/{repository}@{revision} {path}: {error}") from error
            found[name] = dependencies
    return found


def declared_dependencies(plugins: Sequence[Mapping[str, str]], reader: DependencyReader) -> dict[str, list[str]]:
    pins: dict[tuple[str, str], list[str]] = {}
    for plugin in plugins:
        pins.setdefault((plugin["repository"], plugin["revision"]), []).append(plugin["name"])
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = pool.map(lambda pin: reader(pin[0], pin[1], pins[pin]), list(pins))
        found: dict[str, list[str]] = {}
        for result in results:
            found.update(result)
    return found


def build(reader: DependencyReader = read_manifest_dependencies) -> dict[str, bytes]:
    validate_instruction_pairs()
    roster = json.loads((ROOT / "plugins.json").read_text(encoding="utf-8"))
    if roster["name"] != "tj-agents":
        raise ValueError("The shared marketplace identity must remain tj-agents")
    if not roster["description"] or not roster["owner"]:
        raise ValueError("Marketplace description and owner are required")
    plugins = roster["plugins"]
    if not plugins:
        raise ValueError("The marketplace has no plugins")
    names: set[str] = set()
    for plugin in plugins:
        if not isinstance(plugin, dict):
            raise ValueError(f"Plugin entries must be objects: {plugin!r}")
        unknown = set(plugin) - {"name", "repository", "revision", "kind", "extends"}
        if unknown:
            raise ValueError(f"Unknown fields in plugin entry: {sorted(unknown)}")
        if "name" not in plugin or "repository" not in plugin or "revision" not in plugin:
            raise ValueError("Plugin entries require name, repository and revision")
        name, repository = plugin["name"], plugin["repository"]
        if not isinstance(name, str) or not NAME.fullmatch(name) or not isinstance(repository, str) or not NAME.fullmatch(repository):
            raise ValueError(f"Invalid plugin or repository name: {plugin}")
        if name in names:
            raise ValueError(f"Duplicate plugin: {name}")
        names.add(name)
    for plugin in plugins:
        revision = plugin["revision"]
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError(f"Invalid immutable producer revision: {plugin['name']}")
    by_name = {plugin["name"]: plugin for plugin in plugins}
    for plugin in plugins:
        name = plugin["name"]
        if plugin.get("kind") not in Kind:
            raise ValueError(f"Plugin kind must be one of {', '.join(Kind)}: {name}")
        extends = plugin.get("extends")
        if plugin["kind"] != Kind.ORGANIZATION:
            if extends is not None:
                raise ValueError(f"Only an organization can use extends: {name}")
            continue
        if not isinstance(extends, str) or by_name.get(extends, {}).get("kind") != Kind.PROFILE:
            raise ValueError(f"Organization {name} must extend a profile")
    for repository in sorted({plugin["repository"] for plugin in plugins}):
        if len({plugin["revision"] for plugin in plugins if plugin["repository"] == repository}) != 1:
            raise ValueError(f"Every {repository} entry must use the same immutable revision")
    dependencies = declared_dependencies(plugins, reader)
    for plugin in plugins:
        if plugin["kind"] == Kind.ORGANIZATION and plugin["extends"] not in dependencies[plugin["name"]]:
            raise ValueError(f"Organization {plugin['name']} must depend on {plugin['extends']}, the profile it extends")
    graph: dict[str, list[str]] = {}
    claude_entries = []
    codex_entries = []
    for plugin in plugins:
        name, repository = plugin["name"], plugin["repository"]
        requires = dependencies[name]
        for required in requires:
            if required == name:
                raise ValueError(f"Plugin cannot require itself: {name}")
            if required not in names:
                raise ValueError(f"{name} depends on {required!r}, which is not in the roster")
        graph[name] = requires
        source = {
            "source": "git-subdir",
            "url": f"https://github.com/tj-agents/{repository}.git",
            "path": f"./plugins/{name}",
            "sha": plugin["revision"],
        }
        claude_entry = {"name": name, "source": source}
        if requires:
            claude_entry["dependencies"] = requires
        claude_entries.append(claude_entry)
        codex_entries.append({
            "name": name,
            "source": source,
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        })
    try:
        graphlib.TopologicalSorter(graph).prepare()
    except graphlib.CycleError as error:
        raise ValueError("Plugin dependencies form a cycle: " + " -> ".join(error.args[1])) from None
    manifests = {
        "claude": {
            "name": roster["name"],
            "description": roster["description"],
            "owner": {"name": roster["owner"]},
            "plugins": claude_entries,
        },
        "codex": {
            "name": roster["name"],
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
