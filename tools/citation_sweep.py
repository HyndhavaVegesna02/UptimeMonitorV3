"""Citation-resolution sweep for sprint audit reports (STORY-195/196).

For every `` `path:line` `` or `` `path:line-line` `` citation in a Markdown report,
immediately followed by a parenthesized backtick excerpt -- the
`` `path:line` (`excerpt`) `` shape these reports use throughout -- extracts the
excerpt and confirms it is a substring of the actual file's cited line range (a
content-anchor check), not merely that the file has at least that many lines.
Citations with no such excerpt fall back to a line-count-only check, reported as
such rather than silently upgraded to false confidence.

Citations are EXTRACTED from the report's own Markdown via regex, never a
hand-typed manifest (A9, `.scrum/checklists/implementer.md`).

**Known, stated limitations (do not over-trust a FAIL from these classes):**

1. A citation into a file OUTSIDE the given repo root (e.g. a Claude memory file)
   always reports FAIL here -- resolve it manually against its real location.
2. A `` `ClassName.method` `` or `` `ClassName.method(signature)` `` SYMBOL-style
   citation (naming what a line lives inside, not quoting it verbatim) is a
   legitimate documentation style this heuristic cannot distinguish from a literal
   excerpt, and will false-FAIL.
3. A multi-line excerpt PARAPHRASED with semicolons joining several real source
   lines will false-FAIL a strict substring check against the real
   (newline-separated) source.

None of these three classes is a broken citation; each FAIL should be triaged by a
human before being reported as a real defect (STORY-195's own precedent).

Usage: ``python tools/citation_sweep.py <report.md> [repo_root]``
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

#: Matches `` `path:line` `` or `` `path:line-line` `` optionally followed by
#: `` (`excerpt`) ``. `path` must contain a slash-or-dot-separated relative path
#: ending in a known extension.
CITATION_RE = re.compile(
    r"`([\w./\-]+\.(?:py|md|yaml|html)):(\d+)(?:-(\d+))?`\**"
    r"(?:\s*\((`([^`]*)`)?[^)]*\))?"
)


def resolve_path(repo_root: Path, rel: str) -> Path | None:
    candidate = repo_root / rel
    return candidate if candidate.exists() else None


def check_citation(
    repo_root: Path,
    path_str: str,
    line1: int,
    line2: int | None,
    anchor: str | None,
) -> tuple[bool, str]:
    resolved = resolve_path(repo_root, path_str)
    label = f"{path_str}:{line1}" + (f"-{line2}" if line2 else "")
    if resolved is None:
        return False, f"{label} (file does not exist)"

    lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
    end = line2 if line2 else line1

    if anchor:
        window = "\n".join(lines[line1 - 1 : end]) if line1 >= 1 else ""
        if anchor in window:
            return (
                True,
                f"{label} (file has {len(lines)} lines) [anchor matched: {anchor!r}]",
            )
        return False, f"{label} (anchor {anchor!r} NOT found in lines {line1}-{end})"

    if len(lines) >= end:
        return (
            True,
            f"{label} (file has {len(lines)} lines) [line-count only, no anchor]",
        )
    return False, f"{label} (file has only {len(lines)} lines, need >= {end})"


def sweep(report_path: Path, repo_root: Path) -> tuple[int, int]:
    """Run the sweep; print every result; return (failures, total_occurrences)."""
    text = report_path.read_text(encoding="utf-8")
    matches = list(CITATION_RE.finditer(text))

    seen_pairs: set[tuple[str, int, int | None]] = set()
    results: list[str] = []
    anchor_verified = 0
    line_count_only = 0
    failures = 0

    for m in matches:
        path_str, l1, l2, _excerpt_full, anchor = m.groups()
        line1 = int(l1)
        line2 = int(l2) if l2 else None
        key = (path_str, line1, line2)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        ok, msg = check_citation(repo_root, path_str, line1, line2, anchor)
        status = "OK  " if ok else "FAIL"
        results.append(f"{status} {msg}")
        if not ok:
            failures += 1
        elif anchor:
            anchor_verified += 1
        else:
            line_count_only += 1

    for line in results:
        print(line)
    print()
    print(
        f"Extracted {len(matches)} citation occurrence(s), {len(seen_pairs)} distinct "
        f"(path, line-spec) pair(s) checked -- {anchor_verified} content-anchor-verified, "
        f"{line_count_only} line-count-only (no anchor present), {failures} failure(s)."
    )
    return failures, len(matches)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python tools/citation_sweep.py <report.md> [repo_root]")
        return 2
    report_path = Path(sys.argv[1]).resolve()
    repo_root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd()
    failures, _total = sweep(report_path, repo_root)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
