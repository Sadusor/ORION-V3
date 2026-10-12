# Autonomous Loop — Provider correction (2026-10-12)
Status: OWNER DIRECTION / DESIGN DOCUMENTED, NOT RUNTIME TESTED

## Corrected model roles
- Qwen local 9B: coordinator/project manager, not programmer.
- DeepSeek Flash API: main coding architect, code author, final technical decision subject to ORION policy.
- Grok (xAI) API: independent reviewer. This replaces the earlier generic 'free cloud reviewer' target. Do not assume Grok API is free; require explicit API provisioning, budget limits and rate/cost tracking before real calls.
- ORION: canonical authority, policy, approval, STOP, verified evidence.
- ORION internal Hands: bounded execution; preserve all existing capabilities.
- TheHands-: independent frozen remote for manual owner GITCHECK/PowerShell; never repurpose as autonomous executor.

## OpenHands clarification
The owner did not request OpenHands as the coding Hand or as a component of this loop. The earlier inference from a public repository name was not evidence of the internal Hands implementation. Exclude OpenHands from the proposed runtime and implementation scope. Do not install, integrate, modify, or route through OpenHands.

## Routing design
Use only the smallest necessary provider adapters for DeepSeek Flash and Grok review, and local Qwen. Reuse ORION's already-working provider mechanics if compatible, but do not introduce an extra multi-model council or heavyweight routing framework. Record provider/model, request/response, review verdict and spend as ORION task events. Never treat model output as physical test evidence.

## Scope and progress
This correction supersedes the generic reviewer wording in AUTONOMOUS_LOOP_20261012.md and the OpenHands donor suggestion in AUTONOMOUS_LOOP_HANDS_PRESERVATION.md. No frozen source code changed. Step 1 read-only audit remains IN PROGRESS; provider keys and live cost/availability unverified.
