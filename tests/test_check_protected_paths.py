"""Tests for the protected-path enforcement the orchestrator runs before apply."""
import check_protected_paths as C

ENGAGEMENT_GLOBS = ["**/evaluate.py", "**/fixtures/**", "**/gold_*.json", "**/*_gold.json"]

BASE = "engagements/madi_onboarding"
ADAPTER = f"{BASE}/adapters/forbes.toml"
EVALUATOR = f"{BASE}/evaluate.py"
GOLD = f"{BASE}/fixtures/gold_records.jsonl"


def _diff(path: str) -> str:
    """Minimal unified diff touching `path` (only the +++ line is parsed)."""
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n-old\n+new\n"


def test_changed_paths_parsing():
    assert C.changed_paths(_diff(ADAPTER)) == [ADAPTER]


def test_adapter_edit_is_allowed():
    assert C.protected_hits(C.changed_paths(_diff(ADAPTER)), ENGAGEMENT_GLOBS) == []


def test_editing_the_evaluator_is_blocked():
    hits = C.protected_hits(C.changed_paths(_diff(EVALUATOR)), ENGAGEMENT_GLOBS)
    assert hits and hits[0][0].endswith("evaluate.py")


def test_editing_gold_is_blocked():
    assert C.protected_hits(C.changed_paths(_diff(GOLD)), ENGAGEMENT_GLOBS)


def test_no_globs_means_nothing_protected():
    # The calculator declares no protected paths → nothing is blocked.
    assert C.protected_hits(C.changed_paths(_diff(EVALUATOR)), []) == []
