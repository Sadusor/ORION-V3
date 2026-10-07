# AUTOMATIC MEMORY CANDIDATES V1 — PASS / FROZEN

Date: 2026-10-07

## Status

PASS / FROZEN

This module is frozen after physical end-to-end proof. Do not modify it unless a later feature explicitly requires it.

## What was added

Automatic memory selection now works without the owner having to say "remember this".

The selector is deliberately conservative and deterministic:

- stable owner preferences can become candidates;
- stable owner facts can become candidates;
- stable owner naming facts can become candidates;
- owner decisions can become candidates;
- questions are ignored;
- sync/test messages are ignored;
- task requests are ignored;
- obvious secrets and sensitive categories are filtered;
- existing history is not backfilled at startup;
- automatic intake never writes canonical memory directly;
- canonical promotion still requires owner review.

## Physical proof

### Positive automatic-selection test

Owner sent:

`I prefer dark mode for ORION.`

The owner did NOT say "remember".

Result:

- message appeared automatically in Settings -> Review memory candidates;
- automatic candidate creation: PASS.

### Negative-selection test

Owner sent:

`What is 2 + 2?`

Result:

- question did not appear as a memory candidate;
- non-memory filtering: PASS.

### Owner promotion test

Owner promoted:

`I prefer dark mode for ORION.`

Result:

- PROMOTE recorded successfully;
- owner review boundary: PASS.

### Cross-chat canonical recall test

Owner started a new chat and asked:

`What mode do I prefer for ORION?`

Result:

- ORION correctly recalled dark mode;
- promoted canonical memory recall across chats: PASS.

## Bundled mobile fixes physically proven

The same Android release also included:

- Android-side duplicate ORION assistant reply suppression matching the PC chat-store rule;
- New Chat screen now uses the actual ORION app icon;
- Settings buttons give immediate press/busy feedback such as Checking..., Pairing..., Starting update..., Opening installer....

Physical results:

- duplicate-answer regression test using `What is 3 + 3?`: PASS, one answer only;
- New Chat ORION image: PASS;
- Settings Refresh connection press feedback: PASS.

## Safety / authority invariants

Automatic selection is candidate intake only.

It does NOT:

- grant execution authority;
- bypass ORION policy;
- auto-promote canonical memory;
- rewrite chat history;
- treat model output as owner truth;
- remove provenance or review.

Canonical Memory remains context only, not authority.

## Relevant commits

- `e79a169fc148675dd717fbb1509165a4701a0309` — add conservative automatic candidate selector
- `e5e656ffaebf754dd6484be2dcc03a2eb7d9ae34` — allow trusted selector provenance reason
- `3f610fd3269c6d998f3b2814527eb9b2235900f7` — run selector after chat sync
- `f4949e43847f1c1690f73db838f8acba48c73e01` — mobile icon + button feedback
- `ee8cdcb7adb2cd6ac1a2f13105ef48b3c4aff4c5` — automatic-memory regression
- `c8cdb1290eb0756d4c36b11cc6fd9aa14d30e6c0` — add automatic-memory regression to update gate
- `552909058fc6bfc89ea84b97d50b107ba08929af` — Android duplicate ORION reply suppression

## Freeze point

Code freeze point for this module and bundled phone fixes:

`552909058fc6bfc89ea84b97d50b107ba08929af`
