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
                "plugins": entries,
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


@pytest.mark.parametrize("producer", ["agent", "core"])
@pytest.mark.parametrize("second", [None, "b" * 40])
def test_mixed_or_partial_producer_pins_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, producer: str, second: str | None
) -> None:
    entries: list[dict[str, object]] = [
        {"name": "one", "repository": producer, "revision": "a" * 40},
        {"name": "two", "repository": producer},
    ]
    if second is not None:
        entries[1]["revision"] = second
    roster(tmp_path, monkeypatch, entries)
    with pytest.raises(ValueError, match="same immutable revision"):
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


def test_other_producers_keep_independent_pin_policy(
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
    entries = json.loads(generate.build()["codex"])["plugins"]
    assert entries[0]["source"]["sha"] == "a" * 40
    assert entries[1]["source"]["ref"] == "main"


@pytest.mark.parametrize("revision", [[], {}])
def test_guarded_producer_rejects_non_scalar_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, revision: object
) -> None:
    roster(
        tmp_path,
        monkeypatch,
        [{"name": "agent", "repository": "agent", "revision": revision}],
    )
    with pytest.raises(ValueError, match="Invalid immutable"):
        generate.build()
