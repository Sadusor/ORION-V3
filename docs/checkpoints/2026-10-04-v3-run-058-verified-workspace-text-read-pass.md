# V3-RUN-058 — evidence-bound workspace text read PHYSICAL PASS

Date: 2026-10-04

## Evidence

Authoritative Remote session:
`d7e80900655b`

Remote source SHA:
`c30be87e70746ec7502aaa7a46599aedf2ffce95`

Exact V3 SHA:
`8594fe394dbdbc1df86d64c3b5315fd2e63f0e04`

Remote result:
- state: completed
- exit_code: 0
- result: PASS

Regression suite:
- 261 passed in 20.15 s

## Physically proven

Model filesystem-path arguments:
0

Model evidence-identity arguments:
1

Prerequisite:
real pinned OpenJarvis workspace search PASS.

Verified search matches:
3.

Evidence-bound text read:
PASS.

Exact content SHA256:
`199452cf39682eb6370c999dfdf53d240485fc527dd5cab39cb3641d87901ec4`

Trusted-root leak:
0.

## Refusal / race proofs

Forged evidence identity:
BLOCKED

Read ACTIONs after forged identity:
0

File changed after search:
BLOCKED

Read ACTIONs after changed file:
0

Registry changed after search:
BLOCKED

Read ACTIONs after stale registry evidence:
0

## Bounded content

Bounded read:
PASS

Bytes returned:
64

Truncation visibility:
PASS

Content hash covers exactly the bytes returned.

## Canonical causality

Successful read:
`workspace RESULT -> ACTION(read) -> EVIDENCE -> RESULT(text)`

PASS.

## Model / cloud

Local model calls:
0

External provider calls:
0

## Conclusion

ORION can now safely retrieve bounded current UTF-8 file content only from exact
previously verified workspace evidence.

A model cannot supply or invent a local path.

Search provenance, current registry identity and current file metadata must
remain valid before content is read.

This closes the local prerequisite for cross-project cloud egress.

## Next isolated authority boundary

`verified local project evidence -> ORION egress policy -> bounded cloud packet -> real cloud REVIEW`

Required:
- local read permission does not imply cloud permission;
- `no_cloud=true` content is excluded before network;
- included/excluded logical projects are owner-visible;
- exact provider/model are logged;
- provenance and content hashes survive into packet metadata;
- packet truncation is explicit;
- cloud receives no absolute local roots;
- cloud REVIEW is structurally `advisory_only`;
- cloud receives zero authority to select more projects, read files, write files or invoke Hands.
