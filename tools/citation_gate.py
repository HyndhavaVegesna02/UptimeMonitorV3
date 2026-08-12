"""Wiring layer between `tools/citation_sweep.py` and the standing pytest gate
(STORY-219, `backend/tests/test_citation_gate.py`).

This module does NOT re-implement citation resolution -- every check goes
through `citation_sweep.CITATION_RE` (extraction) and
`citation_sweep.check_citation` (resolution) unchanged. What it adds is the
one thing the bare sweep does not do: partition the extracted citations into
an ENFORCED set (a repo-relative path) and an ADVISORY set (a bare filename
such as `server.py:66`), and expose the top-level wiki glob + frontmatter
`tier:` read the standing test's ratchet needs.

**Why path resolvability, not line-number presence, is the filter (AC2):**
`citation_sweep.CITATION_RE` makes the line number MANDATORY in the citation
shape it extracts -- a citation with no line number is never matched at all.
Filtering on "has a line number" is therefore a no-op; filtering on "the path
contains a `/`" is what actually separates a resolvable repo-relative path
from a bare filename mention that can never be uniquely resolved.

Usage (report-only CLI, mirrors `tools/citation_sweep.py`/
`tools/zr3_duplicate_sweep.py`): ``python tools/citation_gate.py [repo_root]``
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import citation_sweep as sweep

#: The literal, top-level-only glob this story's AC3 pins.
#: `docs/scrum/wiki/archive/` is a subdirectory and is OUT of scope --
#: `Path.glob("*.md")` never descends into it, so this is enforced by
#: construction, not by a separate exclusion list.
WIKI_GLOB = "docs/scrum/wiki/*.md"

_TIER_RE = re.compile(r"^tier:\s*(\S+)", re.M)


def wiki_articles(repo_root: Path) -> list[Path]:
    """Every article matched by `WIKI_GLOB`, sorted for determinism."""
    return sorted((repo_root / "docs" / "scrum" / "wiki").glob("*.md"))


def article_tier(article: Path) -> str | None:
    """Read the `tier:` frontmatter field mechanically (AC6) -- never a
    hand-listed filename. Returns ``None`` if the article has no frontmatter
    block or no `tier:` line (neither occurs in this wiki today, but an
    article missing the field is not silently treated as exempt)."""
    text = article.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    frontmatter = text[: end if end != -1 else len(text)]
    match = _TIER_RE.search(frontmatter)
    return match.group(1) if match else None


def partition_citations(
    repo_root: Path, article: Path
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Extract every distinct citation from `article` via
    `citation_sweep.CITATION_RE` + `citation_sweep.check_citation` (never
    re-implemented) and partition it into
    ``(enforced_ok, enforced_fail, advisory_ok, advisory_fail)`` message
    lists (AC2). ENFORCED = the citation's path contains a `/` (a
    repo-relative path, resolvable in principle, even if the path itself is
    wrong); ADVISORY = a bare filename (e.g. `server.py:66`) that
    `CITATION_RE` still matched -- it mandates a line number, never a path
    shape -- but that can never be uniquely resolved against the repo root.

    The two lists partition the full extracted (path, line-spec) set by
    construction: every match lands in exactly one of the four buckets.
    """
    text = article.read_text(encoding="utf-8")
    seen: set[tuple[str, int, int | None]] = set()
    enforced_ok: list[str] = []
    enforced_fail: list[str] = []
    advisory_ok: list[str] = []
    advisory_fail: list[str] = []

    for m in sweep.CITATION_RE.finditer(text):
        path_str, l1, l2, _excerpt_full, anchor = m.groups()
        line1 = int(l1)
        line2 = int(l2) if l2 else None
        key = (path_str, line1, line2)
        if key in seen:
            continue
        seen.add(key)

        ok, msg = sweep.check_citation(repo_root, path_str, line1, line2, anchor)
        enforced = "/" in path_str
        if enforced:
            (enforced_ok if ok else enforced_fail).append(msg)
        else:
            (advisory_ok if ok else advisory_fail).append(msg)

    return enforced_ok, enforced_fail, advisory_ok, advisory_fail


def main() -> int:
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    total_enforced_fail = 0
    for article in wiki_articles(repo_root):
        tier = article_tier(article)
        enforced_ok, enforced_fail, advisory_ok, advisory_fail = partition_citations(
            repo_root, article
        )
        exempt = " [EXEMPT: tier: reference]" if tier == "reference" else ""
        print(
            f"{article.name}{exempt}: enforced {len(enforced_fail)} failing / "
            f"{len(enforced_ok) + len(enforced_fail)} total, advisory "
            f"{len(advisory_fail)} failing / {len(advisory_ok) + len(advisory_fail)} total"
        )
        if tier != "reference":
            total_enforced_fail += len(enforced_fail)
    print()
    print(f"Total ENFORCED failures (non-exempt articles): {total_enforced_fail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
