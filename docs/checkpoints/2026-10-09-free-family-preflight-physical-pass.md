# Free-family preflight — physically verified checkpoint (2026-10-09)

## Evidence and decision
- Manual TheHands session `fdcd53d13fd8`: PASS. This verifies the preflight ran and its offline regression tests passed; it does **not** verify a four-family council.
- Live OpenRouter zero-priced `:free` family preflight: Gemma `google/gemma-4-26b-a4b-it:free` RESPONSIVE; Nemotron `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` MALFORMED_RESPONSE. One responsive family, four required.
- Local Windows evidence: `%LOCALAPPDATA%/ORION-V3/council-evidence/family-preflight-e4c3e3aa2a164d73bd1cea45b68a6f6c.json`. Do not mistake the path for a GitHub artifact.
- Previous council session `a06b41199d22` obtained one author proposal, then failed on author B; its original text remains in local evidence `task-tracker-6eaae574b1744e3abce9b610383b1bd6.json`. Owner approval NOT_GRANTED; generated code NOT_EXECUTED.
- **Freeze:** do not change the proven preflight gateway/adapter, frozen V1 Remote or Memory. TheHands is only the separate manual physical test transport, not ORION's Work Hand.

## Small bounded improvement after PASS (not yet physically verified)
- Family preflight may test a second *distinct* free model after malformed/empty output, maximum two per family, six requests overall.
- Skip second model of a family after RATE_LIMIT; stop on AUTH, REQUEST, NO_CREDENTIAL, WRONG_ADAPTER or PAID_MODEL_BLOCKED.
- Record model-specific statuses; never save credentials, probe answers, or run the council as part of preflight.
- The offline regression tests were extended. Physical revalidation is still required.

## Gate for the next council
- Do not launch a four-family council merely because the catalog advertises free models. Require four distinct families with live RESPONSIVE preflight evidence and owner-triggered council start.
- Preflight responsiveness is only a point-in-time indication; quota can expire before the council.
- Existing Groq/Gemini donor connector candidates must **not** be treated as confirmed free until entitlement and operational behavior are separately established. Do not introduce paid fallback or edit the donor.
- Keep the successful partial author proposal for owner inspection; never label partial output as a complete council.
- Continue the separate ORION-native bounded Work Hand only after confinement and STOP are physically proven and owner approval is granted.
