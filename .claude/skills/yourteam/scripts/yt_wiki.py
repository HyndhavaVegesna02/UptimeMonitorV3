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
  refs   — staleness-amplifier lint (retro sprint-45, 2026-07-14): a file
           cited as a code_ref by many articles quarantines them ALL on any
           touch (one shared file once re-staled a third of a wiki). Notes
           by default; findings under --strict-refs.

The sweep skips LLM re-verification it can prove unnecessary: if the diff
since verified_sha is whitespace-only (`git diff -w --ignore-blank-lines`
empty), no Fact content can have changed — with --update the verified_sha is
bumped mechanically instead of marking stale (retro sprint-45: one formatter
commit re-staled 7 articles, costing two re-verification waves). Any
non-whitespace change (even a quote-style swap) still stales normally.

Usage:
  python yt_wiki.py            # all four checks
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
        # Strip a trailing inline comment (e.g. "verified   # verified | stale") —
        # without this, a commented status line makes the article invisibly skip
        # the sweep, which is exactly the silent hole the sweep exists to prevent.
        if "#" in val and key != "code_refs":
            val = val.split("#", 1)[0].strip()
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
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, timeout=60
    )


def covered(path: str, refs: list[str]) -> bool:
    p = path.replace("\\", "/").lstrip("./")
    for ref in refs:
        r = ref.replace("\\", "/").lstrip("./").rstrip("/")
        if p == r or p.startswith(r + "/"):
            return True
    return False


KNOWN_STATUSES = {"verified", "stale", "archived"}


def check_sweep(root: Path, articles: dict[Path, str], update: bool) -> list[str]:
    findings = []
    for path, text in articles.items():
        meta = parse_frontmatter(text)
        status = meta.get("status")
        if status != "verified":
            # Silent exclusion from the sweep is how knowledge rots invisibly:
            # say WHY every unswept article is unswept. Unknown statuses are
            # findings (typo/mangled frontmatter would otherwise hide an article).
            if status in KNOWN_STATUSES:
                print(f"  note: {path.name} not swept (status={status})")
            else:
                findings.append(
                    f"{path.name}: UNRECOGNIZED status={status!r} — article is invisible "
                    "to the sweep; fix the frontmatter"
                )
            continue
        sha, refs = meta.get("verified_sha"), meta.get("code_refs") or []
        if not sha or not refs:
            findings.append(f"{path.name}: verified but missing verified_sha/code_refs")
            continue
        if git(root, "cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
            findings.append(
                f"{path.name}: UNRESOLVABLE verified_sha {sha} — treat as stale (edge-case #4)"
            )
            continue
        diff = git(root, "diff", "--name-only", f"{sha}..HEAD", "--", *refs)
        hits = [ln for ln in diff.stdout.splitlines() if ln.strip()]
        if diff.returncode != 0:
            findings.append(
                f"{path.name}: git diff failed: {diff.stderr.strip()[:200]}"
            )
        elif hits:
            # Format-only drift: content identical once whitespace is ignored →
            # no Fact can have been invalidated; re-verifying with an LLM is
            # pure waste. Conservative by construction — ANY non-whitespace
            # change still stales. (Retro sprint-45, 2026-07-14.)
            ws = git(
                root, "diff", "-w", "--ignore-blank-lines", f"{sha}..HEAD", "--", *refs
            )
            if ws.returncode == 0 and not ws.stdout.strip():
                if update:
                    head = git(root, "rev-parse", "HEAD").stdout.strip()
                    new = re.sub(
                        rf"^(verified_sha:\s*){re.escape(sha)}",
                        rf"\g<1>{head}",
                        text,
                        count=1,
                        flags=re.M,
                    )
                    path.write_text(new, encoding="utf-8")
                    print(
                        f"  note: {path.name} format-only drift — verified_sha "
                        f"auto-bumped to {head[:7]} (no LLM re-verify needed)"
                    )
                else:
                    print(
                        f"  note: {path.name} format-only drift in {len(hits)} "
                        "path(s) — auto-verifiable with --update"
                    )
                continue
            findings.append(
                f"{path.name}: STALE — {len(hits)} changed path(s): {', '.join(hits[:5])}"
            )
            if update:
                new = text.replace("status: verified", "status: stale", 1)
                path.write_text(new, encoding="utf-8")
    return findings


# A code_ref shared by this many articles is a staleness amplifier: one touch
# of that file quarantines them all, and every quarantine is an LLM re-read.
AMPLIFIER_THRESHOLD = 4


def check_refs(articles: dict[Path, str]) -> list[str]:
    counts: dict[str, list[str]] = {}
    for path, text in articles.items():
        for ref in set(parse_frontmatter(text).get("code_refs") or []):
            counts.setdefault(ref.replace("\\", "/"), []).append(path.name)
    findings = []
    for ref, names in sorted(counts.items()):
        if len(names) >= AMPLIFIER_THRESHOLD:
            findings.append(
                f"amplifier: `{ref}` is a code_ref in {len(names)} articles "
                f"({', '.join(sorted(names)[:4])}...) — any touch quarantines all "
                "of them; narrow it to the article(s) actually ABOUT it"
            )
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
                findings.append(
                    f"{path.name}: Fact cites `{cite_path}` not covered by code_refs"
                )
    return findings


def check_links(root: Path, wiki: Path, articles: dict[Path, str]) -> list[str]:
    findings = []
    for path, text in articles.items():
        for slug in set(LINK_RE.findall(text)):
            if not (
                (wiki / f"{slug}.md").exists()
                or (wiki / "archive" / f"{slug}.md").exists()
            ):
                findings.append(f"{path.name}: broken link [[{slug}]]")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "checks",
        nargs="*",
        default=[],
        help="sweep | facts | links | refs (default: all)",
    )
    ap.add_argument("--wiki", default=None, help="wiki dir (default docs/scrum/wiki)")
    ap.add_argument(
        "--update", action="store_true", help="sweep: rewrite status to stale on hits"
    )
    ap.add_argument(
        "--strict-refs",
        action="store_true",
        help="refs: amplifier notes count as findings (exit 1)",
    )
    args = ap.parse_args()

    root = find_root(Path.cwd().resolve())
    if root is None:
        print(
            "yt_wiki: no .scrum/ directory found walking up from cwd", file=sys.stderr
        )
        return 4
    wiki = Path(args.wiki) if args.wiki else root / "docs" / "scrum" / "wiki"
    if not wiki.is_dir():
        print(f"yt_wiki: wiki dir not found: {wiki}", file=sys.stderr)
        return 4

    articles = {
        p: p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(wiki.glob("*.md"))
    }
    checks = args.checks or ["sweep", "facts", "links", "refs"]
    all_findings: list[str] = []
    for check in checks:
        advisory = False
        if check == "sweep":
            found = check_sweep(root, articles, args.update)
        elif check == "facts":
            found = check_facts(root, articles)
        elif check == "links":
            found = check_links(root, wiki, articles)
        elif check == "refs":
            found = check_refs(articles)
            advisory = not args.strict_refs  # notes by default — never blocks
        else:
            print(f"yt_wiki: unknown check '{check}'", file=sys.stderr)
            return 4
        label = "CLEAN" if not found else (
            f"{len(found)} note(s)" if advisory else f"{len(found)} finding(s)"
        )
        print(f"== {check}: {label} ==")
        for f in found:
            print(f"  {f}")
        if not advisory:
            all_findings.extend(found)

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
