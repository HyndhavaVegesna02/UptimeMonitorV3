# Sprint 50 Retro

## Data
- Velocity 5/5 (STORY-093 accept; STORY-089 accept + follow-up STORY-094).
- Estimate accuracy: both stories landed within estimate; STORY-089's console loop
  (3 failed/retried stack operations) consumed the risk budget its 3 points priced in.
- Blockers: none formal. Two delete→clean→recreate stack cycles (~30 min each) on
  defects that were pre-checkable (see below). One PO org-policy interrupt
  (AWS account rules) absorbed mid-story without scope change.
- Rework loops: zero reviewer rejections (2-pt story = no reviewer tier; 089 is
  PO-verdict-only by design). Gate red at planning (yt_wiki.py format drift from the
  sprint-49 retro commit itself — fixed pre-lock, 74b66e9).
- Wiki: 0 stale at close; 1 new article (deployment-topology); Facts-lint caught one
  citation-outside-code_refs miss and one BOM-blinding incident (both orchestrator-caused,
  both fixed in-session).
- Reality-gate yield: 3 template defects reachable ONLY by live deploy (AutoPublish,
  fabricated CachePolicyId, DefaultRootObject) — the deferred-to-089 gate design worked,
  but two of the three were knowable earlier (see amendment 1).

## What went well
- Plan-verifier GAP 1 (runbook still said `sprint-49`) prevented deploying artifacts
  without the sprint's own hardening — the pre-lock adversarial check earned its dispatch.
- Evidence-chain verification beat re-testing: AC4 was closed from CloudWatch access logs
  + DynamoDB state instead of asking the PO to re-toggle (PO's suggestion).
- The org-policy interrupt (us-east-1 lock, 22:00 IST reaper) was encoded at the artifact
  rung (runbook Prerequisites + stack tags) within minutes and saved the stack from
  deletion that same night.

## What dragged
- Fabricated/mislabeled external IDs (CloudFront managed policies) cost two full stack
  create-fail-clean cycles. cfn-lint validates shape, not existence; quality review had
  APPROVEd the IDs — plausible-looking survived every static rung.
- UI verification (AC2 tabs, AC4 toggle) required PO hands — no browser tooling connected.
- Windows friction (PS 5.1): ECR login pipe mangling (fixed via cmd byte-pipe),
  utf8-BOM Set-Content blinding the wiki parser (fixed via UTF8Encoding(false)).

## Amendments (PO-approved 2026-07-17)
1. **Checklist rung** — quality-review.md + plan-verification.md: hardcoded
   external-service identifiers require live-derivation evidence (the producing CLI
   command + output); plan-verifier re-derives them pre-lock. Motivating incident:
   sprint-50 CachePolicyId 404.
2. **Tooling** — Playwright MCP added at project scope (`.mcp.json`); UI reality gates
   (render checks, mutation round-trips) become orchestrator-driven from the next
   session onward.

## Carry-forward notes (no amendment)
- CFN `DeletionPolicy: Retain` leftovers block stack re-creation by name; the
  delete→clean→recreate recipe is documented in [[deployment-topology]] History.
- STORY-090 (CI/CD) is unblocked per the PO's earlier "UI first, CI/CD later" directive;
  STORY-094 (/history limit param) awaits refinement.
