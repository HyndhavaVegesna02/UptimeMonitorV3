#!/usr/bin/env python3
"""YourTeam v2 wiki checker (yourteam_version: 2.0.0).

Mechanizes the wiki protocol's three mechanical checks over docs/scrum/wiki/:

  sweep  — staleness: for every `status: verified` article, run
           `git diff --name-only <verified_sha>..HEAD -- <code_refs>`;
           any hit means the article is stale (agreement 2026-06-28: the
           sweep, never eyeballing, decides blast radius). An unresolvable
           verified_sha (e.g. lost to a cherry-pick) counts as stale
           (edge-case #4). --update rewrites `status: verified` -> stale
           in the flagged files.
  facts  — coverage lint: every file a Fact cites must be covered by the
           article's code_refs, else the staleness check can never flag
           that Fact and it rots silently (agreement 2026-06-25).
  links  — link lint: every [[slug]] must resolve to wiki/<slug>.md or
           wiki/archive/<slug>.md.

Usage:
  python yt_wiki.py            # all three checks
  python yt_wiki.py sweep --update
  python yt_wiki.py facts links

Exit codes: 0 clean; 1 findings in any requested check; 4 setup error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CITE_RE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./\\-]*\.[A-Za-z0-9_]+)(?:::[^`]*)?`")
LINK_RE = re.compile(r"\[\[([A-Za-z0-9_-]+)\]\]")


def find_root(start: Path) -> Path | None:
    for p in [start, *start.parents]:
        if (p / ".scrum").is_dir():
            return p
    return None


def parse_frontmatter(text: str) -> dict:
    meta: dict = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return meta
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if key == "code_refs":
            inner = val.strip("[]")
            meta[key] = [p.strip().strip("'\"") for p in inner.split(",") if p.strip()]
        else:
            meta[key] = val.strip("'\"")
    return meta


def facts_section(text: str) -> str:
    m = re.search(r"^##\s+Facts.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=60)


def covered(path: str, refs: list[str]) -> bool:
    p = path.replace("\\", "/").lstrip("./")
    for ref in refs:
        r = ref.replace("\\", "/").lstrip("./").rstrip("/")
        if p == r or p.startswith(r + "/"):
            return True
    return False


def check_sweep(root: Path, articles: dict[Path, str], update: bool) -> list[str]:
    findings = []
    for path, text in articles.items():
        meta = parse_frontmatter(text)
        if meta.get("status") != "verified":
            continue
        sha, refs = meta.get("verified_sha"), meta.get("code_refs") or []
        if not sha or not refs:
            findings.append(f"{path.name}: verified but missing verified_sha/code_refs")
            continue
        if git(root, "cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
            findings.append(f"{path.name}: UNRESOLVABLE verified_sha {sha} — treat as stale (edge-case #4)")
            continue
        diff = git(root, "diff", "--name-only", f"{sha}..HEAD", "--", *refs)
        hits = [ln for ln in diff.stdout.splitlines() if ln.strip()]
        if diff.returncode != 0:
            findings.append(f"{path.name}: git diff failed: {diff.stderr.strip()[:200]}")
        elif hits:
            findings.append(f"{path.name}: STALE — {len(hits)} changed path(s): {', '.join(hits[:5])}")
            if update:
                new = text.replace("status: verified", "status: stale", 1)
                path.write_text(new, encoding="utf-8")
    return findings


def check_facts(root: Path, articles: dict[Path, str]) -> list[str]:
    findings = []
    for path, text in articles.items():
        meta = parse_frontmatter(text)
        refs = meta.get("code_refs") or []
        for cite in set(CITE_RE.findall(facts_section(text))):
            cite_path = cite.replace("\\", "/")
            if cite_path.startswith("docs/scrum/"):
                continue  # wiki/history cross-references belong to the links check
            if not (root / cite_path).exists():
                continue  # not a repo file (or already deleted — the sweep owns that)
            if not covered(cite_path, refs):
                findings.append(f"{path.name}: Fact cites `{cite_path}` not covered by code_refs")
    return findings


def check_links(root: Path, wiki: Path, articles: dict[Path, str]) -> list[str]:
    findings = []
    for path, text in articles.items():
        for slug in set(LINK_RE.findall(text)):
            if not ((wiki / f"{slug}.md").exists() or (wiki / "archive" / f"{slug}.md").exists()):
                findings.append(f"{path.name}: broken link [[{slug}]]")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("checks", nargs="*", default=[], help="sweep | facts | links (default: all)")
    ap.add_argument("--wiki", default=None, help="wiki dir (default docs/scrum/wiki)")
    ap.add_argument("--update", action="store_true", help="sweep: rewrite status to stale on hits")
    args = ap.parse_args()

    root = find_root(Path.cwd().resolve())
    if root is None:
        print("yt_wiki: no .scrum/ directory found walking up from cwd", file=sys.stderr)
        return 4
    wiki = Path(args.wiki) if args.wiki else root / "docs" / "scrum" / "wiki"
    if not wiki.is_dir():
        print(f"yt_wiki: wiki dir not found: {wiki}", file=sys.stderr)
        return 4

    articles = {
        p: p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(wiki.glob("*.md"))
    }
    checks = args.checks or ["sweep", "facts", "links"]
    all_findings: list[str] = []
    for check in checks:
        if check == "sweep":
            found = check_sweep(root, articles, args.update)
        elif check == "facts":
            found = check_facts(root, articles)
        elif check == "links":
            found = check_links(root, wiki, articles)
        else:
            print(f"yt_wiki: unknown check '{check}'", file=sys.stderr)
            return 4
        print(f"== {check}: {'CLEAN' if not found else str(len(found)) + ' finding(s)'} ==")
        for f in found:
            print(f"  {f}")
        all_findings.extend(found)

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
