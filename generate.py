#!/usr/bin/env python3
"""Generate host marketplaces from one canonical TJ Agents plugin roster."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
OUTPUTS = {
    "claude": ROOT / ".claude-plugin" / "marketplace.json",
    "codex": ROOT / ".agents" / "plugins" / "marketplace.json",
}


def build() -> dict[str, bytes]:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    if catalog["name"] != "tj-agents":
        raise ValueError("The shared marketplace identity must remain tj-agents")
    if not catalog["description"] or not catalog["owner"]:
        raise ValueError("Marketplace description and owner are required")
    plugins = catalog["plugins"]
    if not plugins:
        raise ValueError("The marketplace has no plugins")
    names: set[str] = set()
    claude_entries = []
    codex_entries = []
    for plugin in plugins:
        name, repository = plugin["name"], plugin["repository"]
        if not NAME.fullmatch(name) or not NAME.fullmatch(repository):
            raise ValueError(f"Invalid plugin or repository name: {plugin}")
        if name in names:
            raise ValueError(f"Duplicate plugin: {name}")
        names.add(name)
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
