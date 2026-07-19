#!/usr/bin/env python3
"""Reject a patch that touches protected paths (deterministic Gate-4.1 check).

The dev-loop orchestrator runs this before `git apply`. It reads the protected
globs from the active flywheel.toml (`[protected].paths`), extracts the files a
unified diff touches, and exits non-zero if any is protected. Protected paths are
held-out evaluators, gold labels, fixtures, and scoring — the things the loop must
never edit to make its own metrics pass.

Exit 0 = clean (apply is allowed). Exit 2 = a protected path was touched.

Usage:
    python scripts/check_protected_paths.py <patchfile>
"""
from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

from flywheel_config import get_value


def changed_paths(diff_text: str) -> list[str]:
    """Extract target file paths from a unified diff (the `+++ b/...` lines)."""
    paths = []
    for line in diff_text.splitlines():
        if line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
            p = line[4:].strip()
            if p.startswith("b/"):
                p = p[2:]
            paths.append(p)
    return paths


def protected_hits(paths: list[str], globs: list[str]) -> list[tuple[str, str]]:
    """Return (path, glob) pairs for every changed path that matches a protected glob."""
    hits = []
    for path in paths:
        for glob in globs:
            if fnmatch.fnmatch(path, glob):
                hits.append((path, glob))
                break
    return hits


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: check_protected_paths.py <patchfile>", file=sys.stderr)
        return 2
    globs = get_value("protected.paths") or []
    if not globs:
        return 0  # app declares nothing protected
    paths = changed_paths(Path(argv[0]).read_text())
    hits = protected_hits(paths, globs)
    if hits:
        print("REJECTED: patch touches protected paths (evaluator/gold/fixtures/scoring):", file=sys.stderr)
        for path, glob in hits:
            print(f"  {path}  (matches {glob})", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
