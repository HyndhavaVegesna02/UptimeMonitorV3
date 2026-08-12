#!/usr/bin/env python3
"""YourTeam backlog board generator (yourteam_version: 2.4.0).

Renders `.scrum/backlog.yaml` as a grouped progress board so "what is done, what is
left, how much is left" is answerable at a glance instead of by scrolling a
thousand-line YAML file.

WHY THIS EXISTS (2026-08-12, PO-raised). The backlog had every field needed to answer
those questions -- status, points, sprint, type on every entry -- and no view. Three
quarters of the file was finished work interleaved with the live work, and the grouping
that did exist lived in 25 comment banners that no tool could read. This script reads
the `epic` field those banners were promoted into and collapses finished epics, so the
open work is the part you see.

THE BOARD IS A SPRINT-CLOSE SNAPSHOT, DELIBERATELY (PO decision). It is regenerated
once, when a sprint closes -- not on every backlog edit. So it is EXPECTED to disagree
with `backlog.yaml` mid-sprint, and `--check` must not fire then. What `--check`
enforces instead: the board's recorded `sprint` must not be older than the last CLOSED
sprint. That fires exactly once, at close, which is when regenerating is the job.

  generate            write the board to docs/scrum/BOARD.md
  --stdout            print instead of writing (no file touched)
  --check             exit 1 only if a sprint has closed since the board was generated

HONESTY RULE, load-bearing: a story with no `points` is counted as UNESTIMATED and
never as zero. 38 of 47 open stories had no estimate when this was written, so a naive
sum reported "15 points remaining" against 47 stories. The board states the gap instead
of implying a total it cannot compute.

Exit codes: 0 ok; 1 --check found a closed sprint newer than the board; 4 setup error.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - reported, never silently degraded
    print("yt_board: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(4) from None

BOARD_REL = "docs/scrum/BOARD.md"

#: Where the project's own design tokens and faces live, if it has them. The HTML board
#: inherits the project's design system rather than inventing one; absent these, it falls
#: back to a system font stack and says so instead of silently rendering in Times.
FONT_DIRS = (
    (
        "Geist",
        "frontend/node_modules/@fontsource/geist/files/geist-latin-{w}-normal.woff2",
    ),
    (
        "Geist Mono",
        "frontend/node_modules/@fontsource/geist-mono/files/geist-mono-latin-{w}-normal.woff2",
    ),
)

#: Statuses that mean the story will never be worked again. `split` and `superseded`
#: are terminal too -- the work moved elsewhere and is counted under its new id, so
#: counting them as open would double-count it.
CLOSED_STATUSES = {"done", "superseded", "archived", "split"}
BAR_WIDTH = 10


def find_root(start: Path) -> Path | None:
    for p in [start, *start.parents]:
        if (p / ".scrum").is_dir():
            return p
    return None


def git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return out.stdout.strip() if out.returncode == 0 else ""


def points(story: dict) -> int | None:
    """None means UNESTIMATED. Never coerce to 0 -- that is the reported-total lie."""
    raw = story.get("points")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def is_closed(story: dict) -> bool:
    return str(story.get("status", "")).strip() in CLOSED_STATUSES


def bar(done: int, total: int) -> str:
    filled = round(BAR_WIDTH * done / total) if total else 0
    return "#" * filled + "." * (BAR_WIDTH - filled)


def load(root: Path) -> tuple[dict, list[dict]]:
    data = yaml.safe_load(
        (root / ".scrum" / "backlog.yaml").read_text(encoding="utf-8")
    )
    epics = data.get("epics") or {}
    stories = data.get("stories") or []
    return epics, stories


def sprint_of_record(root: Path) -> str:
    """The sprint the board is being generated FOR, read from board state."""
    path = root / ".scrum" / "sprint-current.yaml"
    if not path.is_file():
        return "unknown"
    data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    for key in ("sprint", "number", "id", "name"):
        if key in data and data[key] not in (None, ""):
            return str(data[key])
    return "unknown"


def render(root: Path) -> str:
    epics, stories = load(root)
    order = list(epics)
    seen = list(dict.fromkeys(s.get("epic", "ungrouped") for s in stories))
    order += [e for e in seen if e not in order]

    closed = [s for s in stories if is_closed(s)]
    open_ = [s for s in stories if not is_closed(s)]
    est_open = [s for s in open_ if points(s) is not None]
    unest_open = [s for s in open_ if points(s) is None]

    sprint = sprint_of_record(root)
    head = git(root, "rev-parse", "--short", "HEAD") or "unknown"
    today = dt.date.today().isoformat()

    L: list[str] = []
    L.append("# Backlog board")
    L.append("")
    L.append(
        f"**Snapshot at sprint-{sprint}, commit `{head}`, generated {today}.** Regenerated "
        "ONCE per sprint at close, so it is expected to lag `.scrum/backlog.yaml` "
        "mid-sprint — `backlog.yaml` is always the source of truth. Rebuild with "
        "`python .claude/skills/yourteam/scripts/yt_board.py`."
    )
    L.append("")
    L.append(
        f"**{len(closed)}/{len(stories)} stories closed.** "
        f"{len(open_)} open: {len(est_open)} estimated "
        f"({sum(points(s) or 0 for s in est_open)} pts) + **{len(unest_open)} unestimated**."
    )
    if unest_open:
        L.append("")
        L.append(
            f"> ⚠ Total work remaining is NOT computable: {len(unest_open)} of {len(open_)} "
            "open stories carry no estimate, so any points figure below covers only the "
            "estimated ones. Refinement closes this gap; no arrangement of the file can."
        )
    L.append("")

    # ---- open epics -------------------------------------------------------
    L.append("## Open work")
    L.append("")
    L.append("| Epic | Progress | Stories | Est. pts | Unestimated |")
    L.append("| --- | --- | --- | --- | --- |")
    any_open = False
    for slug in order:
        grp = [s for s in stories if s.get("epic") == slug]
        if not grp:
            continue
        o = [s for s in grp if not is_closed(s)]
        if not o:
            continue
        any_open = True
        d = [s for s in grp if is_closed(s)]
        ep = [s for s in grp if points(s) is not None]
        title = str(epics.get(slug, slug)).replace("|", "\\|")
        L.append(
            f"| **{title}** <br>`{slug}` | `{bar(len(d), len(grp))}` | {len(d)}/{len(grp)} "
            f"| {sum(points(s) or 0 for s in d if points(s) is not None)}/"
            f"{sum(points(s) or 0 for s in ep)} | "
            f"{sum(1 for s in o if points(s) is None) or '—'} |"
        )
    if not any_open:
        L.append("| _no open work_ | | | | |")
    L.append("")

    # ---- the open stories themselves --------------------------------------
    L.append("### Open stories by epic")
    L.append("")
    for slug in order:
        o = [s for s in stories if s.get("epic") == slug and not is_closed(s)]
        if not o:
            continue
        L.append(f"**{epics.get(slug, slug)}**")
        L.append("")
        for s in sorted(o, key=lambda x: str(x.get("id"))):
            pt = points(s)
            pts_txt = f"{pt} pts" if pt is not None else "**unestimated**"
            fileref = s.get("file")
            name = (
                f"[{s.get('id')}]({Path(str(fileref)).as_posix()})"
                if fileref and fileref != "None"
                else f"{s.get('id')} _(no story file yet)_"
            )
            L.append(
                f"- `{s.get('status')}` {name} — {s.get('title')} "
                f"· {s.get('type')} · {pts_txt}"
            )
        L.append("")

    # ---- finished epics, collapsed ----------------------------------------
    done_epics = [
        slug
        for slug in order
        if [s for s in stories if s.get("epic") == slug]
        and not [s for s in stories if s.get("epic") == slug and not is_closed(s)]
    ]
    L.append("## Complete")
    L.append("")
    L.append(
        f"{len(done_epics)} epics with no open stories. Listed, not detailed — this is "
        "the three quarters of the backlog that no longer needs reading."
    )
    L.append("")
    for slug in done_epics:
        grp = [s for s in stories if s.get("epic") == slug]
        ep = [s for s in grp if points(s) is not None]
        L.append(
            f"- **{epics.get(slug, slug)}** — {len(grp)} stories, "
            f"{sum(points(s) or 0 for s in ep)} pts"
        )
    L.append("")
    return "\n".join(L) + "\n"


def _fonts(root: Path) -> tuple[str, bool]:
    """@font-face blocks with the faces inlined as data URIs. CSP blocks font CDNs."""
    css, found = [], False
    for family, tmpl in FONT_DIRS:
        for weight in (400, 500, 600):
            f = root / tmpl.format(w=weight)
            if not f.is_file():
                continue
            found = True
            b64 = base64.b64encode(f.read_bytes()).decode("ascii")
            css.append(
                f"@font-face{{font-family:'{family}';font-style:normal;"
                f"font-weight:{weight};font-display:swap;"
                f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
            )
    return "\n".join(css), found


def esc(s: object) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


#: Status -> the health token that carries it. Semantic colour, separate from the accent.
STATUS_TOKEN = {
    "ready": "maintenance",
    "draft": "unknown",
    "blocked": "down",
    "in_progress": "degraded",
}


def render_html(root: Path) -> str:
    epics, stories = load(root)
    order = list(epics) + [
        e
        for e in dict.fromkeys(s.get("epic", "ungrouped") for s in stories)
        if e not in epics
    ]
    closed = [s for s in stories if is_closed(s)]
    open_ = [s for s in stories if not is_closed(s)]
    est = [s for s in open_ if points(s) is not None]
    unest = [s for s in open_ if points(s) is None]
    sprint, head = sprint_of_record(root), git(root, "rev-parse", "--short", "HEAD")
    font_css, have_fonts = _fonts(root)
    sans = (
        "'Geist',system-ui,-apple-system,'Segoe UI',sans-serif"
        if have_fonts
        else "system-ui,-apple-system,'Segoe UI',sans-serif"
    )
    mono = (
        "'Geist Mono',ui-monospace,'Cascadia Mono',monospace"
        if have_fonts
        else "ui-monospace,'Cascadia Mono',monospace"
    )

    open_epics, done_epics = [], []
    for slug in order:
        grp = [s for s in stories if s.get("epic") == slug]
        if not grp:
            continue
        (open_epics if any(not is_closed(s) for s in grp) else done_epics).append(
            (slug, grp)
        )

    def tile(value: str, label: str, note: str = "", token: str = "") -> str:
        style = f' style="color:var(--h-{token})"' if token else ""
        return (
            f'<div class="tile"><div class="tile-v"{style}>{esc(value)}</div>'
            f'<div class="tile-l">{esc(label)}</div>'
            + (f'<div class="tile-n">{esc(note)}</div>' if note else "")
            + "</div>"
        )

    pct = round(100 * len(closed) / len(stories)) if stories else 0
    tiles = "".join(
        [
            tile(
                f"{pct}%", "of stories closed", f"{len(closed)} of {len(stories)}", "up"
            ),
            tile(str(len(open_)), "stories open", f"across {len(open_epics)} epics"),
            tile(
                str(sum(points(s) or 0 for s in est)),
                "points, estimated",
                f"covers {len(est)} of {len(open_)} open",
            ),
            tile(
                str(len(unest)),
                "unestimated",
                "not countable as remaining work",
                "degraded" if unest else "up",
            ),
        ]
    )

    rows = []
    for slug, grp in open_epics:
        d = [s for s in grp if is_closed(s)]
        o = [s for s in grp if not is_closed(s)]
        gap = sum(1 for s in o if points(s) is None)
        frac = len(d) / len(grp)
        rows.append(
            f'<tr><th scope="row"><span class="ep">{esc(epics.get(slug, slug))}</span>'
            f"<code>{esc(slug)}</code></th>"
            f'<td class="barcell"><span class="bar"><i style="width:{frac * 100:.4g}%"></i>'
            f"</span></td>"
            f'<td class="num">{len(d)}/{len(grp)}</td>'
            f'<td class="num">{sum(points(s) or 0 for s in d if points(s) is not None)}'
            f"/{sum(points(s) or 0 for s in grp if points(s) is not None)}</td>"
            f'<td class="num">'
            + (
                f'<span class="pill warn">{gap}</span>'
                if gap
                else '<span class="dash">—</span>'
            )
            + "</td></tr>"
        )

    groups = []
    for slug, grp in open_epics:
        o = sorted((s for s in grp if not is_closed(s)), key=lambda x: str(x.get("id")))
        items = []
        for s in o:
            pt = points(s)
            st = str(s.get("status", "?"))
            items.append(
                f'<li><span class="pill s-{esc(STATUS_TOKEN.get(st, "unknown"))}">'
                f"{esc(st)}</span>"
                f'<code class="sid">{esc(s.get("id"))}</code>'
                f'<span class="stitle">{esc(s.get("title"))}</span>'
                f'<span class="meta">{esc(s.get("type"))}</span>'
                + (
                    f'<span class="meta">{pt} pts</span>'
                    if pt is not None
                    else '<span class="meta warn-t">unestimated</span>'
                )
                + "</li>"
            )
        groups.append(
            f'<section class="grp"><h3>{esc(epics.get(slug, slug))}'
            f'<span class="cnt">{len(o)} open</span></h3>'
            f'<ul class="stories">{"".join(items)}</ul></section>'
        )

    done_list = "".join(
        f"<li><span>{esc(epics.get(slug, slug))}</span>"
        f'<span class="meta">{len(grp)} stories · '
        f"{sum(points(s) or 0 for s in grp if points(s) is not None)} pts</span></li>"
        for slug, grp in done_epics
    )

    warn = (
        f'<p class="callout"><strong>Work remaining is not computable yet.</strong> '
        f"{len(unest)} of {len(open_)} open stories carry no estimate, so the points figure "
        f"covers only the other {len(est)}. Refinement closes this gap — no arrangement of "
        f"the backlog can.</p>"
        if unest
        else ""
    )

    # Dark-first: the bare :root carries the complete dark palette (this is an operator
    # cockpit), and the light set is swapped in consistently for both the OS preference
    # and the explicit stamp. Every colour is a token; none is defined only inside a
    # media or [data-theme] block.
    return f"""<title>Backlog board — sprint-{esc(sprint)}</title>
<style>
{font_css}
:root{{
  --canvas:#0b0d10; --s1:#111419; --s2:#171b21; --hair:#22272e; --hair-2:#2d333b;
  --ink:#e6e9ee; --ink-m:#98a1ac; --ink-s:#69727d;
  --accent:#7c85f0; --accent-bg:rgba(124,133,240,.14);
  --h-up:#3fb950; --h-up-bg:rgba(63,185,80,.13);
  --h-degraded:#d6a419; --h-degraded-bg:rgba(214,164,25,.14);
  --h-down:#f85149; --h-down-bg:rgba(248,81,73,.14);
  --h-maintenance:#3b9eff; --h-maintenance-bg:rgba(59,158,255,.15);
  --h-unknown:#8b96a5; --h-unknown-bg:rgba(139,150,165,.13);
  --shadow:none;
}}
@media (prefers-color-scheme:light){{
  :root:not([data-theme="dark"]){{
    --canvas:#f6f7f9; --s1:#ffffff; --s2:#f0f2f5; --hair:#e4e7eb; --hair-2:#d3d8de;
    --ink:#161a1e; --ink-m:#59626c; --ink-s:#8a929b;
    --accent:#5b60d6; --accent-bg:rgba(91,96,214,.10);
    --h-up:#1a7f37; --h-up-bg:rgba(26,127,55,.11);
    --h-degraded:#9a6700; --h-degraded-bg:rgba(154,103,0,.11);
    --h-down:#cf222e; --h-down-bg:rgba(207,34,46,.10);
    --h-maintenance:#0b68cb; --h-maintenance-bg:rgba(11,104,203,.12);
    --h-unknown:#57606a; --h-unknown-bg:rgba(87,96,106,.11);
    --shadow:0 1px 3px rgba(18,24,38,.06),0 1px 2px rgba(18,24,38,.04);
  }}
}}
:root[data-theme="light"]{{
  --canvas:#f6f7f9; --s1:#ffffff; --s2:#f0f2f5; --hair:#e4e7eb; --hair-2:#d3d8de;
  --ink:#161a1e; --ink-m:#59626c; --ink-s:#8a929b;
  --accent:#5b60d6; --accent-bg:rgba(91,96,214,.10);
  --h-up:#1a7f37; --h-up-bg:rgba(26,127,55,.11);
  --h-degraded:#9a6700; --h-degraded-bg:rgba(154,103,0,.11);
  --h-down:#cf222e; --h-down-bg:rgba(207,34,46,.10);
  --h-maintenance:#0b68cb; --h-maintenance-bg:rgba(11,104,203,.12);
  --h-unknown:#57606a; --h-unknown-bg:rgba(87,96,106,.11);
  --shadow:0 1px 3px rgba(18,24,38,.06),0 1px 2px rgba(18,24,38,.04);
}}
*,*::before,*::after{{box-sizing:border-box}}
body{{margin:0;background:var(--canvas);color:var(--ink);font-family:{sans};
  font-variant-numeric:tabular-nums;line-height:1.5;
  -webkit-font-smoothing:antialiased}}
.wrap{{max-width:1080px;margin:0 auto;padding:clamp(24px,5vw,56px) clamp(16px,4vw,32px);
  display:flex;flex-direction:column;gap:40px}}
header{{display:flex;flex-direction:column;gap:10px}}
.eyebrow{{font-family:{mono};font-size:11px;letter-spacing:.13em;text-transform:uppercase;
  color:var(--ink-s);display:flex;gap:14px;flex-wrap:wrap}}
h1{{margin:0;font-size:clamp(28px,4.2vw,40px);font-weight:600;letter-spacing:-.022em;
  text-wrap:balance}}
.sub{{margin:0;color:var(--ink-m);max-width:66ch}}
.tiles{{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}}
.tile{{background:var(--s1);border:1px solid var(--hair);border-radius:10px;
  padding:18px 20px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:3px}}
.tile-v{{font-size:34px;font-weight:600;letter-spacing:-.02em;line-height:1.1}}
.tile-l{{font-size:13px;color:var(--ink-m)}}
.tile-n{{font-family:{mono};font-size:11px;color:var(--ink-s)}}
.callout{{margin:0;background:var(--h-degraded-bg);border:1px solid var(--h-degraded);
  border-left-width:3px;border-radius:8px;padding:14px 18px;color:var(--ink);
  font-size:14px;max-width:78ch}}
h2{{margin:0 0 14px;font-size:13px;font-weight:600;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ink-s);font-family:{mono}}}
.scroll{{overflow-x:auto;border:1px solid var(--hair);border-radius:10px;
  background:var(--s1);box-shadow:var(--shadow)}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{text-align:left;padding:12px 16px;border-bottom:1px solid var(--hair)}}
tbody tr:last-child th,tbody tr:last-child td{{border-bottom:0}}
thead th{{font-family:{mono};font-size:11px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--ink-s);font-weight:500;background:var(--s2)}}
th[scope=row]{{font-weight:500;display:flex;flex-direction:column;gap:2px;min-width:250px}}
.ep{{text-wrap:balance}}
code{{font-family:{mono};font-size:11px;color:var(--ink-s)}}
.num{{text-align:right;font-family:{mono};font-size:13px;color:var(--ink-m);
  white-space:nowrap}}
.barcell{{width:170px;min-width:120px}}
.bar{{display:block;height:6px;background:var(--s2);border-radius:99px;overflow:hidden;
  box-shadow:inset 0 0 0 1px var(--hair)}}
.bar i{{display:block;height:100%;background:var(--h-up);border-radius:99px}}
.pill{{display:inline-block;font-family:{mono};font-size:10.5px;letter-spacing:.05em;
  text-transform:uppercase;padding:2px 7px;border-radius:99px;white-space:nowrap}}
.warn{{background:var(--h-degraded-bg);color:var(--h-degraded)}}
.warn-t{{color:var(--h-degraded)}}
.s-unknown{{background:var(--h-unknown-bg);color:var(--h-unknown)}}
.s-maintenance{{background:var(--h-maintenance-bg);color:var(--h-maintenance)}}
.s-down{{background:var(--h-down-bg);color:var(--h-down)}}
.s-degraded{{background:var(--h-degraded-bg);color:var(--h-degraded)}}
.dash{{color:var(--ink-s)}}
.groups{{display:flex;flex-direction:column;gap:26px}}
.grp h3{{margin:0 0 10px;font-size:15px;font-weight:600;display:flex;gap:12px;
  align-items:baseline;flex-wrap:wrap;text-wrap:balance}}
.cnt{{font-family:{mono};font-size:11px;color:var(--ink-s);font-weight:400}}
.stories{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:1px;
  border:1px solid var(--hair);border-radius:10px;overflow:hidden}}
.stories li{{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;
  padding:11px 16px;background:var(--s1);font-size:14px}}
.sid{{font-size:12px;color:var(--accent)}}
.stitle{{flex:1 1 320px;min-width:0}}
.meta{{font-family:{mono};font-size:11px;color:var(--ink-s);white-space:nowrap}}
.done ul{{list-style:none;margin:0;padding:0;display:grid;gap:1px;
  grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
  border:1px solid var(--hair);border-radius:10px;overflow:hidden}}
.done li{{display:flex;justify-content:space-between;gap:16px;align-items:baseline;
  padding:10px 16px;background:var(--s1);font-size:13.5px;color:var(--ink-m)}}
footer{{color:var(--ink-s);font-size:12.5px;font-family:{mono};
  border-top:1px solid var(--hair);padding-top:18px;max-width:80ch;line-height:1.7}}
</style>
<div class="wrap">
<header>
  <p class="eyebrow"><span>Uptime Monitor V3</span><span>sprint-{esc(sprint)}</span>
    <span>{esc(head or "unknown")}</span><span>{dt.date.today().isoformat()}</span></p>
  <h1>Backlog board</h1>
  <p class="sub">A snapshot taken at sprint close. <code>.scrum/backlog.yaml</code> is the
    source of truth; this page is the view of it, regenerated once per sprint.</p>
</header>

<section class="tiles">{tiles}</section>

{warn}

<section>
  <h2>Open epics</h2>
  <div class="scroll"><table>
    <thead><tr><th scope="col">Epic</th><th scope="col">Progress</th>
      <th scope="col">Stories</th><th scope="col">Points</th>
      <th scope="col">Unest.</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table></div>
</section>

<section>
  <h2>Open stories</h2>
  <div class="groups">{"".join(groups)}</div>
</section>

<section class="done">
  <h2>Complete — {len(done_epics)} epics, no open stories</h2>
  <ul>{done_list}</ul>
</section>

<footer>Generated by <code>yt_board.py</code> from <code>.scrum/backlog.yaml</code> at
sprint-{esc(sprint)}, commit {esc(head or "unknown")}. Points totals cover estimated
stories only — an unestimated story is never counted as zero.
{"" if have_fonts else "Geist was unavailable at generation time; this page uses a system font stack."}
</footer>
</div>
"""


BOARD_SPRINT_RE = re.compile(r"Snapshot at sprint-([^,]+),")


def check(root: Path) -> int:
    """Fail only if a sprint CLOSED since the board was generated.

    Not "the board differs from backlog.yaml" -- mid-sprint that is the intended state
    and a check that fired then would be noise the reader learns to ignore.
    """
    board = root / BOARD_REL
    if not board.is_file():
        print(f"yt_board: {BOARD_REL} does not exist — generate it", file=sys.stderr)
        return 1
    m = BOARD_SPRINT_RE.search(board.read_text(encoding="utf-8", errors="replace"))
    if not m:
        print(
            "yt_board: board carries no `Snapshot at sprint-N` line, so its age cannot "
            "be established — regenerate it",
            file=sys.stderr,
        )
        return 1
    on_board, current = m.group(1).strip(), sprint_of_record(root)
    if on_board != current:
        print(
            f"yt_board: board is a sprint-{on_board} snapshot but board state says "
            f"sprint-{current} — regenerate at sprint close",
            file=sys.stderr,
        )
        return 1
    print(f"yt_board: board is current for sprint-{current}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stdout", action="store_true", help="print instead of writing")
    ap.add_argument(
        "--html",
        metavar="PATH",
        default=None,
        help="also render the artifact HTML board to PATH (design tokens + faces are "
        "inherited from the project's own frontend, never invented here)",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if a sprint closed since the board was generated",
    )
    args = ap.parse_args()

    root = find_root(Path.cwd().resolve())
    if root is None:
        print(
            "yt_board: no .scrum/ directory found walking up from cwd", file=sys.stderr
        )
        return 4
    if not (root / ".scrum" / "backlog.yaml").is_file():
        print("yt_board: .scrum/backlog.yaml not found", file=sys.stderr)
        return 4

    if args.check:
        return check(root)

    text = render(root)
    if args.stdout:
        # Windows stdout defaults to the locale codec (cp1252), which cannot encode the
        # board's em-dashes or the unestimated-work warning glyph — it raises rather than
        # degrading, so --stdout died with UnicodeEncodeError while writing the FILE
        # worked (that path passes encoding="utf-8" explicitly). Caught by the CLI test,
        # not by any run of mine, because my terminal had PYTHONIOENCODING set.
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (
            AttributeError,
            ValueError,
        ):  # pragma: no cover - non-reconfigurable stream
            pass
        sys.stdout.write(text)
        return 0
    out = root / BOARD_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"yt_board: wrote {BOARD_REL} ({len(text.splitlines())} lines)")
    if args.html:
        html = render_html(root)
        dest = Path(args.html)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        print(f"yt_board: wrote {dest} ({len(html) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
