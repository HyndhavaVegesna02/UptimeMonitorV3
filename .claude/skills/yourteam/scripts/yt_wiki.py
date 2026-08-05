#!/usr/bin/env python3
"""YourTeam v2 wiki checker (yourteam_version: 2.2.1 — adds the c3 catalogue-lag check).

Mechanizes the wiki protocol's mechanical checks over docs/scrum/wiki/:

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
  c3     — catalogue-lag lint (retro sprint-68, 2026-08-05; needs --range
           BASE..HEAD): for every non-merge commit in the range, a commit that
           MODIFIES a file an article both lists in code_refs and cites by name in
           its Facts must touch that article too. Notes by default; findings under
           --strict-c3. Read per STORY range. Bounds: check_c3's docstring.
  integrity — wiki-integrity lint (retro sprint-49, 2026-07-16): (1) verified_sha
           must be a SHORT sha (7-12 hex) — a 40-char full sha is the tell of a
           bulk "bump every article to HEAD" pass that never re-verified the Facts
           (sprint-49: 12 articles laundered to one 40-char sha). (2) status:
           archived ⇒ the file must LIVE under wiki/archive/ AND carry
           archived_sprint + archived_reason frontmatter — a status-flip that
           leaves the article in the main dir with no tombstone is a fake archive
           the sweep silently skips (sprint-49: migrations-and-db.md).

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
  python yt_wiki.py c3 --range sprint-68-start..HEAD    # not in the default run

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


SHORT_SHA_RE = re.compile(r"^[0-9a-f]{7,12}$")


def check_integrity(wiki: Path, articles: dict[Path, str]) -> list[str]:
    """Wiki-integrity lint (retro sprint-49, 2026-07-16).

    Two mechanical guards for failure modes an external delivery slipped past the
    other checks:
      1. verified_sha must be a SHORT sha (7-12 hex). A 40-char full sha is the
         tell of a bulk re-stamp that never re-verified the per-article Facts —
         which launders staleness and defeats the sweep's whole premise.
      2. status: archived ⇒ the file lives under wiki/archive/ AND carries
         archived_sprint + archived_reason frontmatter. A status-flip that leaves
         the article in the main dir with no tombstone is a fake archive: the
         sweep skips `status: archived`, so the flip silences the linter instead
         of being caught by it.
    """
    findings = []
    for path, text in articles.items():  # main-dir articles
        meta = parse_frontmatter(text)
        sha = meta.get("verified_sha")
        if sha and not SHORT_SHA_RE.match(sha):
            findings.append(
                f"{path.name}: verified_sha {sha!r} is not a short sha (7-12 hex) — a "
                "40-char sha signals a bulk re-stamp with no per-article re-verification"
            )
        if meta.get("status") == "archived":
            findings.append(
                f"{path.name}: status=archived but the file is in the main wiki dir — move "
                "it to wiki/archive/ with archived_sprint + archived_reason (a real tombstone)"
            )
    archive = wiki / "archive"
    if archive.is_dir():
        for path in sorted(archive.glob("*.md")):
            meta = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
            sha = meta.get("verified_sha")
            if sha and not SHORT_SHA_RE.match(sha):
                findings.append(
                    f"archive/{path.name}: verified_sha {sha!r} is not a short sha (7-12 hex)"
                )
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


def _blob_text(root: Path, blob: str, cache: dict[str, str]) -> str:
    if blob not in cache:
        cache[blob] = git(root, "cat-file", "-p", blob).stdout
    return cache[blob]


def check_c3(root: Path, wiki: Path, rng: str) -> list[str] | None:
    """C3 — the catalogue moves in the SAME COMMIT as the code it describes.

    For every non-merge commit in <base>..<head>: if the commit touches a file
    that some article lists in its `code_refs`, that same commit must also touch
    that article. This is pure git arithmetic over commit contents — no checkout,
    no judgment, no new dependency.

    Frontmatter is read AS OF EACH COMMIT (one `ls-tree` per commit, blobs cached),
    not at HEAD, so an article that gains a code_ref mid-range does not retroactively
    condemn the commits before it.

    ADVISORY BY DEFAULT (--strict-c3 blocks), and the reason is measured, not assumed.
    Two known bounds, stated because a check that oversells itself is worse than none:

    1. IT CATCHES THE SEQUENCING CLASS ONLY — prose landing after the code it
       describes. It cannot see a `verified_sha` bumped over a Fact nobody re-read,
       nor a citation into a file the citing article does not list as a code_ref: in
       both the arithmetic is correct and the CLAIM is what is false. On the five C3
       failures of sprint 68 it reaches two. Those need citation resolution.
    2. IT CANNOT TELL A COMPLETING COMMIT FROM A TDD STEP, and that is where its
       noise comes from. Measured on sprint 68 (101 commits): RED on both commits
       that produced a real AC failure, and 45 notes overall — 11 of them on
       STORY-205, a story no reviewer faulted. Mid-story green steps do not falsify a
       "this violation is live" claim; only the commit that COMPLETES the change
       does, and which commit that is, is not visible to arithmetic. Read the notes
       per story range, not per sprint.
    """
    findings: list[str] = []
    # A SETUP failure returns None, never a finding. c3 is advisory by default, so a
    # bad range reported as a note would exit 0 — a check that cannot run reading as
    # a check that found nothing. That is the A7 failure mode this repo already paid
    # for once, and it was caught here by testing the error path rather than the
    # happy one.
    try:
        rel_wiki = wiki.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        print(
            f"yt_wiki: wiki dir {wiki} is outside the repo root {root} — "
            "c3 cannot range-check it",
            file=sys.stderr,
        )
        return None

    rev = git(root, "rev-list", "--reverse", "--no-merges", rng)
    if rev.returncode != 0:
        print(f"yt_wiki: c3 bad range '{rng}': {rev.stderr.strip()}", file=sys.stderr)
        return None
    shas = [s for s in rev.stdout.split() if s]

    blobs: dict[str, str] = {}
    for sha in shas:
        status = [
            line.split("\t")
            for line in git(
                root, "show", "--name-status", "--format=", sha
            ).stdout.splitlines()
            if "\t" in line
        ]
        if not status:
            continue
        touched = {parts[-1] for parts in status}
        # Only a file that ALREADY EXISTED can falsify prose written about it. A
        # newly ADDED file cannot: no article can cite a line that did not exist.
        # Renames (R) and deletions (D) very much can, so only "A" is dropped.
        files = [parts[-1] for parts in status if parts[0][:1] != "A"]
        if not files:
            continue
        tree = git(root, "ls-tree", "-r", sha, "--", rel_wiki).stdout.splitlines()
        for line in tree:
            if "\t" not in line:
                continue
            info, apath = line.split("\t", 1)
            parts = info.split()
            if len(parts) < 3 or parts[1] != "blob" or not apath.endswith(".md"):
                continue
            if "/archive/" in apath:
                continue
            atext = _blob_text(root, parts[2], blobs)
            meta = parse_frontmatter(atext)
            refs = meta.get("code_refs") or []
            if not refs or meta.get("status") == "archived":
                continue
            if apath in touched:
                continue  # the article moved with the code — this is C3 satisfied
            # A code_ref only says "this article is ABOUT this area". What C3 protects
            # is a CLAIM, and a claim lives in a Fact that names the file. So require
            # both: the file is in code_refs AND some Fact in the article (as of this
            # commit) cites it by name. Without the second half every TDD green step
            # under a broad code_ref reads as a violation.
            facts = facts_section(atext)
            hits = [
                f
                for f in files
                if f != apath and covered(f, refs) and Path(f).name in facts
            ]
            if hits:
                extra = f" (+{len(hits) - 1} more)" if len(hits) > 1 else ""
                findings.append(
                    f"{sha[:9]}: {Path(apath).name} not updated, but the commit "
                    f"touched its code_ref {hits[0]}{extra}"
                )
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "checks",
        nargs="*",
        default=[],
        help="sweep | facts | links | refs | citations | integrity | c3 "
        "(default: all but c3, which needs --range)",
    )
    ap.add_argument(
        "--range",
        dest="rng",
        default=None,
        metavar="BASE..HEAD",
        help="c3: commit range to check (required by, and only used by, the c3 check)",
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
    ap.add_argument(
        "--strict-c3",
        action="store_true",
        help="c3: catalogue-lag notes count as findings (exit 1)",
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
        elif check == "c3":
            if not args.rng:
                print(
                    "yt_wiki: the c3 check requires --range BASE..HEAD", file=sys.stderr
                )
                return 4
            found = check_c3(root, wiki, args.rng)
            if found is None:
                return 4  # setup failure, never a silent advisory pass
            advisory = not args.strict_c3  # notes by default — see check_c3's docstring
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
