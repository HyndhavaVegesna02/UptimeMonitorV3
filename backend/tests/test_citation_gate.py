"""Standing guard (STORY-219): wires `tools/citation_sweep.py`'s citation
RESOLUTION into `python -m pytest` via a per-article ratchet baseline, instead
of the tool sitting unused (filed against sprint-68's RC-2: five `file:line`
citations went stale under a commit that never touched their content).

**What this test proves, stated exactly because the honest scope is narrower
than "citations are correct" (AC1):** for every citation whose path resolves
from the repo root (a repo-relative path, not a bare filename), the cited
file exists and is long enough to contain the cited line. The cited CONTENT
is verified only for the minority of citations carrying a parenthesized
excerpt anchor (`` `path:line` (`excerpt`) ``) -- **13 of 198 distinct
citations repo-wide carry one and get a content check; 8 pass and 5 fail**
(the 5 are zone-rules.md's own anchor-mismatch baseline). Corrected
2026-08-13 after quality review: the earlier "8 of 195" was wrong twice --
195 was the BASE-COMMIT denominator, which this very story's edits to
config-layer.md and zone-rules.md moved to 198, and 8 counted the PASSING
subset while the sentence described the CHECKED set. "Distinct" means
per-article dedupe summed across articles (`partition_citations` resets its
`seen` set per article), NOT globally distinct -- which is 186, and stating
the number without its method is how the first version rotted.
`test_ac1_docstring_scope_numbers_are_current` re-derives all three live, so
this sentence cannot go stale silently again. **A wrong-but-in-range line
number PASSES.** The worked example that demonstrates this today:
`scripts/seed_topology.py:44` (cited from `config-layer.md`'s own History,
sprint-68 entry) is reported OK by this exact mechanism, even though the
Fact it once supported has since moved to `:48` -- the tool cannot tell.
Do not read a green run of this test as "the wiki's citations are correct";
read it as "the wiki's *resolvable* citations point at real, long-enough
files."

**The filter that actually discriminates is PATH RESOLVABILITY, not the
presence of a line number** (`tools/citation_gate.py::partition_citations`,
AC2). `citation_sweep.CITATION_RE` makes the line number MANDATORY, so a
"filter on citations carrying a line number" removes nothing -- measured:
129 of 129 raw failures at this story's base commit carried one. A citation
whose path contains no `/` (a bare filename such as `server.py:66`) is
reported ADVISORY, never enforced; a citation with a repo-relative path
(even an incomplete/wrong one, e.g. `adapters/inbound/dynatrace/query.py:83`
missing its `backend/src/` prefix) is ENFORCED.

`tools/citation_gate.py` derives `wiki_articles()`/`article_tier()`/
`partition_citations()` by calling straight into `citation_sweep.CITATION_RE`
and `citation_sweep.check_citation` -- this module is NOT a rewrite of the
sweep, only a partition + ratchet wired on top of it.
"""

from __future__ import annotations

from pathlib import Path

import citation_gate as gate  # tools/ is on sys.path via backend/tests/conftest.py

_REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# AC3/AC4/AC6/AC8 -- the committed per-article baseline.
#
# Glob is LITERAL: docs/scrum/wiki/*.md, top level only (`Path.glob`, non-
# recursive) -- 17 articles. `docs/scrum/wiki/archive/` is a subdirectory and
# is OUT of scope; this is stated here, not left as a 17-vs-19 ambiguity.
#
# Per article: {"tier": "map"|"reference", "baseline": int | None, "note": str}.
#   - tier == "reference": AC6 EXEMPTS it from the ratchet -- read live from
#     the article's OWN frontmatter at test time (`gate.article_tier`), never
#     assumed from this table (the "tier" value below is descriptive, cross-
#     checked against the live read by `test_ac6...`, not authoritative on
#     its own). "baseline" is None and carries no enforcement. Two
#     independent reasons pin this (`.claude/skills/yourteam/references/
#     wiki-protocol.md:21` -- reference tier is "append-only, cites no live
#     line" -- and `:56` -- an article wanting to cite code IS a map article):
#     `zone-rules-history.md`'s citations are into HISTORY, claims about past
#     state a tool resolving against HEAD cannot judge, and AC4's ratchet on
#     an append-only article would go RED on the next appended entry, forcing
#     its author to move a baseline they did not set.
#   - tier == "map": "baseline" is the EXACT enforced-citation failure count
#     (AC2's partition) this ratchet holds the article to. AC4 is an EQUALITY
#     ratchet, not a ceiling: a count BELOW baseline fails too, so paid-down
#     debt cannot silently refill un-noticed -- lowering it is a required same-
#     commit edit, not a bonus.
#   - "note" distinguishes AC8's two kinds of zero-pin: no citations extracted
#     at all (vacuously clean) vs citations extracted and all of them pass
#     (genuinely clean) vs an honest nonzero (unpaid debt).
#
# AC8 context (informational, NOT what is enforced below): the RAW sweep --
# every citation `citation_sweep.py` reports, before AC2's path-resolvability
# filter -- totals 129 at this story's base commit, four articles holding 123
# of it (demo-engine.md 73, zone-rules.md 18, core-pipeline-and-availability.md
# 17, zone-rules-history.md 15). Of the eight articles at raw-zero, SEVEN have
# no extracted citations at all (vacuously clean) and only deployment-and-
# infra.md (10 citations, all passing) is genuinely clean. The 129 are not
# silently accepted: 113 of them are bare-filename ADVISORY citations this
# story deliberately does not enforce (content-anchor coverage is filed as a
# sprint-71 follow-up, out of this story's 3 points) -- they are visible via
# `tools/citation_sweep.py` directly, not hidden by this narrower gate.
#
# THE HEADLINE RATIO, stated so a green run cannot be misread: this ratchet
# enforces 15 failures across 14 map-tier articles. Of the 129 raw, 113 are
# ADVISORY (bare filename) and 1 sits in a `tier: reference` article that AC6
# exempts. Green here means "no NEW resolvable-path drift", never "the wiki's
# citations are correct".
BASELINE: dict[str, dict] = {
    "api-five-file-convention.md": {
        "tier": "map",
        "baseline": 0,
        "note": "vacuously clean -- no citations extracted",
    },
    "api-five-file-history.md": {
        "tier": "reference",
        "baseline": None,
        "note": "exempt (AC6) -- append-only History, no live-code claims",
    },
    "architecture-boundary.md": {
        "tier": "map",
        "baseline": 0,
        "note": "vacuously clean -- no citations extracted",
    },
    "canonical-types-and-ports.md": {
        "tier": "map",
        "baseline": 0,
        "note": ("1 citation extracted, bare filename -- advisory only, 0 enforced"),
    },
    "config-layer.md": {
        "tier": "map",
        "baseline": 0,
        "note": (
            "genuinely clean on the enforced set -- every full-path citation "
            "(including the two AC7 fixed `seed_dynamo.py`/`vendor_health.py` "
            "lines, and the History prose naming their old, now-superseded "
            "values) passes on line-count; the article's one raw failure "
            "(`dispatch.py:44`) is a bare filename, advisory only (AC7)"
        ),
    },
    "core-pipeline-and-availability.md": {
        "tier": "map",
        "baseline": 0,
        "note": (
            "17 citations extracted, all bare filenames -- advisory only, 0 enforced"
        ),
    },
    "demo-engine.md": {
        "tier": "map",
        "baseline": 8,
        "note": (
            "unpaid debt -- 8 enforced failures, all a repo-relative path "
            "missing its `backend/src/` prefix (e.g. "
            "`adapters/inbound/dynatrace/query.py:83`); 65 more raw failures "
            "are bare-filename advisory, not enforced here"
        ),
    },
    "deployment-and-infra.md": {
        "tier": "reference",
        "baseline": None,
        "note": (
            "exempt (AC6) -- converted to tier: reference as a decommission "
            "tombstone (STORY-222, 2026-08-13); its 10 citations are unchanged "
            "content and still all pass, but the ratchet no longer enforces "
            "them since a reference article makes no live-code claims"
        ),
    },
    "deployment-topology.md": {
        "tier": "reference",
        "baseline": None,
        "note": "exempt (AC6) -- reference tier",
    },
    "dynatrace-adapter.md": {
        "tier": "map",
        "baseline": 1,
        "note": (
            "unpaid debt -- 1 enforced failure "
            "(`composition/app.py:224`, missing `backend/src/` prefix)"
        ),
    },
    "frontend-zone.md": {
        "tier": "map",
        "baseline": 0,
        "note": "vacuously clean -- no citations extracted",
    },
    "ingest-service-and-pull-loop.md": {
        "tier": "map",
        "baseline": 0,
        "note": ("1 citation extracted, bare filename -- advisory only, 0 enforced"),
    },
    "persistence-adapters.md": {
        "tier": "map",
        "baseline": 0,
        "note": ("1 citation extracted, bare filename -- advisory only, 0 enforced"),
    },
    "sample-mode.md": {
        "tier": "map",
        "baseline": 0,
        "note": "vacuously clean -- no citations extracted",
    },
    "statuspage-publish.md": {
        "tier": "map",
        "baseline": 0,
        "note": "vacuously clean -- no citations extracted",
    },
    "zone-rules.md": {
        "tier": "map",
        "baseline": 6,
        "note": (
            "unpaid debt -- 6 enforced failures (5 anchor-mismatch, 1 path "
            "missing its `backend/src/` prefix); 12 more raw failures are "
            "bare-filename advisory, not enforced here"
        ),
    },
    "zone-rules-history.md": {
        "tier": "reference",
        "baseline": None,
        "note": (
            "exempt (AC6) -- append-only History, citations into past state "
            "a HEAD-resolving tool cannot judge"
        ),
    },
}


def test_ac3_glob_matches_exactly_the_committed_baseline_keys() -> None:
    """The literal glob `docs/scrum/wiki/*.md` (top-level only) must name
    exactly the 17 articles this baseline covers -- no more, no fewer. A
    mismatch means either a new article landed with no baseline entry (AC4
    would silently default it to unlimited if this test did not exist) or a
    baseline entry survives for an article that is gone."""
    found = {p.name for p in gate.wiki_articles(_REPO_ROOT)}
    assert found == set(BASELINE), (
        f"docs/scrum/wiki/*.md (top-level) found {sorted(found)}, "
        f"baseline covers {sorted(BASELINE)} -- add/remove a BASELINE entry"
    )
    assert len(found) == 17, f"expected 17 top-level articles, found {len(found)}"


def test_ac3_archive_directory_is_out_of_scope() -> None:
    """`docs/scrum/wiki/archive/` must never appear in `wiki_articles()` --
    the glob is non-recursive by construction, but this pins that behaviour
    directly rather than trusting `Path.glob`'s semantics from memory."""
    archive_dir = _REPO_ROOT / "docs" / "scrum" / "wiki" / "archive"
    assert archive_dir.is_dir(), "fixture assumption: archive/ exists"
    found = {p for p in gate.wiki_articles(_REPO_ROOT)}
    assert not any("archive" in p.parts for p in found)


def test_ac2_partition_covers_every_extracted_citation() -> None:
    """For every article, the four partition_citations buckets
    (enforced_ok, enforced_fail, advisory_ok, advisory_fail) must together
    account for exactly the distinct (path, line-spec) pairs `citation_sweep`
    itself extracts -- cross-checked against the sweep's own `sweep()` return
    value, so the partition can never silently drop or double-count a
    citation relative to the tool it wraps."""
    import citation_sweep as sweep

    wiki_dir = _REPO_ROOT / "docs" / "scrum" / "wiki"
    for article in sorted(wiki_dir.glob("*.md")):
        _failures, total_occurrences = sweep.sweep(article, _REPO_ROOT)
        text = article.read_text(encoding="utf-8")
        distinct = len(
            {
                (m.group(1), m.group(2), m.group(3))
                for m in sweep.CITATION_RE.finditer(text)
            }
        )
        enforced_ok, enforced_fail, advisory_ok, advisory_fail = (
            gate.partition_citations(_REPO_ROOT, article)
        )
        partitioned_total = (
            len(enforced_ok)
            + len(enforced_fail)
            + len(advisory_ok)
            + len(advisory_fail)
        )
        assert partitioned_total == distinct, (
            f"{article.name}: partition accounts for {partitioned_total} "
            f"distinct citations, sweep extracted {distinct}"
        )
        assert total_occurrences >= distinct


def test_ac6_reference_tier_articles_are_read_from_frontmatter() -> None:
    """AC6's exemption is mechanical: for every article the glob finds,
    `gate.article_tier` (a live frontmatter read) must agree with this
    baseline's descriptive `"tier"` field -- so a future author cannot grant
    an exemption by editing this table alone without also changing the
    article's own frontmatter."""
    for article in gate.wiki_articles(_REPO_ROOT):
        live_tier = gate.article_tier(article)
        expected_tier = BASELINE[article.name]["tier"]
        assert live_tier == expected_tier, (
            f"{article.name}: frontmatter tier is {live_tier!r}, baseline "
            f"table says {expected_tier!r} -- one of the two is wrong"
        )
        if live_tier == "reference":
            assert BASELINE[article.name]["baseline"] is None
        else:
            assert isinstance(BASELINE[article.name]["baseline"], int)


def test_ac4_ac6_enforced_citation_count_matches_baseline_exactly() -> None:
    """The ratchet (AC4): for every MAP-tier article (`tier: reference` is
    exempt, decided live from frontmatter -- AC6, never from a hand-listed
    filename), today's ENFORCED failure count must equal the committed
    baseline EXACTLY. Above baseline is new drift; below baseline is paid-
    down debt that must lower the baseline in the same commit (AC4) -- both
    fail here, deliberately, so debt cannot silently refill. An article the
    glob finds but this baseline does not cover fails via
    `test_ac3_glob_matches_exactly_the_committed_baseline_keys` first.
    """
    mismatches = []
    for article in gate.wiki_articles(_REPO_ROOT):
        if gate.article_tier(article) == "reference":
            continue  # AC6 -- exempt, read live from frontmatter.
        entry = BASELINE[article.name]
        _, enforced_fail, _, _ = gate.partition_citations(_REPO_ROOT, article)
        actual = len(enforced_fail)
        if actual != entry["baseline"]:
            direction = "ABOVE" if actual > entry["baseline"] else "BELOW"
            mismatches.append(
                f"{article.name}: baseline={entry['baseline']}, actual={actual} "
                f"({direction} baseline) -- "
                + (
                    "new citation drift, fix it or file it"
                    if direction == "ABOVE"
                    else (
                        "paid-down debt -- LOWER the baseline in this commit, OR "
                        "the enforced set shrank for another reason (e.g. a "
                        "classifier change demoting enforced citations to "
                        "advisory). READ the list below before lowering: "
                        "lowering it against the wrong cause bakes in a "
                        "coverage loss"
                    )
                )
                + ":\n    "
                + "\n    ".join(enforced_fail)
            )

    assert not mismatches, "Citation ratchet mismatch(es):\n\n" + "\n\n".join(
        mismatches
    )


def test_ac5d_control_wrong_but_in_range_line_stays_green() -> None:
    """AC5(d) -- the control that makes AC5(a) mean anything. A full
    repo-relative path with a WRONG but in-range line number is
    indistinguishable, to this tool, from a correct one: both resolve and
    both pass the line-count check (no excerpt anchor to catch the content
    drift). Pinned directly against `citation_sweep.check_citation` -- the
    function `partition_citations` calls, never re-implemented -- using
    `scripts/seed_topology.py`, the story's own worked example."""
    import citation_sweep as sweep

    target = _REPO_ROOT / "scripts" / "seed_topology.py"
    real_line_count = len(target.read_text(encoding="utf-8").splitlines())
    assert real_line_count >= 44, "fixture assumption: file has >= 44 lines"

    # `:44` is the story's own decisive example -- the real content moved to
    # `:48` (config-layer.md's History), but `:44` is still a valid, in-range
    # line, so this reports OK for the wrong reason.
    ok, msg = sweep.check_citation(
        _REPO_ROOT, "scripts/seed_topology.py", 44, None, None
    )
    assert ok, f"expected the wrong-but-in-range control to PASS, got: {msg}"

    # And a line past the end of the file is the actual, detectable failure
    # (AC5(a)'s shape) -- recorded here so the two are read side by side.
    out_of_range = real_line_count + 1
    ok2, msg2 = sweep.check_citation(
        _REPO_ROOT, "scripts/seed_topology.py", out_of_range, None, None
    )
    assert not ok2, f"expected an out-of-range line to FAIL, got: {msg2}"


def test_ac1_docstring_scope_numbers_are_current() -> None:
    """The module docstring's anchor-coverage numbers, re-derived live.

    Added 2026-08-13 after quality review found the original "8 of 195" wrong
    twice over: 195 was the base-commit denominator that THIS STORY'S OWN
    edits moved to 198, and 8 counted the passing subset while the sentence
    described the checked set. That is the failure class this whole story
    exists to attack -- a number in prose that a later commit silently
    invalidates -- so the fix is not a better number, it is a check.

    Falsified by: any edit that changes the repo's citation population without
    updating the docstring sentence above. That is the single observation this
    test exists to catch.
    """
    import citation_sweep as sweep

    total = anchored = anchored_ok = 0
    for article in gate.wiki_articles(_REPO_ROOT):
        seen: set[tuple[str, int, int | None]] = set()
        for m in sweep.CITATION_RE.finditer(article.read_text(encoding="utf-8")):
            path_str, l1, l2, _excerpt_full, anchor = m.groups()
            key = (path_str, int(l1), int(l2) if l2 else None)
            if key in seen:
                continue
            seen.add(key)
            total += 1
            if anchor:
                anchored += 1
                ok, _ = sweep.check_citation(
                    _REPO_ROOT, path_str, int(l1), int(l2) if l2 else None, anchor
                )
                anchored_ok += 1 if ok else 0

    assert (anchored, total) == (13, 198), (
        f"the module docstring says 13 of 198 distinct citations carry an "
        f"excerpt anchor; live measurement says {anchored} of {total}. Update "
        f"the docstring sentence AND this assertion in the same commit."
    )
    assert anchored_ok == 8, (
        f"the docstring says 8 of the {anchored} anchored citations pass; live "
        f"measurement says {anchored_ok}."
    )


def test_ac2_classifier_keeps_its_teeth_when_the_debt_is_paid_to_zero() -> None:
    """A known repo-relative citation must land in an ENFORCED bucket, never
    advisory.

    Added 2026-08-13 after quality review. Today the classifier is guarded
    only as a side effect: three articles carry a nonzero baseline, so a
    change demoting enforced citations to advisory reds the ratchet from
    BELOW. That guard EVAPORATES the day the debt is paid to zero everywhere
    -- exactly when someone would trust this gate most -- because
    `test_ac2_partition_covers_every_extracted_citation` checks the partition
    TOTAL and never the split.

    Falsified by: a classifier change that routes a path containing `/` to
    advisory. This test does not depend on any baseline being nonzero.
    """
    article = _REPO_ROOT / "docs" / "scrum" / "wiki" / "deployment-and-infra.md"
    enforced_ok, enforced_fail, advisory_ok, advisory_fail = gate.partition_citations(
        _REPO_ROOT, article
    )

    assert enforced_ok or enforced_fail, (
        "deployment-and-infra.md's citations are all repo-relative paths, so at "
        "least one must be ENFORCED. An empty enforced set here means the "
        "path-resolvability classifier has stopped discriminating -- the whole "
        "gate would then be advisory-only while still reporting green."
    )
    assert not advisory_ok and not advisory_fail, (
        "deployment-and-infra.md carries no bare-filename citations today; "
        f"got {len(advisory_ok) + len(advisory_fail)} advisory. If a bare "
        "filename was legitimately added, move this pin to another "
        "all-repo-relative article rather than relaxing it."
    )
