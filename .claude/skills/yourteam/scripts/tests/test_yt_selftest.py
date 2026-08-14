"""Self-tests for yt_selftest.py -- AC4 (STORY-224).

`unittest.defaultTestLoader.discover` fails SILENTLY when a module stops
being discovered: an import error surfaces as a loud synthetic failing test,
but a rename or a file falling outside the `test_*.py` glob makes the
discovered-module count drop with no error at all. `yt_selftest.py` gains a
floor on that count so a silent drop fails the RUN, not just quietly changes
what the next standup happens to see.

Falsified by: a module dropping out of discovery (renamed, or removed) and
`yt_selftest.py` still exiting 0.
"""

from __future__ import annotations

import itertools
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yt_selftest  # noqa: E402

REAL_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
YT_SELFTEST_PATH = REAL_SCRIPTS_DIR / "yt_selftest.py"
REAL_TESTS_DIR = Path(__file__).resolve().parent
#: .../skills/yourteam -- the whole skill, not just scripts/. test_template_parity.py
#: reaches sideways into `SKILL / "templates"`, so a copy of `scripts/` ALONE fails
#: it for a reason that has nothing to do with a dropped module (measured: 1 real
#: failure + 6 real errors from missing siblings, in a first version of this proof).
REAL_SKILL_DIR = Path(__file__).resolve().parents[2]

#: `unittest.discover` caches imported module NAMES process-wide, so two
#: separate tempdirs each holding a `test_m0.py` collide the second time
#: (`ImportError: 'test_m0' module incorrectly imported from ...`). Every
#: synthetic module gets a globally-unique name to avoid that -- an artifact
#: of running discovery repeatedly in one process, not of the code under test.
_UNIQUE = itertools.count()


def _write_passing_module(tests_dir: Path, prefix: str) -> str:
    name = f"test_{prefix}_{next(_UNIQUE)}"
    (tests_dir / f"{name}.py").write_text(
        "import unittest\n\n\n"
        "class T(unittest.TestCase):\n"
        "    def test_x(self) -> None:\n"
        "        self.assertTrue(True)\n",
        encoding="utf-8",
    )
    return name


class ModuleDiscoveryFunctionsTests(unittest.TestCase):
    """Unit-level pin, decoupled from a subprocess."""

    def test_real_tests_dir_has_at_least_the_stated_floor(self) -> None:
        modules = yt_selftest.discovered_test_modules(REAL_TESTS_DIR)
        self.assertGreaterEqual(
            len(modules), yt_selftest.MIN_TEST_MODULES, sorted(modules)
        )

    def test_synthetic_modules_at_the_floor_are_all_discovered(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tests_dir = Path(td)
            (tests_dir / "__init__.py").write_text("", encoding="utf-8")
            for _ in range(yt_selftest.MIN_TEST_MODULES):
                _write_passing_module(tests_dir, "m")
            modules = yt_selftest.discovered_test_modules(tests_dir)
            self.assertEqual(
                len(modules), yt_selftest.MIN_TEST_MODULES, sorted(modules)
            )

    def test_a_module_renamed_out_of_the_pattern_silently_drops_the_count(self) -> None:
        """This IS the defect AC4 guards -- discovery itself never errors."""
        with tempfile.TemporaryDirectory() as td:
            tests_dir = Path(td)
            (tests_dir / "__init__.py").write_text("", encoding="utf-8")
            floor = yt_selftest.MIN_TEST_MODULES
            names = [_write_passing_module(tests_dir, "m") for _ in range(floor)]
            self.assertEqual(len(yt_selftest.discovered_test_modules(tests_dir)), floor)

            last = names[-1]
            # Renamed OUT of the `test_*.py` glob -- a real "no longer discovered",
            # not just a differently-named module that discovery still finds.
            (tests_dir / f"{last}.py").rename(tests_dir / "dropped_not_a_test_file.py")
            self.assertEqual(
                len(yt_selftest.discovered_test_modules(tests_dir)), floor - 1
            )


class MainExitCodeTests(unittest.TestCase):
    """End-to-end through the real script, as a subprocess.

    `yt_selftest.py` resolves its `tests/` directory off its own `__file__`,
    so a copy of the script alongside a scratch `tests/` directory exercises
    the real `main()` unmodified, no CLI override needed in production code.
    """

    def _scratch_script(self, module_count: int) -> Path:
        # MINOR, STORY-224 fix round (quality reviewer): `tempfile.mkdtemp()`
        # has no matching cleanup and leaked 2 directories per run (measured
        # 78 -> 80) -- on a suite that now runs on EVERY gate. `addCleanup`
        # ties removal to the test's own lifecycle, success or failure.
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        root = Path(tmpdir.name)
        shutil.copy(YT_SELFTEST_PATH, root / "yt_selftest.py")
        tests_dir = root / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        for i in range(module_count):
            _write_passing_module(tests_dir, f"m{i}")
        return root / "yt_selftest.py"

    def test_at_the_floor_passes_and_exits_0(self) -> None:
        script = self._scratch_script(yt_selftest.MIN_TEST_MODULES)
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=script.parent,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_one_module_short_of_the_floor_exits_nonzero_and_says_why(self) -> None:
        """AC4 shown RED: a silent drop must fail the RUN, not just note it."""
        short = yt_selftest.MIN_TEST_MODULES - 1
        script = self._scratch_script(short)
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=script.parent,
            capture_output=True,
            text=True,
        )
        combined = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, combined)
        self.assertIn(f"{short} test module", combined)


class RealTestsDirDriftTests(unittest.TestCase):
    """STORY-224 fix round, MAJOR 1 (both reviewers, independently).

    The synthetic exactly-N/N-1 fixtures above pin the MECHANISM but were the
    ONLY proof offered for AC4's shown-RED, and both reviewers found that
    `MIN_TEST_MODULES = 7` was already one behind the REAL tree (8 modules
    after this story added `test_yt_selftest.py` itself) -- so the actual
    failure mode neither review needed to imagine, dropping this suite's own
    file, passed silently: `Ran 94 tests ... OK`, exit 0, with every test of
    the AC4 mechanism itself gone. This copies the REAL `scripts/` directory
    (not a synthetic fixture) and drops `test_yt_selftest.py` from the copy.
    """

    def test_dropping_test_yt_selftest_py_itself_reds_the_real_tree(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            scratch_skill = Path(td) / "yourteam"
            shutil.copytree(
                REAL_SKILL_DIR,
                scratch_skill,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            (scratch_skill / "scripts" / "tests" / "test_yt_selftest.py").unlink()
            proc = subprocess.run(
                [sys.executable, str(scratch_skill / "scripts" / "yt_selftest.py")],
                cwd=scratch_skill / "scripts",
                capture_output=True,
                text=True,
            )
            combined = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, combined)


if __name__ == "__main__":
    unittest.main()
