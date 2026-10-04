# V3-RUN-058 — verified workspace text-read byte-exact retry staged

Date: 2026-10-04

## Prior attempt

V3-RUN-057R failed in the normal regression phase before the physical gate ran.

Authoritative Remote session:
`f5527618ee76`

Remote source SHA:
`36b49b115e7eb59b495d903499c04982e5567735`

Regression result:
- 260 passed
- 1 failed

Failure:
the Windows test fixture used `Path.write_text(... "\n")`.

Windows newline translation stored CRLF bytes:
`\r\n`

The evidence-bound reader intentionally reads exact bytes, so it correctly
returned CRLF. The test incorrectly expected LF.

## Interpretation

This was not a production authority failure.

It reinforces the earlier exact-payload lesson:
exact content must be represented as bytes, not inferred through platform text
newline conversion.

## Correction

Unit and physical fixtures now use:
`write_bytes(...)`

for the exact text payloads whose SHA256/content equality is asserted.

Production text-read authority code is unchanged.

## Physical proof still required

V3-RUN-058 still proves:
- model path arguments = 0;
- verified evidence identity is the only model-facing locator;
- real pinned OpenJarvis prerequisite workspace search;
- exact project/revision/path binding;
- file size + modified_ns unchanged check;
- bounded UTF-8 read;
- content SHA256 over exactly returned bytes;
- explicit truncation;
- trusted root leak = 0;
- forged evidence identity blocked before ACTION;
- file changed after search blocked before ACTION;
- registry-stale evidence blocked before ACTION;
- exact causal chain from workspace RESULT through text-read RESULT.

## PASS meaning

PASS proves the evidence-bound text-read primitive physically, with deterministic
cross-platform byte fixtures.
