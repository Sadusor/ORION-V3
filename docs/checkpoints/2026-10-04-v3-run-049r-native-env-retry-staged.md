# V3-RUN-049R — production routine Hand retry staged

Date: 2026-10-04

## Prior attempt

V3-RUN-049 failed before the filesystem Hand executed.

Authoritative Remote session:
`aafbd5d4eea3`

Remote source SHA:
`59f79c0939f4486d34ac97e6ed1bea59fabb54a5`

Observed:
- authoring preflight: PASS;
- regression suite: 217 passed;
- pinned OpenJarvis SHA: PASS;
- qwen35-9b-orion:latest thinking ON / ctx 4096: available;
- governor chose `fs.search_exact`: PASS;
- canonical PROPOSAL creation: PASS;
- canonical proposal SHA256:
  `62b7da4bb9f5d9107479f1fd0b482e56f8aef4485e915bc445a2c529670c7208`.

Failure occurred at first OpenJarvis security-policy construction:

`ModuleNotFoundError: No module named 'openjarvis_rust'`

No Hand execution occurred.

## Root cause

The RUN-049 bootstrap verified/fetched the pinned donor but executed the V3 gate
inside the ORION-V3 Python environment.

The already-proven Gate-1 physical path requires:
1. `uv sync --project external/OpenJarvis --group desktop-native`;
2. native Rust extension import from the OpenJarvis environment;
3. execution of the V3 gate using `uv run --project external/OpenJarvis python ...`.

RUN-049 omitted steps 1 and 3.

This is a bootstrap/environment integration error, not an authority-policy or
governor-selection failure.

## Retry

V3-RUN-049R keeps the exact production logic and authority contract unchanged.

Bootstrap now:
- requires `cargo`;
- performs bounded `uv sync --group desktop-native` with up to 3 attempts;
- explicitly proves `import openjarvis_rust`;
- runs the V3 gate inside the pinned OpenJarvis environment.

No weakening:
- same exact donor SHA;
- same ORION Action Lease;
- same default-deny OpenJarvis capability policy;
- same canonical proposal hash/version/normalization checks;
- same READ_ONLY-only auto-dispatch;
- same real filesystem Hand;
- same EvidenceEnvelope normalization;
- same deterministic verifier;
- same duplicate-proposal dispatch denial.

## PASS meaning

A RUN-049R PASS will prove the first complete production read-only effect loop:

`OWNER -> 9B -> ORION PROPOSAL -> ORION LEASE -> OpenJarvis Hand -> EVIDENCE -> ORION RESULT`.
