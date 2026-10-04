# V3-RUN-059R — cross-project cloud egress PHYSICAL PASS

Date: 2026-10-04

## Authoritative Remote evidence

Remote session:
`880790edea78`

Remote source SHA:
`7184f89df046477120a9707eaef04a4bf0633316`

Remote result commit:
`fef76bde1b3cd1a80ce8e635297111cdace1de14`

Exact V3 SHA:
`fb7171a501b911250ea1194c88ac94c57abb9166`

Result:
PASS

Exit code:
0

## Regression

`267 passed in 21.16s`

Authoring preflight:
PASS

OpenJarvis pin:
PASS

OpenJarvis Rust import:
PASS

## Local cross-project evidence

Two registered projects were searched locally:

- `project-public`
- `project-private`

Cross-project search:
PASS, 2 matches

Both files were read locally through evidence-bound verified text reads.

This proves local read authorization included both projects.

## Cloud egress policy

`project-public`
- no_cloud: false
- included in provider packet

`project-private`
- no_cloud: true
- excluded before provider call

Private sentinel in cloud packet:
0

Private sentinel sent to provider:
0

Trusted absolute root in cloud packet:
0

Packet truncation:
false

## Owner-visible egress decision

Canonical policy DECISION:
PASS

Raw code content in egress DECISION:
0

Included project IDs:
- project-public

Excluded project IDs:
- project-private

Exclusion reason:
`no_cloud_policy`

Cloud request was causally parented to the exact egress DECISION.

## Real provider

Provider:
`groq`

Requested model:
`openai/gpt-oss-120b`

Served model:
`openai/gpt-oss-120b`

Provider status:
PASS

Provider latency:
43.078 seconds

Canonical prompt SHA256:
`ba2b1ba612db1fa9b1f0a94d6075393bb7feec8bae59bd01e958fac92a055086`

Provider prompt SHA256:
`ba2b1ba612db1fa9b1f0a94d6075393bb7feec8bae59bd01e958fac92a055086`

Exact prompt binding:
PASS

Provider response SHA256:
`62d1c5f732dbb32f9efb2dc43329ceb90c2498cf18a1cad7a6708a12127aabd5`

Fallback substitutions:
0

Tools enabled:
0

## Cloud response authority

Live response ingestion:
PASS

Event type:
REVIEW

Authority:
`advisory_only`

Cloud ACTIONs created:
0

Cloud Hand executions:
0

Cloud project-selection authority:
0

## Conclusion

The cross-project cloud-egress trust boundary is physically proven.

ORION can:
1. read multiple registered projects locally;
2. keep `no_cloud` evidence local;
3. record a deterministic owner-visible egress policy decision;
4. send only permitted bounded evidence to an exact cloud model;
5. bind the actual network request to the canonical packet hash;
6. ingest the response only as non-authoritative REVIEW evidence.

Local read permission does not imply cloud export permission.
