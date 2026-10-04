# V3-RUN-047 — live Groq cloud round-trip PHYSICAL PASS

Date: 2026-10-04

## Evidence

Authoritative Remote session:
`eed9bb040170`

Remote source SHA:
`78fe5f31de848dbc211cc581668c43b4a33bc49e`

Exact V3 SHA:
`ba6c5d23272f611258c98215d775a1880084ce8a`

Remote result:
- state: completed
- exit_code: 0
- result: PASS

Regression suite:
- 209 passed in 11.81 s

## Live provider proof

Provider:
- Groq
- requested model: `openai/gpt-oss-120b`
- served model: `openai/gpt-oss-120b`
- provider latency: 44.064 s
- response chars: 2783

Identity/evidence:
- prompt SHA256:
  `873f6cc09b285328711bd19a718c36eb3dd2ad9f3a723cb27d5831bad7a1ef6c`
- provider response SHA256:
  `7065effadf99c6436e72f607c9bcd363d6b3c910b9f71b93ebf26b29afebfd72`
- ORION response-envelope SHA256:
  `1340eff60e7ee1cb4c525cb07bee5e9b3135599b4cb0c4d15d9ffd218a61bcc5`
- provider external message identity: present

## ORION binding proof

Cloud request:
- request ID:
  `83a02b97-5276-4219-b7c0-2d4f1d4d0630`
- request SHA256:
  `b4cab8d00866459cd5d4e9498686bac8d55aa95f3a862c80cde07bbd9ea78a48`

Returned answer:
- ingested as EventType.REVIEW;
- exact request/response binding: PASS;
- advisory-only authority: PASS;
- exact live re-ingest idempotent: PASS;
- visible exactly once in `orion:governor` inbox.

Authority:
- DECISION events created: 0;
- ACTION events created: 0;
- Hand executions: 0;
- provider tools enabled: 0;
- fallback substitutions: 0.

## Conclusion

The complete live provider transport is physically proven:

`ORION request -> exact Groq model -> real advisory answer -> ORION REVIEW`

The cloud model can think for ORION but remains outside execution/approval
authority.

## Next bounded slice

V3-RUN-048:
feed a pending advisory REVIEW to the real 9B governor and prove it can convert
useful advice into a new semantic ORION proposal while treating the cloud
response as untrusted advisory data rather than authority.
