#!/usr/bin/env python3
"""YourTeam v2 wiki checker (yourteam_version: 2.3.0 — tiers + DERIVED staleness).

Mechanizes the wiki protocol's mechanical checks over docs/scrum/wiki/:

  sweep  — staleness, for every `tier: map` article with `status: verified`.
           The baseline is DERIVED, never stored: it is the article's own last
           commit (`git log -1 -- <article>`). Any `code_ref` touched after that
           commit means the article is stale (agreement 2026-06-28: the sweep,
           never eyeballing, decides blast radius). --update rewrites
           `status: verified` -> stale in the flagged files.
           `tier: reference` articles make no live-code claims and are not swept.
  facts  — coverage lint: every file a Fact cites must be covered by the
           article's code_refs, else the staleness check can never flag
           that Fact and it rots silently (agreement 2026-06-25).
  links  — link lint: every [[slug]] must resolve to wiki/<slug>.md or
           wiki/archive/<slug>.md.
  refs   — staleness-amplifier lint (retro sprint-45, 2026-07-14): a file
           cited as a code_ref by many articles quarantines them ALL on any
           touch (one shared file once re-staled a third of a wiki). Notes
           by default; findings under --strict-refs.
  integrity — wiki-integrity lint (retro sprint-49, 2026-07-16; tier half added
           2026-08-12): (1) status: archived ⇒ the file must LIVE under
           wiki/archive/ AND carry archived_sprint + archived_reason frontmatter
           — a status-flip that leaves the article in the main dir with no
           tombstone is a fake archive the sweep silently skips (sprint-49:
           migrations-and-db.md). (2) `tier: reference` ⇒ NO code_refs and NO
           `## Facts` section. That is what makes "not swept" honest instead of
           an escape hatch: a reference article asserts nothing about live code,
           so it has nothing that can rot. An unknown tier is a finding, for the
           same reason an unknown status is.

WHY THE BASELINE IS DERIVED (2026-08-12). It used to be a stored `verified_sha`.
Bumping that field creates a NEW commit, which leaves the stamp pointing one
commit too early — the "verified_sha self-reference" repair commit, eight of them
in this repo, and unsatisfiable under per-step TDD where a wiki correction may cite
code that does not exist yet (sprint-69 retro, RC-10). Deriving the baseline from
the article's own last commit makes that class impossible by construction: a commit
touching the article and its code_ref TOGETHER is trivially not stale. It also
retires the c3 catalogue-lag check, whose satisfiable half this IS, and the
short-sha integrity rule, which existed only to detect a bulk re-stamp of a field
that no longer exists.

The cost, accepted deliberately: an edit to a swept article resets its baseline
whether or not the Facts were re-read. So editing a swept article IS re-verifying
it — if you are not re-verifying, do not touch it.

The sweep skips re-verification it can prove unnecessary: if the diff since the
baseline is whitespace-only (`git diff -w --ignore-blank-lines` empty), no Fact
content can have changed, so the article is not stale (retro sprint-45: one
formatter commit re-staled 7 articles, costing two re-verification waves). Any
non-whitespace change (even a quote-style swap) still stales normally.

Usage:
  python yt_wiki.py            # all checks
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
    # encoding is pinned: text=True alone decodes with the platform locale codec
    # (cp1252 on Windows), which raises on any non-ASCII byte in file CONTENT and
    # leaves stdout None. Harmless while git output was only ASCII paths; fatal once
    # a check reads a blob. errors="replace" matches how articles are read on disk.
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def covered(path: str, refs: list[str]) -> bool:
    p = path.replace("\\", "/").lstrip("./")
    for ref in refs:
        r = ref.replace("\\", "/").lstrip("./").rstrip("/")
        if p == r or p.startswith(r + "/"):
            return True
    return False


KNOWN_STATUSES = {"verified", "stale", "archived"}

# Absent `tier` means `map`: every article predating the 2026-08-12 tier split
# made live-code claims, so the backward-compatible default must be the swept one.
KNOWN_TIERS = {"map", "reference"}
DEFAULT_TIER = "map"


def article_baseline(root: Path, path: Path) -> str | None:
    """The article's own last commit — the DERIVED staleness baseline.

    Replaces the stored `verified_sha` (2026-08-12). Returns None when the
    article has no commit yet: a file written but not committed is not evidence
    about anything, and the sweep reads committed state.
    """
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None
    out = git(root, "log", "-1", "--format=%H", "--", rel)
    return out.stdout.strip() or None if out.returncode == 0 else None


def check_sweep(root: Path, articles: dict[Path, str], update: bool) -> list[str]:
    findings = []
    for path, text in articles.items():
        meta = parse_frontmatter(text)
        tier = meta.get("tier", DEFAULT_TIER)
        if tier not in KNOWN_TIERS:
            findings.append(
                f"{path.name}: UNRECOGNIZED tier={tier!r} — article is invisible to "
                f"the sweep; use one of {sorted(KNOWN_TIERS)}"
            )
            continue
        if tier == "reference":
            # Not a silent skip: a reference article is unswept because it asserts
            # nothing about live code, and `integrity` is what holds it to that.
            print(f"  note: {path.name} not swept (tier=reference — no live claims)")
            continue
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
        refs = meta.get("code_refs") or []
        if not refs:
            findings.append(
                f"{path.name}: tier=map and verified but no code_refs — nothing anchors "
                "its Facts, so nothing can ever flag them stale"
            )
            continue
        base = article_baseline(root, path)
        if base is None:
            print(
                f"  note: {path.name} not swept (no commit yet — uncommitted article)"
            )
            continue
        diff = git(root, "diff", "--name-only", f"{base}..HEAD", "--", *refs)
        hits = [ln for ln in diff.stdout.splitlines() if ln.strip()]
        if diff.returncode != 0:
            findings.append(
                f"{path.name}: git diff failed: {diff.stderr.strip()[:200]}"
            )
        elif hits:
            # Format-only drift: content identical once whitespace is ignored →
            # no Fact can have been invalidated; re-verifying with an LLM is
            # pure waste. Conservative by construction — ANY non-whitespace
            # change still stales. (Retro sprint-45, 2026-07-14.) Under a derived
            # baseline this needs no write: the same comparison stays empty on
            # every later sweep, so there is no stamp to keep up to date.
            ws = git(
                root, "diff", "-w", "--ignore-blank-lines", f"{base}..HEAD", "--", *refs
            )
            if ws.returncode == 0 and not ws.stdout.strip():
                print(
                    f"  note: {path.name} format-only drift in {len(hits)} "
                    "path(s) — no Fact content can have changed"
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


# A16 (sprint-67 retro, 2026-08-03). A bare `:NNN` line reference inside a Fact —
# no filename in front of it — is invisible to CITE_RE, which needs a filename to
# anchor on. Matched here only to REPORT it, never to resolve it: the check cannot
# know which file the author meant, which is precisely the problem.
BARE_LINE_RE = re.compile(r"`:(\d+)(?:-\d+)?`")


def check_citations(root: Path, articles: dict[Path, str]) -> list[str]:
    """Report Fact citations this tool could not check. (A16, sprint-67 retro.)

    `check_facts` answers "is every cited file covered by code_refs?" and, to do
    that, it must silently drop two kinds of citation: one whose path does not
    resolve from the repo root, and one with no filename at all. Both then pass
    as CLEAN — the tool reporting success about text it never examined.

    Sprint 67 hit both, in `status: verified` articles carrying fresh stamps:
      * six bare `:NNN` sites copied from a story's pre-edit AC text, five of
        which pointed at unrelated code (a comment, a docstring, `],`);
      * a Fact citing an abbreviated `core/services/...` path while the file was
        absent from the article's `code_refs`, so edits to it would never have
        staled the article.

    Advisory by default, like `refs`: it flags text a human must read, and a
    citation form is a style question until a project decides otherwise.
    """
    findings = []
    unresolved_total = 0
    for path, text in sorted(articles.items()):
        facts = facts_section(text)
        unresolved = []
        for cite in sorted(set(CITE_RE.findall(facts))):
            cite_path = cite.replace("\\", "/")
            if cite_path.startswith("docs/scrum/"):
                continue  # cross-references belong to the links check
            if "/" not in cite_path:
                # CITE_RE also matches dotted SYMBOL references (`Class.method`),
                # which are not paths and must never be reported as broken ones.
                # Requiring a separator is the only fully generic way to tell the
                # two apart, and a detector that flags everything is worse than
                # none — measured: without this, 515 notes, nearly all false. The
                # cost is that a bare `settings.py` shorthand goes unflagged; the
                # failure class this exists for is path-shaped and wrongly-rooted.
                continue
            if (root / cite_path).exists():
                continue  # resolvable — check_facts owns it from here
            unresolved.append(cite_path)
        if unresolved:
            unresolved_total += len(unresolved)
            sample = ", ".join(f"`{c}`" for c in unresolved[:3])
            more = f", +{len(unresolved) - 3} more" if len(unresolved) > 3 else ""
            findings.append(
                f"{path.name}: {len(unresolved)} Fact citation(s) do not resolve "
                f"from the repo root, so the Facts lint SKIPPED them ({sample}"
                f"{more}) — write full paths, or remove claims whose file is gone"
            )
        for line_no in sorted(set(BARE_LINE_RE.findall(facts)), key=int):
            findings.append(
                f"{path.name}: Fact cites a bare `:{line_no}` with no filename — "
                "nothing anchors it, so no lint can check it and it rots silently "
                f"on the next edit above that line. Use `path/to/file.py:{line_no}` "
                "or a `::symbol` reference"
            )
    if unresolved_total:
        findings.append(
            f"TOTAL: {unresolved_total} Fact citation(s) across "
            f"{sum(1 for f in findings if 'do not resolve' in f)} article(s) were "
            "never checked by the Facts lint. A `facts: CLEAN` line does not cover "
            "them — that gap is what this check exists to make visible"
        )
    return findings


def check_integrity(wiki: Path, articles: dict[Path, str]) -> list[str]:
    """Wiki-integrity lint (retro sprint-49, 2026-07-16; tier half 2026-08-12).

    Two mechanical guards for ways an article can escape the sweep while still
    looking like knowledge:
      1. status: archived ⇒ the file lives under wiki/archive/ AND carries
         archived_sprint + archived_reason frontmatter. A status-flip that leaves
         the article in the main dir with no tombstone is a fake archive: the
         sweep skips `status: archived`, so the flip silences the linter instead
         of being caught by it.
      2. tier: reference ⇒ no code_refs and no `## Facts` section. Reference
         articles are exempt from staleness because they claim nothing about live
         code — reasons, decisions, tombstones. The moment one cites code it is a
         map article wearing an exemption, which is precisely the trusted-and-wrong
         state the protocol exists to prevent.

    The former guard on `verified_sha` being a short sha is retired with the field
    itself (2026-08-12): it detected a bulk re-stamp of a stamp that no longer
    exists, and the derived baseline cannot be bulk-set at all.
    """
    findings = []
    for path, text in articles.items():  # main-dir articles
        meta = parse_frontmatter(text)
        if meta.get("status") == "archived":
            findings.append(
                f"{path.name}: status=archived but the file is in the main wiki dir — move "
                "it to wiki/archive/ with archived_sprint + archived_reason (a real tombstone)"
            )
        tier = meta.get("tier", DEFAULT_TIER)
        if tier not in KNOWN_TIERS:
            findings.append(
                f"{path.name}: UNRECOGNIZED tier={tier!r} — use one of {sorted(KNOWN_TIERS)}"
            )
        elif tier == "reference":
            if meta.get("code_refs"):
                findings.append(
                    f"{path.name}: tier=reference but declares code_refs — a reference "
                    "article makes no live-code claims. Drop the refs, or make it tier: map"
                )
            if facts_section(text).strip():
                findings.append(
                    f"{path.name}: tier=reference but has a `## Facts` section — Facts cite "
                    "live code and are never swept at this tier. Move them to a tier: map "
                    "article, or restate them as Inference"
                )
    archive = wiki / "archive"
    if archive.is_dir():
        for path in sorted(archive.glob("*.md")):
            meta = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
            missing = [
                k for k in ("archived_sprint", "archived_reason") if not meta.get(k)
            ]
            if missing:
                findings.append(
                    f"archive/{path.name}: archived article missing tombstone "
                    f"frontmatter: {', '.join(missing)}"
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
        help="sweep | facts | links | refs | citations | integrity (default: all)",
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
    ap.add_argument(
        "--strict-citations",
        action="store_true",
        help="citations: unresolvable/unanchored citations count as findings (exit 1)",
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
    checks = args.checks or [
        "sweep",
        "facts",
        "links",
        "refs",
        "citations",
        "integrity",
    ]
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
        elif check == "citations":
            found = check_citations(root, articles)
            advisory = not args.strict_citations  # notes by default (A16)
        elif check == "integrity":
            found = check_integrity(wiki, articles)
        else:
            print(f"yt_wiki: unknown check '{check}'", file=sys.stderr)
            return 4
        label = (
            "CLEAN"
            if not found
            else (f"{len(found)} note(s)" if advisory else f"{len(found)} finding(s)")
        )
        print(f"== {check}: {label} ==")
        for f in found:
            print(f"  {f}")
        if not advisory:
            all_findings.extend(found)

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
