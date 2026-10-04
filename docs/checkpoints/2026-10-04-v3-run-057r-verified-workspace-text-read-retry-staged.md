# V3-RUN-057R — verified workspace text-read retry staged

Date: 2026-10-04

## Prior attempt

V3-RUN-057 failed during the normal V3 pytest phase before the physical gate ran.

Authoritative Remote session:
`967b0b915931`

Remote source SHA:
`af36b516c010e2486b4b5d4020e0081b9a498edb`

Regression result:
- 256 passed
- 5 failed

All five failures came from:
`tests/test_operator_workspace_content.py`

Failure:
`ModuleNotFoundError: No module named 'openjarvis'`

## Root cause

The new unit tests accidentally invoked the production workspace-search runner
inside the normal ORION-V3 pytest environment.

The production runner lazily imports the pinned OpenJarvis donor.

That is correct for physical execution, but core/unit tests intentionally run
without requiring the donor package.

This was a test-harness error, not an authority or content-read failure.

The physical RUN-057 gate never started.

## Correction

The content-read unit tests now inject a deterministic workspace-search runner.

That runner produces the same ORION EvidenceEnvelope contract needed by the
content-read tests, including:
- logical project IDs;
- safe relative paths;
- file kind;
- size_bytes;
- modified_ns.

This isolates the unit tests to the authority logic they are meant to falsify.

## Physical gate unchanged in substance

RUN-057R still performs the prerequisite workspace search through the real
pinned OpenJarvis environment.

The production design remains:
- model path arguments = 0;
- exact verified path identity only;
- current registry must match search provenance;
- size + modified_ns must still match;
- symlink/path escape rejected;
- bounded UTF-8 read;
- content SHA256;
- explicit truncation;
- trusted root leak = 0;
- forged evidence ID blocked before read ACTION;
- changed file blocked before read ACTION;
- registry-stale evidence blocked before read ACTION.

## PASS meaning

PASS proves both:
1. the V3 unit layer no longer accidentally depends on donor installation;
2. the real pinned OpenJarvis search -> evidence-bound ORION content-read path
   works physically.
