"""Standing guard (STORY-219): wires `tools/citation_sweep.py`'s citation
RESOLUTION into `python -m pytest` via a per-article ratchet baseline, instead
of the tool sitting unused (filed against sprint-68's RC-2: five `file:line`
citations went stale under a commit that never touched their content).

**What this test proves, stated exactly because the honest scope is narrower
than "citations are correct" (AC1):** for every citation whose path resolves
from the repo root (a repo-relative path, not a bare filename), the cited
file exists and is long enough to contain the cited line. The cited CONTENT
is verified only for the minority of citations carrying a parenthesized
excerpt anchor (`` `path:line` (`excerpt`) ``) -- **13 of 191 distinct
citations repo-wide carry one and get a content check; 8 pass and 5 fail**
(the 5 are zone-rules.md's own anchor-mismatch baseline). Corrected
2026-08-13 after quality review: the earlier "8 of 195" was wrong twice --
195 was the BASE-COMMIT denominator, which this very story's edits to
config-layer.md and zone-rules.md moved to 198, and 8 counted the PASSING
subset while the sentence described the CHECKED set. "Distinct" means
per-article dedupe summed across articles (`partition_citations` resets its
`seen` set per article), NOT globally distinct -- which is a SEPARATE,
smaller number (deduped on `(path, l1, l2)` across ALL articles combined,
one `seen` set, not one per article) -- and stating either number without
its method is how the first version rotted. Re-corrected
2026-08-13 (STORY-222 fix round): `deployment-and-infra.md`'s 10 citations
were de-lined when that article became a decommission tombstone (its
`file:line` claims into `infra/stack.yaml`/`scripts/create_tables.py` were
no longer checkable at `tier: reference`), dropping the distinct total from
198 to 188 -- the anchored count (13) and the anchored-passing count (8) are
unaffected, none of those 10 carried an excerpt anchor. Re-corrected again
2026-08-16 (STORY-147): the wiki blast-radius pass net-added two distinct,
non-anchored citations -- `config-layer.md` gained
`backend/src/adapters/outbound/statuspage/__init__.py:54` and re-keyed
`seed_dynamo.py:60` to `:76` (net +1 distinct), and `zone-rules.md` gained
the bare-filename `component.py:17` (net +1 distinct, advisory-only per the
path-resolvability filter above) -- moving the per-article-summed total from
188 to 190, AND (missed in the first pass at this same commit, caught at
quality review) the globally-distinct count from 176 to 178. The anchored
count (13) and the anchored-passing count (8) are unaffected, since none of
those citations carry an excerpt anchor. Moved again 2026-08-16 (STORY-155b,
detailed in `test_ac1_docstring_scope_numbers_are_current`'s own extended
docstring below): zone-rules.md's harness.py re-key added one new distinct
citation net, moving total 190 -> 191 and globally-distinct 178 -> 179 -- a
move this LEAD sentence was never updated for, so it silently read "13 of
190" while the live value was 191 for the rest of sprint 73, until this
very correction. STORY-228 touched this population twice at fix round.
AC2 consolidated zone-rules.md's four STORY-155b re-verification blocks
into one but re-quoted its sole unique advisory citation (`harness.py:62-69`,
which occurs nowhere else in that article), contributing zero net change.
AC3's FIRST attempt de-lined a citation into
`backend/src/adapters/outbound/statuspage/__init__.py` that config-layer.md
carried twice (neither occurrence covered by that article's `code_refs`),
which would have removed it from the citation population -- but that
regressed a DIFFERENT check (`yt_wiki.py facts`, whose `CITE_RE` matches a
bare backticked path with no line number, unlike this gate's `CITATION_RE`,
which requires one) and did not fix the underlying harm (the file was still
absent from `code_refs`), so it was reverted at review. **Resolved instead
by adding the file to `config-layer.md`'s `code_refs` and restoring both
`:54` citations** -- the harm AC3 was filed for is fixed (the file is now a
`code_ref`, so drift there re-triggers this article), and the citation
population is UNCHANGED: total stays 191, globally-distinct stays 179, both
still the STORY-155b values this LEAD sentence now finally reflects. The
anchored count (13) and anchored-passing count (8) are unaffected by any of
this; none of the touched citations carry an excerpt anchor.
`test_ac1_docstring_scope_numbers_are_current` re-derives all FOUR numbers
live -- `anchored`, `total`, `anchored_ok`, and now the globally-distinct
count (179) named just above -- so none of this sentence's numbers can go
stale silently again; the earlier "re-derives all three" claim was itself
false (it asserted three, this docstring stated four, and 186/178 was the
fourth left unchecked). **A wrong-but-in-range line
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
# recursive) -- 16 articles (was 17 before STORY-155b archived sample-mode.md
# to docs/scrum/wiki/archive/). `docs/scrum/wiki/archive/` is a subdirectory
# and is OUT of scope; this is stated here, not left as a 16-vs-19 ambiguity.
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
# filter -- totals 129 at this story's (STORY-219) base commit, four articles
# holding 123 of it (demo-engine.md 73, zone-rules.md 18,
# core-pipeline-and-availability.md 17, zone-rules-history.md 15). Of the
# eight articles at raw-zero, SEVEN have no extracted citations at all
# (vacuously clean); deployment-and-infra.md (10 citations, all passing) was
# the eighth, "genuinely clean" one -- but STORY-222 (2026-08-13) converted it
# to `tier: reference` as a decommission tombstone and de-lined its 10
# citations (they no longer carry a line number at all, so `CITATION_RE` no
# longer extracts them; see the module docstring's 198->188 correction
# above). It is EXEMPT today (AC6, read live from frontmatter), not
# "genuinely clean" -- there is nothing left for AC2's partition to count.
# The 129 raw at STORY-219's base are not silently accepted: 113 of them are
# bare-filename ADVISORY citations this story deliberately does not enforce
# (content-anchor coverage is filed as a sprint-71 follow-up, out of this
# story's 3 points) -- they are visible via `tools/citation_sweep.py`
# directly, not hidden by this narrower gate.
#
# THE HEADLINE RATIO, stated so a green run cannot be misread: this ratchet
# enforces 15 failures across 12 map-tier articles (was 13 before STORY-155b
# archived sample-mode.md, a vacuously-clean map article that contributed 0
# to the failure count -- `test_ac1_docstring_scope_
# numbers_are_current` re-derives both numbers live, so this cannot go stale
# silently). Of the 129 raw at STORY-219's base, 113 are ADVISORY (bare
# filename) and 1 sits in a `tier: reference` article that AC6 exempts. Green
# here means "no NEW resolvable-path drift", never "the wiki's citations are
# correct".
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
            "tombstone (STORY-222, 2026-08-13). Its 10 `file:line` citations "
            "into infra/stack.yaml and scripts/create_tables.py were de-lined "
            "in the same story's fix round: at tier: reference the article "
            "makes no live-code claim, so a line number pointing at a file "
            "that is still gated and could drift out from under it was a "
            "false checkable claim, not a harmless one -- restoring the "
            "'## Facts' heading in a scratch copy re-triggers the integrity/ "
            "facts lints, proving the tier is honest now, not just declared. "
            "The bare filenames remain as navigation; CITATION_RE requires a "
            "line number, so none of the 10 are extracted as citations at "
            "all anymore -- there is nothing for this ratchet to enforce or "
            "exempt"
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
    exactly the 16 articles this baseline covers (was 17 before STORY-155b
    archived sample-mode.md to docs/scrum/wiki/archive/) -- no more, no fewer.
    A mismatch means either a new article landed with no baseline entry (AC4
    would silently default it to unlimited if this test did not exist) or a
    baseline entry survives for an article that is gone."""
    found = {p.name for p in gate.wiki_articles(_REPO_ROOT)}
    assert found == set(BASELINE), (
        f"docs/scrum/wiki/*.md (top-level) found {sorted(found)}, "
        f"baseline covers {sorted(BASELINE)} -- add/remove a BASELINE entry"
    )
    assert len(found) == 16, f"expected 16 top-level articles, found {len(found)}"


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

    Extended 2026-08-13 (STORY-222 fix round) to also re-derive the two
    headline-ratio numbers ("15 failures across 13 map-tier articles") that a
    MAJOR from this same fix round found stale in a bare docstring sentence
    nothing asserted against -- the exact failure class this test already
    exists to attack, just not yet applied to those two numbers.

    Extended again 2026-08-16 (STORY-147 fix round) to also assert the
    globally-distinct count (deduped on ``(path, l1, l2)`` in ONE `seen` set
    across every article, not per-article-summed). The module docstring
    NAMED this number ("NOT globally distinct -- which is N") without ever
    asserting it, so a prior commit updated the per-article total (188 ->
    190) and left this one stale (186, real value 178) -- a claim of
    "cannot go stale silently" sitting beside its own live counter-example.
    Not yet applied to the globally-distinct-on-PATH-ALONE number (78) named
    in the fix-round report but not in this module's docstring.

    Re-derived 2026-08-16 (STORY-155b), in two steps. First, archiving
    sample-mode.md (a vacuously-clean, `tier: map`, `baseline: 0` article) to
    docs/scrum/wiki/archive/ removed it from the `docs/scrum/wiki/*.md` glob
    entirely, moving the map-tier-article count from 13 to 12; it contributed
    0 to `anchored`/`total`/`anchored_ok`/`globally_distinct`, so those four
    were unaffected by the archival itself. Second, this same story's
    blast-radius pass corrected zone-rules.md's own line-numbered citations
    into `tools/demo_loop_gate/harness.py`, which the same story's AC10
    shifted -- the correction added one NEW distinct (path, line) citation
    net (a corrected line number is, mechanically, a different tuple from
    the stale one it replaces), moving `total` 190 -> 191 and
    `globally_distinct` 178 -> 179. `anchored`, `anchored_ok` and
    `total_enforced_fail` are unaffected (none of the corrected citations
    carry an excerpt anchor). The headline-ratio comment above BASELINE was
    updated in the same commit as the map-tier-count move.

    Re-derived 2026-08-17 (STORY-228 AC5, first pass), from TWO independent
    edits in the same story: AC2 consolidated zone-rules.md's four separate
    STORY-155b re-verification blocks (`:57-100`, inside the frontmatter
    comment block) into one entry, re-quoting `harness.py:62-69` -- the one
    citation in that range with no other occurrence in the article -- so this
    consolidation contributed a NET-ZERO change to `total`/`globally_distinct`.
    AC3's first attempt resolved config-layer.md's citation into
    `backend/src/adapters/outbound/statuspage/__init__.py:54`, present TWICE
    (a Fact and a History entry) and outside that article's `code_refs`, by
    de-lining BOTH occurrences. That would have removed one distinct
    citation (`total` 191 -> 190, `globally_distinct` 179 -> 178).

    **Reverted at the fix round (STORY-228 AC3, second pass), same day.**
    De-lining regressed a DIFFERENT check: `yt_wiki.py facts`'s `CITE_RE`
    matches a bare backticked path with no line number (unlike this gate's
    `CITATION_RE`, which requires one), so the de-lined citation went from
    invisible to every checker to flagged by that one -- a genuine new
    failure, clean at the sprint-74 baseline. It also did not fix the harm
    AC3 was filed for: the file was still absent from `config-layer.md`'s
    `code_refs`, so drift there still could not re-trigger the article.
    Resolved instead by adding the file to `code_refs` and restoring both
    `:54` citations, which fixes the actual harm (the file is now a
    `code_ref`) without touching the citation population at all: `total`
    and `globally_distinct` are back to 191/179, the exact STORY-155b
    values, unchanged net by this story. `anchored`, `anchored_ok` and
    `total_enforced_fail`/`map_tier_count` were never affected by any of
    this -- neither touched citation carried an excerpt anchor, and the
    statuspage citation was always ENFORCED-and-passing (a `/` in its path,
    at config-layer.md's committed baseline of 0), never in the
    `enforced_fail` bucket `total_enforced_fail` counts.

    Falsified by: any edit that changes the repo's citation population, or a
    wiki article's tier, without updating the docstring sentences above.
    """
    import citation_sweep as sweep

    total = anchored = anchored_ok = 0
    globally_distinct: set[tuple[str, int, int | None]] = set()
    for article in gate.wiki_articles(_REPO_ROOT):
        seen: set[tuple[str, int, int | None]] = set()
        for m in sweep.CITATION_RE.finditer(article.read_text(encoding="utf-8")):
            path_str, l1, l2, _excerpt_full, anchor = m.groups()
            key = (path_str, int(l1), int(l2) if l2 else None)
            if key in seen:
                continue
            seen.add(key)
            total += 1
            globally_distinct.add(key)
            if anchor:
                anchored += 1
                ok, _ = sweep.check_citation(
                    _REPO_ROOT, path_str, int(l1), int(l2) if l2 else None, anchor
                )
                anchored_ok += 1 if ok else 0

    assert (anchored, total) == (13, 191), (
        f"the module docstring says 13 of 191 distinct citations carry an "
        f"excerpt anchor; live measurement says {anchored} of {total}. Update "
        f"the docstring sentence AND this assertion in the same commit."
    )
    assert anchored_ok == 8, (
        f"the docstring says 8 of the {anchored} anchored citations pass; live "
        f"measurement says {anchored_ok}."
    )
    assert len(globally_distinct) == 179, (
        f"the module docstring's method-defining clause says the GLOBALLY "
        f"distinct count (deduped on (path, l1, l2) across every article, not "
        f"per-article-summed) is 179; live measurement says "
        f"{len(globally_distinct)}. Update the docstring sentence AND this "
        f"assertion in the same commit."
    )

    map_tier_count = 0
    total_enforced_fail = 0
    for article in gate.wiki_articles(_REPO_ROOT):
        if gate.article_tier(article) != "map":
            continue
        map_tier_count += 1
        _, enforced_fail, _, _ = gate.partition_citations(_REPO_ROOT, article)
        total_enforced_fail += len(enforced_fail)

    assert (total_enforced_fail, map_tier_count) == (15, 12), (
        f"the headline ratio says 15 failures across 12 map-tier articles; "
        f"live measurement says {total_enforced_fail} failures across "
        f"{map_tier_count} map-tier articles. Update the headline-ratio "
        f"comment above BASELINE AND this assertion in the same commit."
    )


def test_ac2_classifier_keeps_its_teeth_when_the_debt_is_paid_to_zero(
    tmp_path: Path,
) -> None:
    """A known repo-relative citation must land in an ENFORCED bucket, never
    advisory.

    Added 2026-08-13 after quality review. Today the classifier is guarded
    only as a side effect: three articles carry a nonzero baseline, so a
    change demoting enforced citations to advisory reds the ratchet from
    BELOW. That guard EVAPORATES the day the debt is paid to zero everywhere
    -- exactly when someone would trust this gate most -- because
    `test_ac2_partition_covers_every_extracted_citation` checks the partition
    TOTAL and never the split.

    Re-pointed 2026-08-13 (STORY-222 fix round): this originally pinned on
    `deployment-and-infra.md`, which at the time carried 10 all-repo-relative,
    all-passing citations and no advisory ones. The same fix round de-lined
    those 10 citations (the article became a decommission tombstone at
    `tier: reference`, where a `file:line` claim into still-live code was no
    longer honest) -- `CITATION_RE` mandates a line number, so none of the 10
    are extracted at all anymore, and the article has nothing left to pin on.
    A synthetic fixture citing a real, long-enough repo file removes the
    dependency on any wiki article's *content* staying a certain shape --
    exactly the kind of drift that broke the original pin.

    Falsified by: a classifier change that routes a path containing `/` to
    advisory. This test does not depend on any baseline being nonzero.
    """
    real_path = "scripts/create_tables.py"
    real_line_count = len(
        (_REPO_ROOT / real_path).read_text(encoding="utf-8").splitlines()
    )
    article = tmp_path / "synthetic-control.md"
    article.write_text(f"See `{real_path}:{real_line_count}`.\n", encoding="utf-8")

    enforced_ok, enforced_fail, advisory_ok, advisory_fail = gate.partition_citations(
        _REPO_ROOT, article
    )

    assert enforced_ok or enforced_fail, (
        "a repo-relative path (contains '/') must land in an ENFORCED bucket. "
        "An empty enforced set here means the path-resolvability classifier "
        "has stopped discriminating -- the whole gate would then be "
        "advisory-only while still reporting green."
    )
    assert not advisory_ok and not advisory_fail, (
        "a repo-relative path must never be classified as advisory; got "
        f"{len(advisory_ok) + len(advisory_fail)} advisory."
    )
