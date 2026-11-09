import json
from pathlib import Path

import generate

RENOVATE = generate.ROOT / ".github" / "renovate.json"


def employer_repositories() -> set[str]:
    roster = json.loads((generate.ROOT / "plugins.json").read_text(encoding="utf-8"))
    return {plugin["repository"] for plugin in roster["plugins"] if "work" in plugin.get("requires", [])}


def test_renovate_never_advances_an_employer_profile_pin() -> None:
    rules = json.loads(RENOVATE.read_text(encoding="utf-8"))["packageRules"]
    final = rules[-1]
    assert final.get("enabled") is False
    assert final.get("matchManagers") == ["custom.regex"]
    assert set(final.get("matchDepNames", [])) == employer_repositories()


def test_employer_profiles_are_detected_from_the_roster() -> None:
    assert "infonetica" in employer_repositories()
    assert "work" not in employer_repositories()
