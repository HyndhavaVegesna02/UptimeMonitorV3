"""Self-tests for yt_wiki.py — frontmatter parsing, coverage logic, sweep skips.

Pins the sprint-44 bug class: a trailing `# comment` on the status: line made
an article invisible to the sweep (silent trusted-and-wrong hole), and the
facts/links regex behaviors the compile pass depends on.
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yt_wiki  # noqa: E402

ARTICLE = """---
title: Sample
code_refs: [src/a.py, src/pkg/, 'docs spaced/file.md']
verified_sha: abc1234
verified_sprint: sprint-9
status: verified          # verified | stale | archived
---

## Facts (verified against code)
- Fact one cites `src/a.py::func` and `pyproject.toml`.
- Cross-ref [[other-article]] and history `docs/scrum/wiki/other-article.md`.

## Inference
- Not a fact: `never/scanned.py` lives outside the Facts section.
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
