import subprocess
from pathlib import Path

import check_generic_scope as scope


def test_specific_profile_names_returns_only_specific_entries() -> None:
    plugins = [
        {"name": "work", "profile": "generic"},
        {"name": "infonetica", "profile": "specific", "extends": "work"},
        {"name": "acme", "profile": "specific", "extends": "work"},
    ]
    assert scope.specific_profile_names(plugins) == ["acme", "infonetica"]


def test_specific_profile_names_is_empty_when_everything_is_generic() -> None:
    plugins = [{"name": "base", "profile": "generic"}]
    assert scope.specific_profile_names(plugins) == []


def test_generic_repositories_excludes_a_repository_with_any_specific_entry() -> None:
    plugins = [
        {
            "name": "infonetica",
            "repository": "infonetica",
            "revision": "a" * 40,
            "profile": "specific",
        },
    ]
    assert scope.generic_repositories(plugins) == {}


def test_generic_repositories_groups_a_shared_repository_once() -> None:
    plugins = [
        {
            "name": "base",
            "repository": "core",
            "revision": "a" * 40,
            "profile": "generic",
        },
        {
            "name": "workflow",
            "repository": "core",
            "revision": "a" * 40,
            "profile": "generic",
        },
        {
            "name": "cli",
            "repository": "cli",
            "revision": "b" * 40,
            "profile": "generic",
        },
    ]
    assert scope.generic_repositories(plugins) == {"core": "a" * 40, "cli": "b" * 40}


def test_marketplace_source_id_reads_the_remote_origin_path(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "remote",
            "add",
            "origin",
            "https://github.com/tj-agents/marketplace.git",
        ],
        check=True,
    )
    assert scope.marketplace_source_id(tmp_path) == "tj-agents/marketplace"


def test_is_history_path_excludes_plans_reviews_and_generated_plugins() -> None:
    assert scope.is_history_path("plans/roadmap/GAMEPLAN.md")
    assert scope.is_history_path("reviews/Feature-X.md")
    assert scope.is_history_path("plugins/base/SKILL.md")


def test_is_history_path_allows_other_top_level_paths() -> None:
    assert not scope.is_history_path("AGENTS.md")
    assert not scope.is_history_path(".agents/base/convention/README.md")


def test_is_catalog_generated_true_for_the_recorded_marketplace_source() -> None:
    content = b'{"repository": "tj-agents/marketplace", "revision": "a"}'
    assert scope.is_catalog_generated(content, "tj-agents/marketplace")


def test_is_catalog_generated_false_for_an_unrelated_marketplace_source() -> None:
    content = b'{"repository": "tj-agents/other", "revision": "a"}'
    assert not scope.is_catalog_generated(content, "tj-agents/marketplace")


def test_is_catalog_generated_false_for_non_json_text() -> None:
    assert not scope.is_catalog_generated(
        b"Infonetica is work scope.", "tj-agents/marketplace"
    )


def test_find_matches_is_case_insensitive_and_whole_word() -> None:
    text = (
        "Line one\n"
        "See Infonetica's tracker\n"
        "unrelated infonetica-adjacent line\n"
        "Infonetical typo"
    )
    matches = scope.find_matches("infonetica", text)
    assert matches == [
        (2, "See Infonetica's tracker"),
        (3, "unrelated infonetica-adjacent line"),
    ]


def test_find_matches_returns_nothing_when_absent() -> None:
    assert scope.find_matches("infonetica", "no mention here") == []


def test_scan_tree_reports_a_violation_with_repository_path_and_line(
    tmp_path: Path,
) -> None:
    (tmp_path / "AGENTS.md").write_text(
        "Infonetica owns the tracker.\n", encoding="utf-8"
    )
    violations = scope.scan_tree(
        "core", tmp_path, ["infonetica"], "tj-agents/marketplace"
    )
    assert violations == [
        scope.Violation(
            "core", "AGENTS.md", 1, "infonetica", "Infonetica owns the tracker."
        )
    ]


def test_scan_tree_skips_history_and_catalog_generated_files(tmp_path: Path) -> None:
    (tmp_path / "plans").mkdir()
    (tmp_path / "plans" / "PLAN.md").write_text("Infonetica\n", encoding="utf-8")
    (tmp_path / "lock.json").write_text(
        '{"repository": "tj-agents/marketplace", "note": "Infonetica"}',
        encoding="utf-8",
    )
    violations = scope.scan_tree(
        "core", tmp_path, ["infonetica"], "tj-agents/marketplace"
    )
    assert violations == []


def test_scan_tree_skips_binary_files(tmp_path: Path) -> None:
    (tmp_path / "logo.bin").write_bytes(b"\xff\xfe\x00Infonetica\x00")
    violations = scope.scan_tree(
        "core", tmp_path, ["infonetica"], "tj-agents/marketplace"
    )
    assert violations == []
