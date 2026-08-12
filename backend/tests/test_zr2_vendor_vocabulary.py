"""ZR-2 standing guard (STORY-207): vendor vocabulary never becomes an
identifier/annotation/signature/dict-key/stored-value inside `core/`.

Cites `docs/scrum/wiki/zone-rules.md` ZR-2 -- the Statement (three closed
compliant prose forms, plus the `Provenance` carve-out) and its Coverage
verdict (the six-rule AST walk this module implements almost verbatim):
(1) `FunctionDef`/`AsyncFunctionDef`/`ClassDef` names; (2) `arg` names;
(3) `Name` ids; (4) `Attribute.attr`; (5) `keyword.arg`; (6) `Constant`
string/number values that are NOT the sole value of an `Expr` statement --
i.e. neither a real docstring nor the "attribute docstring" idiom (a bare
string-literal statement following a class-level field assignment, e.g.
`backend/src/core/domain/publication.py:66`).

**Why rule (6) needs the exclusion at all (the discrimination this guard
must get right, AC2).** A formal docstring and the attribute-docstring idiom
are BOTH, at the AST level, nothing more than `ast.Expr(value=ast.Constant)`
-- a bare string-literal statement. `ast.get_docstring` recognises only the
first of those two shapes (the first statement of a `Module`/`ClassDef`/
`FunctionDef` body); the second is invisible to it. So this walk cannot use
`ast.get_docstring` to tell prose from a forbidden stored value -- it has to
recognise the shared `Expr(Constant)` shape directly and exclude it, which
is also exactly why the exclusion can be *proven* to matter: without it,
`backend/src/core/domain/signal.py`'s module docstring and
`backend/src/core/domain/publication.py:66`'s attribute docstring -- both of
which ZR-2 already adjudicates COMPLIANT -- would flag, and an
over-triggering guard is reverted, not obeyed by editing compliant code
(`test_compliant_prose_forms_are_not_flagged` below proves this directly, by
running the walk with the exclusion turned off against those exact real
files and showing it WOULD flag them).

**The `Provenance` carve-out (AC3) is NOT implemented by this walk, and that
residue is stated here, not hidden.** ZR-2 calls a vendor word stored as
`Provenance.system` "compliant BY DESIGN -- the rule's one sanctioned data
channel, not an exception carved out of it"
(`backend/src/core/domain/signal.py:26-39`). But `Provenance(system="dynatrace")`
written inside `core/` WOULD be flagged by rule (6) above -- it is a
`Constant` argument that is not the sole value of an `Expr` statement, and
this walk draws no distinction for a `Provenance(...)` call site. That
contradiction is moot TODAY: `core/` holds no such literal (verified by grep
at STORY-207 planning), and `Provenance`'s own field-type definition
(`system: str`) contains no vendor token, so a test asserting that call
shape unflagged would be vacuous -- there is nothing real to assert against.
The correct response WHEN a `Provenance(system="...")` literal is first
written inside `core/` is a narrow exemption for `Constant` arguments to a
`Provenance(...)` call specifically -- never widening the `Expr`-sole
exclusion (which would reopen the docstring/stored-value hole this guard
exists to close) and never deleting the domain's one sanctioned vendor-data
channel to satisfy this guard.

**The TRUE residue (AC4) -- corrected from ZR-2's own text, which is false
for this six-rule walk.** ZR-2's prose names two escapes --
`def f(x: "DynatraceRow")` and `getattr(obj, "dynatrace_" + suffix)` -- that
do NOT escape this walk: both surface as rule (6) `Constant` string values
(`'DynatraceRow'`, `'dynatrace_'`) and are caught, because neither is the
sole value of an `Expr` statement. That text was written against an earlier,
narrower walk (names/`arg`/`Name` only) and was never re-derived for the
six-rule walk. What this walk genuinely cannot see: it sees a string
annotation or a `getattr`/`globals()` string argument only as an opaque
`Constant` value, with no way to distinguish "this string names a type
forward-reference or a dynamically-built identifier" from "this string is
comment-like prose" -- so any identifier ASSEMBLED FROM FRAGMENTS carrying
no whole seed token in a single `Constant` (e.g. `"dyna" + "trace_id"`, or a
seed token split across an f-string's static and interpolated parts) is
invisible to it, because no single node this walk inspects ever holds the
complete token. **ZR-2 may not be described anywhere -- this docstring, the
catalogue row, or a commit message -- as fully enforced.**

**AC9 non-vacuity floor.** `test_discovers_at_least_25_core_modules` fails
loudly if module discovery ever returns fewer than 25 modules (a wrong root
or a moved package), rather than the other two tests silently iterating over
nothing and passing. Do not hardcode the exact count at any point in time
(31 at STORY-207 landing) -- later stories add modules under `core/`.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CORE_ROOT = _REPO_ROOT / "backend" / "src" / "core"

# Detection seed for the guard (AC6) -- explicitly NON-EXHAUSTIVE. This is a
# RECALL AID, not the rule's definition: the definition is the FORM
# distinction in `docs/scrum/wiki/zone-rules.md` ZR-2 (three closed compliant
# prose forms, everything else forbidden except the `Provenance` carve-out),
# which is closed and decidable independent of any word list. A future vendor
# integration adds its own tokens here; that does not change the rule. Case-
# insensitive substring match; declared exactly once (ZR-3 -- `tools/` must
# never re-declare this).
_VENDOR_SEED_WORDS: tuple[str, ...] = (
    "dynatrace",
    "grail",
    "dql",
    "statuspage",
    "dynamodb",
)
_VENDOR_SEED_CLASS_FAMILIES: tuple[re.Pattern[str], ...] = (
    re.compile(r"dynamo\w*repository", re.IGNORECASE),
    re.compile(r"statuspage\w*", re.IGNORECASE),
)


def _matches_seed(text: str) -> bool:
    """True if `text` contains a detection-seed token (AC6), case-insensitive."""
    lowered = text.lower()
    if any(word in lowered for word in _VENDOR_SEED_WORDS):
        return True
    return any(pattern.search(text) for pattern in _VENDOR_SEED_CLASS_FAMILIES)


@dataclass(frozen=True)
class _Hit:
    """One vendor-vocabulary hit: which file, which line, which AST node kind,
    and the exact token that matched the seed."""

    file: str
    line: int
    node: str
    token: str

    def __str__(self) -> str:  # pragma: no cover - assertion message formatting only
        return f"{self.file}:{self.line} [{self.node}] {self.token!r}"


def _discover_core_modules() -> list[Path]:
    """Every `.py` file under `backend/src/core/` (`domain`, `ports`, `services`,
    `queries`, and the package root `core/__init__.py`) -- AC1's scan root."""
    return sorted(_CORE_ROOT.rglob("*.py"))


def _find_vendor_vocabulary(
    tree: ast.AST, filename: str, *, exclude_prose_constants: bool = True
) -> list[_Hit]:
    """The six-rule walk (ZR-2 Coverage verdict, AC1).

    `exclude_prose_constants` implements rule (6)'s exclusion -- a `Constant`
    string/number value that IS the sole value of an `Expr` statement (a
    formal docstring or the attribute-docstring idiom) is never a hit. It
    defaults True (the actual guard's behaviour); `False` exists only so
    `test_compliant_prose_forms_are_not_flagged` (AC2) can show what the walk
    WOULD flag without the exclusion, proving it is doing real work rather
    than vacuously matching nothing to begin with.
    """
    prose_constant_ids: set[int] = set()
    if exclude_prose_constants:
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                prose_constant_ids.add(id(node.value))

    hits: list[_Hit] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if _matches_seed(node.name):
                hits.append(_Hit(filename, node.lineno, type(node).__name__, node.name))
        elif isinstance(node, ast.arg):
            if _matches_seed(node.arg):
                hits.append(_Hit(filename, node.lineno, "arg", node.arg))
        elif isinstance(node, ast.Name):
            if _matches_seed(node.id):
                hits.append(_Hit(filename, node.lineno, "Name", node.id))
        elif isinstance(node, ast.Attribute):
            if _matches_seed(node.attr):
                hits.append(_Hit(filename, node.lineno, "Attribute", node.attr))
        elif isinstance(node, ast.keyword):
            if node.arg is not None and _matches_seed(node.arg):
                hits.append(_Hit(filename, node.lineno, "keyword", node.arg))
        elif isinstance(node, ast.Constant):
            if id(node) in prose_constant_ids:
                continue
            value = node.value
            if isinstance(value, bool):
                continue  # bool is an int subclass; not a vendor-vocabulary carrier
            if isinstance(value, (str, int, float)) and _matches_seed(str(value)):
                hits.append(_Hit(filename, node.lineno, "Constant", str(value)))
    return hits


def test_discovers_at_least_25_core_modules() -> None:
    """AC9 -- non-vacuity floor. A wrong root or a moved package must go RED,
    never silently iterate over nothing and pass. Do not hardcode 31 -- later
    stories (STORY-206 AC6, STORY-220) each add a module under `core/`."""
    modules = _discover_core_modules()
    assert len(modules) >= 25, (
        f"expected at least 25 modules under {_CORE_ROOT}, found "
        f"{len(modules)}: {[str(m) for m in modules]} -- check "
        "_CORE_ROOT / _discover_core_modules before trusting this guard at all"
    )


def test_core_has_no_vendor_vocabulary_leak() -> None:
    """AC1 -- the six-rule walk finds zero vendor-vocabulary hits inside
    `core/` at HEAD. Clean on arrival (STORY-207 planning's prototype scanned
    31 modules, 0 hits); AC5's mutation is the only way to see this RED."""
    modules = _discover_core_modules()
    assert modules, (
        "module discovery returned nothing -- see test_discovers_at_least_25_core_modules"
    )

    all_hits: list[_Hit] = []
    for path in modules:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        rel = path.relative_to(_REPO_ROOT).as_posix()
        all_hits.extend(_find_vendor_vocabulary(tree, rel))

    assert not all_hits, (
        "ZR-2 violation(s) -- vendor vocabulary appears inside core/ outside "
        "its three compliant prose forms (# comment, formal docstring, "
        "attribute-docstring idiom) or the Provenance carve-out:\n"
        + "\n".join(str(h) for h in all_hits)
    )


def test_compliant_prose_forms_are_not_flagged() -> None:
    """AC2 -- both prose forms stay compliant, proven in the compliant
    direction too. This is a real failure mode, not ceremony: an
    over-triggering guard would flag the six citations ZR-2 already
    adjudicates COMPLIANT and would have to be reverted rather than obeyed.

    Discrimination proof, against the real cited files (not a synthetic
    fixture): with the rule (6) exclusion turned OFF, the walk DOES flag
    `signal.py`'s module docstring ("... heard of Dynatrace ...") and
    `publication.py:66`'s attribute-docstring idiom ("... Statuspage publish
    ..."). With the exclusion ON (the guard's real, default behaviour), both
    go silent. The two sides differ, which is what proves the exclusion is
    doing real work rather than the walk vacuously matching nothing to begin
    with.
    """
    signal_path = _CORE_ROOT / "domain" / "signal.py"
    publication_path = _CORE_ROOT / "domain" / "publication.py"

    signal_tree = ast.parse(
        signal_path.read_text(encoding="utf-8"), filename=str(signal_path)
    )
    publication_tree = ast.parse(
        publication_path.read_text(encoding="utf-8"), filename=str(publication_path)
    )

    naive_signal_hits = _find_vendor_vocabulary(
        signal_tree, "signal.py", exclude_prose_constants=False
    )
    naive_publication_hits = _find_vendor_vocabulary(
        publication_tree, "publication.py", exclude_prose_constants=False
    )

    assert any("dynatrace" in h.token.lower() for h in naive_signal_hits), (
        "expected the naive (non-excluding) walk to flag signal.py's module "
        f"docstring mentioning Dynatrace; got {naive_signal_hits!r} -- the "
        "discrimination fixture itself is broken"
    )
    assert any(
        h.line == 66 and "statuspage" in h.token.lower() for h in naive_publication_hits
    ), (
        "expected the naive (non-excluding) walk to flag publication.py:66's "
        f"attribute docstring mentioning Statuspage; got "
        f"{naive_publication_hits!r} -- the discrimination fixture itself is broken"
    )

    real_signal_hits = _find_vendor_vocabulary(signal_tree, "signal.py")
    real_publication_hits = _find_vendor_vocabulary(publication_tree, "publication.py")

    assert not real_signal_hits, (
        f"the real (exclusion-on) walk must not flag signal.py's prose: {real_signal_hits!r}"
    )
    assert not real_publication_hits, (
        "the real (exclusion-on) walk must not flag publication.py's attribute-docstring "
        f"idiom: {real_publication_hits!r}"
    )
