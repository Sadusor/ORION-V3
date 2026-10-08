# ORION V3 — Windows isolation checkpoint and Milestone 4 handoff
Date: 2026-10-08
Status: experimental branch; real ORION execution remains DISABLED until a bounded task's preflight explicitly qualifies it.
Decision: stop expanding WFP audit research; reuse existing safety controls; prioritize first bounded, disposable ORION→Hands execution.

## Architecture and boundaries
- Owner approves; ORION owns policy, scope, STOP, evidence and Vault commit authority; Hands executes bounded instructions. Models do not grant themselves permissions.
- Remote V1 and frozen TheHands product remain unchanged. All new tests use disposable fixtures and experimental ORION files.
- Keep all components replaceable. No silent promotion of inconclusive evidence to PASS.

## Physical results
- Cross-process STOP + real Vault: TheHands session 03bb1e6561a0; 9/9 reported PASS. Commit/crash linearization is explicitly NOT QUALIFIED.
- Windows AppContainer filesystem: session af7a5f6970d7; native child launched; workspace read/write ALLOW; outside read/write DENY; outside fixture unchanged; disposable profile deleted. PASS for disposable fixture only.
- Network: same session; host listener control PASS, native child WSAStartup=0, nonblocking connection to loopback timed out (child exit 12). No connection observed in that probe. Verdict INCONCLUSIVE as a universal network-isolation claim; no WSAEACCES or correlated WFP event. This must not be reclassified as verified kernel denial.
- WFP event read-only diagnostic: session fe4793d2cc05 PASS for script completion; no 5152/5157 events found; network still INCONCLUSIVE.
- WFP audit readiness: session c3153579e93c PASS for script completion; auditpol /get both subcategories returned 1314 required privilege not held; Security log read unauthorized; no events. No audit or firewall settings changed. Network still INCONCLUSIVE.
- GitHub commits: WFP diagnostic ORION 3217594; TheHands staging cac12c9; checkpoint 2f64266; readiness probe ORION 171a7d6; TheHands staging 1917db9.
- Some later GitHub write attempts were blocked by safety checks; do not assume those files/updates exist.

## Donor review
- Forks verified: Sadusor/OpenSandbox, OpenHands, cua, OpenJarvis, mantis.
- OpenSandbox offers sandbox lifecycle and fail-closed policy patterns; its egress implementation uses Linux namespaces/nftables and is not drop-in native Windows code. Do not replace already-working Windows substrate before benchmarking.
- OpenHands and cua are secondary execution/desktop donors; OpenJarvis is a low-consumption runtime/measurement donor; mantis is a security-review donor.
- Review was documentation-level, not a line-by-line code reuse audit.

## Explicit decision and limitations
- Single-user personal assistant threat model; avoid disproportionate security research. DeepSeek advised accepting timeout operationally and shipping the product.
- Adopt the prioritization, NOT the claim that a timeout proves all network paths are denied.
- No further WFP audit escalation or administrator privilege changes in this phase. First bounded task must require no network and cannot rely on universal network denial as a proven security boundary.
- Preserve strict STOP, scope restrictions, timeouts, disposable workspace, evidence and no automatic retries after crash.
- Do not mark full descendant STOP, crash/commit safety, or combined 8-gate sandbox qualification PASS without evidence.

## Milestone 4: first bounded real execution
1. Inspect current ORION work-loop, approval, scope and Hands adapter contracts before touching code.
2. Prepare an isolated disposable workspace, predeclared harmless action (create one text file), explicit approval, tight timeout, and a dedicated killable child process; deny unapproved paths.
3. Stage a single GitCheck with machine-readable evidence for: approval, workspace scope, task execution, file content verification, STOP availability, cleanup and fail-closed error behavior.
4. Do not change Remote V1 or frozen TheHands modules. Keep real execution disabled outside this one bounded fixture.
5. After physical PASS, document result and proceed to PC/Android UI integration, Qwen/cloud orchestration and latency/power benchmarks.

## Definition of done for this checkpoint
Decision recorded; previous PASS/FAIL/INCONCLUSIVE evidence preserved; next work is bounded product execution rather than further WFP diagnostics.
