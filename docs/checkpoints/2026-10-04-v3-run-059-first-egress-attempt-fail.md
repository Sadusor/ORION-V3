# V3-RUN-059 — first cloud-egress execution attempt FAIL (canonical newline mismatch)

Date: 2026-10-04

## Authoritative Remote evidence

Remote session:
`27984c717df8`

Remote source SHA:
`8dd419859642358b9f52b292bd2564bf9593dbb2`

Published Remote result commit:
`4d86725cabdc7413ea6a5bae759df29d3297d66d`

## Remote / Evidence Pack layer

Before V3 execution, the new observer-only Evidence Pack integration physically passed:

- `REMOTE_INTEGRATION_COMPILE> PASS`
- `REMOTE_UI_SESSION_FOCUS_PROBE> PASS`
- `REMOTE_EVIDENCE_PACK_PROBE> PASS`
- observer-only: PASS
- desktop capture: 0
- structured steps: 11
- PNG cards: 12
- SVG fallback cards: 12
- ZIP: PASS
- Evidence Pack SHA256:
  `a1d2ecaa02295f07eef6e7c1c797b47473dd3df2b059f271a78c589e8ab61fc3`

This physically validates the Evidence Pack renderer/ZIP probe on the Windows PC.

## V3 gate result

V3 exact SHA checkout:
PASS

Authoring preflight:
PASS

Regression:
- 266 passed
- 1 failed

The physical RUN-059 script did not execute because pytest stopped the bootstrap.

## Single failure

Test:
`test_no_cloud_content_is_excluded_from_prompt_and_canonical_egress`

Expected:
`queued.request.task == packet.prompt`

Actual difference:
one trailing newline.

The cloud queue canonicalizes required text through its existing text-normalization semantics, removing outer whitespace.

The new cloud-egress packet had hashed/stored a prompt with a final newline.

Therefore the exact packet/request binding correctly failed.

## Correction

The egress packet now canonicalizes the complete rendered prompt with:

`.strip()`

before:
- bound checking;
- SHA256;
- canonical egress DECISION;
- cloud request queueing.

This does not alter file/code content inside the evidence block because required policy/review framing surrounds the evidence. It only normalizes outer packet whitespace to the queue's established semantics.

A regression assertion now requires:

`packet.prompt == packet.prompt.strip()`

## Retry

New run:
`V3-RUN-059R`

The authority/privacy design remains unchanged:
- local read != cloud egress authority;
- no_cloud content excluded;
- private sentinel never enters provider prompt;
- absolute roots never enter provider prompt;
- exact provider/model;
- no fallback/tools;
- REVIEW advisory_only;
- cloud ACTION/Hand authority = 0.
