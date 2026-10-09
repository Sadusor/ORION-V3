# Four-slot cloud council — DeepSeek adversarial review disposition
Date: 2026-10-09
Status: DESIGN REVIEW ONLY; NOT IMPLEMENTED; NO CODE EXECUTION
Source: owner-provided DeepSeek review (2026-10-09).

## Accepted
- Four replaceable logical slots: two blind independent code authors, two independent reviewers.
- Enforce model-family diversity and record provider identity separately; provider redundancy is not model independence.
- Keep ORION authority, owner approval, STOP, DPAPI vault, existing ReviewerConnector and native Work Hand boundaries unchanged.
- Checkpoint each successful model output immediately, preserve exact hashes, and resume without duplicate successful requests.
- Diagnose underlying provider HTTP failure category; never retry 401/403 automatically.
- Compare two-model and four-model results on a small task before committing to four permanent slots.
- Model-generated PASS is not independent evidence. No generated code execution without physical native safety qualification.

## Qualified or rejected
- DeepSeek's claim that our observed failures were *not* provider outages is unsupported by the available generic `error` state. The root cause remains unknown.
- Model names, quotas, costs and availability in the review are unverified for our configured accounts; query live provider catalog and record evidence before assignments.
- No guarantee that different model families imply statistically independent failures; treat diversity as a heuristic, not proof.
- Do not automatically accept fewer than two independent successful authors as a completed owner-required authoring round. Insufficient reviewer coverage must not silently become approval.
- Do not silently truncate code when sending it for review: either use explicit bounded per-file chunks or mark review incomplete.
- Do not automatically delete/recreate corrupted SQLite data, execute patches, or expose keys in prompts or evidence.
- Avoid premature per-model circuit breakers, large retry budgets and costly orchestration.
- Review's suggested canary token is optional detection, not a security boundary.
- Do not treat suggested AppContainer/Job Object design as physical PASS; execution gate remains pending.

## Minimum next implementation
1. Read-only inventory of configured Groq and OpenRouter model catalog and provider error categories (no secrets).
2. Four-slot selector with distinct family IDs and bounded request budgets.
3. Per-slot durable checkpoint and explicit statuses: SUCCEEDED, FAILED, SKIPPED, PENDING.
4. Deterministic offline tests for failed model, resume, duplicate suppression, family collision and insufficient coverage.
5. Owner-triggered small physical advisory-only benchmark; record quality, latency and failures.
6. Select four actual working models based on evidence, with fallback options. Keep proposal-only authorization scope.

## Owner authorization boundary
Owner approved Task Tracker V1 **code proposals and cross-review only**. This review does not authorize cloud code application or execution. TheHands remains a separate remote test transport, not ORION native Work Hand.
