"""Publisher-chain discrimination (STORY-182 reality gate side 2).

`build_publisher` (`composition/publish_helper.py:183-234`) returns the same
top-level type, `StatusWritebackPublisher`, on BOTH its safe (empty mapping)
and unsafe (non-empty mapping) branches -- asserting the top-level type
proves nothing (sprint-64 plan finding B2, itself a repeat of the
sprint-63 `implementer.md` A3 trap: the layers store `_delegate`, never
`delegate`). The only thing that actually discriminates is the FULL
`_delegate` chain of type names, which is what `describe_publisher_chain`
walks.
"""

from __future__ import annotations

from typing import Any


def describe_publisher_chain(publisher: Any) -> list[str]:
    """Return the chain of type names from `publisher` down through every
    `_delegate` it wraps, outermost first.

    A chain of length 1 (no `_delegate` attribute found at all) is never a
    legitimate "safe" or "unsafe" result on its own -- it means the wrong
    attribute was walked (the sprint-63 trap: the layers store `_delegate`,
    not `delegate`) and the caller must discard that result rather than
    report it.
    """
    chain = [type(publisher).__name__]
    current = publisher
    while hasattr(current, "_delegate"):
        current = current._delegate
        chain.append(type(current).__name__)
    return chain
