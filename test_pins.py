import json
from pathlib import Path

import pytest

import generate


def roster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entries: list[dict[str, object]]
) -> None:
    monkeypatch.setattr(generate, "ROOT", tmp_path)
    (tmp_path / "plugins.json").write_text(
        json.dumps(
            {
                "name": "tj-agents",
                "description": "Fixture",
                "owner": "Fixture",
                "plugins": [{"profile": "generic", **entry} for entry in entries],
            }
        ),
        encoding="utf-8",
    )


def test_immutable_revision_uses_native_sha_for_both_hosts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roster(
        tmp_path,
        monkeypatch,
        [
            {"name": "agent", "repository": "agent", "revision": "a" * 40},
            {"name": "base", "repository": "core", "revision": "c" * 40},
        ],
    )
    for output in generate.build().values():
        entries = json.loads(output)["plugins"]
        assert entries[0]["source"]["sha"] == "a" * 40
        assert entries[1]["source"]["sha"] == "c" * 40
        assert all("ref" not in entry["source"] for entry in entries)


@pytest.mark.parametrize("producer", ["agent", "core", "cli"])
def test_mixed_producer_pins_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, producer: str
) -> None:
    roster(
        tmp_path,
        monkeypatch,
        [
            {"name": "one", "repository": producer, "revision": "a" * 40},
            {"name": "two", "repository": producer, "revision": "b" * 40},
        ],
    )
    with pytest.raises(ValueError, match="same immutable revision"):
        generate.build()


def test_an_unpinned_entry_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roster(
        tmp_path,
        monkeypatch,
        [
            {"name": "one", "repository": "other", "revision": "a" * 40},
            {"name": "two", "repository": "other"},
        ],
    )
    with pytest.raises(ValueError, match="require name, repository and revision"):
        generate.build()


@pytest.mark.parametrize("revision", ["main", "a" * 39, "A" * 40, 42, None, [], {}])
def test_invalid_revision_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, revision: object
) -> None:
    roster(
        tmp_path,
        monkeypatch,
        [{"name": "other", "repository": "other", "revision": revision}],
    )
    with pytest.raises(ValueError, match="Invalid immutable"):
        generate.build()

