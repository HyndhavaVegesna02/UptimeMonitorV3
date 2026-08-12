"""Self-tests for yt_wiki.py — frontmatter parsing, coverage logic, sweep skips.

Pins the sprint-44 bug class: a trailing `# comment` on the status: line made
an article invisible to the sweep (silent trusted-and-wrong hole), and the
facts/links regex behaviors the compile pass depends on.

`DerivedBaselineTests` pins the 2026-08-12 change: the staleness baseline is the
article's own last commit, not a stored `verified_sha`. Those tests run against
a REAL throwaway git repo, because the behaviour under test IS git arithmetic —
a fake would only assert what the fake was told.
"""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yt_wiki  # noqa: E402

ARTICLE = """---
title: Sample
tier: map
code_refs: [src/a.py, src/pkg/, 'docs spaced/file.md']
verified_sprint: sprint-9
status: verified          # verified | stale | archived
---

## Facts (verified against code)
- Fact one cites `src/a.py::func` and `pyproject.toml`.
- Cross-ref [[other-article]] and history `docs/scrum/wiki/other-article.md`.

## Inference
- Not a fact: `never/scanned.py` lives outside the Facts section.
"""

REFERENCE_ARTICLE = """---
title: Why polling was removed
tier: reference
status: verified
---

## Inference
- Polling caused thundering-herd load; websocket push replaced it in STORY-023.
"""


class FrontmatterTests(unittest.TestCase):
    def test_trailing_comment_stripped_from_status(self):
        meta = yt_wiki.parse_frontmatter(ARTICLE)
        self.assertEqual(meta["status"], "verified")

    def test_code_refs_inline_list_parsed(self):
        meta = yt_wiki.parse_frontmatter(ARTICLE)
        self.assertEqual(
            meta["code_refs"], ["src/a.py", "src/pkg/", "docs spaced/file.md"]
        )

    def test_no_frontmatter_returns_empty(self):
        self.assertEqual(yt_wiki.parse_frontmatter("# just a doc\n"), {})


class FactsAndCoverageTests(unittest.TestCase):
    def test_facts_section_bounded_by_next_heading(self):
        section = yt_wiki.facts_section(ARTICLE)
        self.assertIn("Fact one", section)
        self.assertNotIn("never/scanned.py", section)

    def test_cite_regex_strips_symbol_suffix(self):
        cites = yt_wiki.CITE_RE.findall(yt_wiki.facts_section(ARTICLE))
        self.assertIn("src/a.py", cites)
        self.assertIn("pyproject.toml", cites)

    def test_covered_exact_dir_prefix_and_slashes(self):
        refs = ["src/a.py", "src/pkg/"]
        self.assertTrue(yt_wiki.covered("src/a.py", refs))
        self.assertTrue(yt_wiki.covered("src/pkg/deep/mod.py", refs))
        self.assertTrue(yt_wiki.covered("src\\pkg\\deep\\mod.py", refs))
        self.assertFalse(yt_wiki.covered("src/other.py", refs))

    def test_check_facts_flags_existing_uncovered_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pyproject.toml").write_text("x", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "a.py").write_text("x", encoding="utf-8")
            findings = yt_wiki.check_facts(root, {root / "art.md": ARTICLE})
            joined = "\n".join(findings)
            self.assertIn("pyproject.toml", joined)  # exists, uncovered
            self.assertNotIn("src/a.py", joined)  # covered
            self.assertNotIn("docs/scrum", joined)  # wiki cross-ref: links' domain


class SweepSkipTests(unittest.TestCase):
    def _sweep(self, text: str):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "art.md"
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                findings = yt_wiki.check_sweep(Path(td), {path: text}, update=False)
            return findings, out.getvalue()

    def test_stale_article_noted_not_finding(self):
        findings, out = self._sweep(
            ARTICLE.replace("status: verified", "status: stale")
        )
        self.assertEqual(findings, [])
        self.assertIn("not swept (status=stale)", out)

    def test_unrecognized_status_is_a_finding(self):
        findings, _ = self._sweep(
            ARTICLE.replace("status: verified", "status: verfied")
        )
        self.assertEqual(len(findings), 1)
        self.assertIn("UNRECOGNIZED", findings[0])

    def test_reference_tier_is_noted_not_swept(self):
        findings, out = self._sweep(REFERENCE_ARTICLE)
        self.assertEqual(findings, [])
        self.assertIn("not swept (tier=reference", out)

    def test_unrecognized_tier_is_a_finding(self):
        findings, _ = self._sweep(ARTICLE.replace("tier: map", "tier: mapp"))
        self.assertEqual(len(findings), 1)
        self.assertIn("UNRECOGNIZED tier", findings[0])

    def test_map_article_without_code_refs_is_a_finding(self):
        text = ARTICLE.replace(
            "code_refs: [src/a.py, src/pkg/, 'docs spaced/file.md']\n", ""
        )
        findings, _ = self._sweep(text)
        self.assertEqual(len(findings), 1)
        self.assertIn("no code_refs", findings[0])

    def test_absent_tier_defaults_to_map_and_is_swept(self):
        # Backward compatibility: every article predating the tier split is a map.
        text = ARTICLE.replace("tier: map\n", "")
        findings, out = self._sweep(text)
        self.assertEqual(findings, [])
        self.assertIn("uncommitted article", out)  # reached the baseline step


def _run(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


class DerivedBaselineTests(unittest.TestCase):
    """The baseline is the article's own last commit (2026-08-12)."""

    @contextlib.contextmanager
    def _repo(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _run(root, "init", "-q", "-b", "main")
            _run(root, "config", "user.email", "t@example.invalid")
            _run(root, "config", "user.name", "test")
            (root / "src").mkdir()
            (root / "src" / "a.py").write_text("v1\n", encoding="utf-8")
            _run(root, "add", "src/a.py")
            _run(root, "commit", "-qm", "code")
            yield root

    def _sweep(self, root: Path, path: Path):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            findings = yt_wiki.check_sweep(
                root, {path: path.read_text(encoding="utf-8")}, update=False
            )
        return findings, out.getvalue()

    def _write_article(self, root: Path, text: str = ARTICLE) -> Path:
        path = root / "art.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_code_committed_after_the_article_is_stale(self):
        with self._repo() as root:
            path = self._write_article(root)
            _run(root, "add", "art.md")
            _run(root, "commit", "-qm", "article")
            (root / "src" / "a.py").write_text("v2 — real change\n", encoding="utf-8")
            _run(root, "add", "src/a.py")
            _run(root, "commit", "-qm", "code moved under the article")
            findings, _ = self._sweep(root, path)
            self.assertEqual(len(findings), 1, findings)
            self.assertIn("STALE", findings[0])

    def test_article_committed_after_the_code_is_clean(self):
        with self._repo() as root:
            (root / "src" / "a.py").write_text("v2\n", encoding="utf-8")
            _run(root, "add", "src/a.py")
            _run(root, "commit", "-qm", "code first")
            path = self._write_article(root)
            _run(root, "add", "art.md")
            _run(root, "commit", "-qm", "article re-verified after the code change")
            findings, _ = self._sweep(root, path)
            self.assertEqual(findings, [])

    def test_article_and_code_in_the_SAME_commit_is_clean(self):
        # The case that produced eight "fix verified_sha self-reference" commits:
        # under a stored stamp the bump could never name its own commit. Derived,
        # the article's commit IS the baseline, so a joint commit is trivially clean.
        with self._repo() as root:
            path = self._write_article(root)
            (root / "src" / "a.py").write_text("v2\n", encoding="utf-8")
            _run(root, "add", "art.md", "src/a.py")
            _run(root, "commit", "-qm", "code + article together")
            findings, _ = self._sweep(root, path)
            self.assertEqual(findings, [])

    def test_uncommitted_article_is_noted_not_a_finding(self):
        with self._repo() as root:
            path = self._write_article(root)  # written, never committed
            findings, out = self._sweep(root, path)
            self.assertEqual(findings, [])
            self.assertIn("uncommitted article", out)

    def test_whitespace_only_code_change_does_not_stale(self):
        with self._repo() as root:
            path = self._write_article(root)
            _run(root, "add", "art.md")
            _run(root, "commit", "-qm", "article")
            (root / "src" / "a.py").write_text("v1\n\n\n", encoding="utf-8")
            _run(root, "add", "src/a.py")
            _run(root, "commit", "-qm", "reformat only")
            findings, out = self._sweep(root, path)
            self.assertEqual(findings, [])
            self.assertIn("format-only drift", out)
            # No stamp to bump: the article must be untouched on disk.
            self.assertEqual(path.read_text(encoding="utf-8"), ARTICLE)


class IntegrityTests(unittest.TestCase):
    def _integrity(self, name: str, text: str):
        with tempfile.TemporaryDirectory() as td:
            wiki = Path(td)
            return yt_wiki.check_integrity(wiki, {wiki / name: text})

    def test_forty_char_sha_is_no_longer_flagged(self):
        # The short-sha rule retired with the field it guarded (2026-08-12).
        text = ARTICLE.replace("tier: map", "tier: map\nverified_sha: " + "a" * 40)
        self.assertEqual(self._integrity("art.md", text), [])

    def test_fake_archive_still_flagged(self):
        text = ARTICLE.replace("status: verified", "status: archived")
        findings = self._integrity("art.md", text)
        self.assertEqual(len(findings), 1)
        self.assertIn("main wiki dir", findings[0])

    def test_reference_with_code_refs_is_a_finding(self):
        text = REFERENCE_ARTICLE.replace(
            "tier: reference", "tier: reference\ncode_refs: [src/a.py]"
        )
        findings = self._integrity("why.md", text)
        self.assertEqual(len(findings), 1)
        self.assertIn("declares code_refs", findings[0])

    def test_reference_with_facts_section_is_a_finding(self):
        text = REFERENCE_ARTICLE + "\n## Facts (verified against code)\n- `src/a.py`\n"
        findings = self._integrity("why.md", text)
        self.assertEqual(len(findings), 1)
        self.assertIn("`## Facts` section", findings[0])

    def test_clean_reference_article_passes(self):
        self.assertEqual(self._integrity("why.md", REFERENCE_ARTICLE), [])


class RetiredC3Tests(unittest.TestCase):
    """The c3 catalogue-lag check was deleted, not disabled (2026-08-12).

    Derived staleness IS its satisfiable half, and sprint-69's retro redrafted its
    "same commit" premise to "same STORY, no false intermediate" — which arithmetic
    cannot check. Asserted so the deletion cannot silently regrow.
    """

    def test_check_c3_is_gone(self):
        self.assertFalse(hasattr(yt_wiki, "check_c3"))
        self.assertFalse(hasattr(yt_wiki, "_blob_text"))

    def test_range_flag_is_gone(self):
        proc = subprocess.run(
            [sys.executable, str(Path(yt_wiki.__file__)), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertNotIn("--range", proc.stdout)
        self.assertNotIn("c3", proc.stdout)


class LinkTests(unittest.TestCase):
    def test_broken_and_resolved_links(self):
        with tempfile.TemporaryDirectory() as td:
            wiki = Path(td)
            (wiki / "archive").mkdir()
            (wiki / "other-article.md").write_text("x", encoding="utf-8")
            text = "See [[other-article]] and [[missing-one]]."
            findings = yt_wiki.check_links(wiki, wiki, {wiki / "a.md": text})
            self.assertEqual(len(findings), 1)
            self.assertIn("missing-one", findings[0])


if __name__ == "__main__":
    unittest.main()
