# V3-RUN-045R — production 9B governor attachment retry staged

Date: 2026-10-04

## Prior attempt

V3-RUN-045 executed correctly up to the bounded publish proposal.

Evidence:
- authoring preflight: PASS;
- 201 tests: PASS;
- Ollama/model availability: PASS;
- simple `fs.search_exact` production proposal: PASS;
- no Hand execution: PASS;
- 9B selected the correct `project.publish_exact_artifact` capability.

Failure:
- the owner prompt requested exact artifact content with a trailing newline;
- the 9B tool call proposed the same text without the trailing newline;
- ORION correctly froze what the model actually proposed;
- the gate failed because that proposal did not exactly equal the owner-requested bytes.

The exception path also exposed a harness cleanup defect:
- the SQLite store remained open;
- Windows refused to remove the temporary database.

## Interpretation

This was not an approval/hash/authority failure.

It exposed an important product boundary:

> Owner-supplied exact bytes must not rely on an LLM to reproduce whitespace or
> other opaque byte-level payloads.

Future production hardening should bind exact owner/file payloads through a
deterministic data plane or opaque reference while the governor chooses only the
semantic capability.

## Retry changes

1. RUN-045R uses exact bounded content without a trailing-newline requirement:
   `RUN045_PRODUCTION_GOVERNOR`.
   This keeps the gate focused on governor -> ORION authority/routing rather than
   LLM byte-fidelity.
2. The harness now uses `ExitStack` so `OrionStateStore.close()` is guaranteed
   before the temporary directory is cleaned up, including failure paths.
3. The authority checks remain unchanged:
   - semantic registry-derived tools only;
   - no raw Hand;
   - exact action frozen by ORION;
   - human approval;
   - approval-ID-only resume;
   - no replacement parameters;
   - single-use/stale replay denial;
   - difficult coding request enters `cloud:coding`;
   - no direct provider call;
   - no PC side effect.

## Frozen governor

- `qwen35-9b-orion:latest`
- thinking ON
- context 4096

## PASS meaning

PASS proves the real 9B can operate the production ORION proposal/approval/cloud
queue surface. It does not claim arbitrary owner-provided byte payload fidelity;
that must be solved deterministically outside model rewriting.
