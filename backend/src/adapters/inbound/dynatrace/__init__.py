"""The Dynatrace inbound adapter (STORY-008, dossier §5/§7/§8).

Queries synthetic monitor results via DQL and normalizes each location
execution into a canonical `SignalObservation`
(`src.core.domain.signal.SignalObservation`). Vendor specifics — monitor
type, vendor ids, the raw DQL row shape — are fully contained in this
package; nothing here leaks into `src.core`. The adapter is deliberately
dumb and lossless: it produces exactly one observation per location
execution and never aggregates (collapse to one verdict per cycle is a
core step, dossier §10).
"""
