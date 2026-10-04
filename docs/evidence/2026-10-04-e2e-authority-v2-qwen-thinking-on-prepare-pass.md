# E2E Authority Proof V2 — Qwen Thinking-ON Prepare PASS

Date: 2026-10-04  
Status: PREPARE/FREEZE PASS — EXECUTION NOT AUTHORIZED  
Source repo: `Sadusor/Orion`  
Source SHA: `97d151bc6d88e3229149e7cf0455c84ae961a8cf`  
Session: `b1a40da121ff`

## Qwen mode

Model: `qwen35-9b-orion:latest`  
Thinking: ON  
Authority: advisory only  
Latency: 15.841 seconds  
Prompt tokens: 139  
Output tokens: 670

The visible bounded proposal was:

```json
{
  "action": "create_text_file",
  "filename": "ORION_E2E_TEST.txt",
  "content_utf8": "ORION END TO END PASS\n"
}
```

Proposal SHA-256:

`ff517c893d5393c2ac0439e5193fe338702491aa5c65170437c382a76e637a6a`

## ORION gates

- `QWEN_INTERPRETATION> PASS`
- `ORION_CANONICALIZATION> PASS`
- `QWEN_NO_EXECUTION_AUTHORITY> PASS`
- `NO_DISPATCH_BEFORE_APPROVAL> PASS`
- `FROZEN_PLAN_HASH> PASS`

Frozen runtime plan SHA-256:

`11bde1a425a263adde2e835006934bbc354bd8b8c8c137d6ef66ff6733048536`

Execution state:

`EXECUTION_AUTHORIZED> FALSE`

## Visual evidence

Evidence Pack: READY  
Observer-only: true  
Authority effect: none  
ZIP SHA-256: `c56be69c95498c304e3bd4bcee9a6499adf9798d93aaa53fed39b5569601af5c`  
Steps: 22  
PNG cards: 23  
SVG cards: 23

## Comparison with thinking OFF prepare

The earlier thinking-OFF prepare used the same model and produced the same visible bounded proposal in 6.115 seconds with 44 output tokens.

This thinking-ON run took 15.841 seconds with 670 output tokens. On this tiny deterministic interpretation task it did not improve the final proposal, so this single probe does not establish a quality benefit from thinking mode. The owner preference remains to keep thinking enabled where its quality benefit justifies the added latency.

The thinking-OFF frozen hash remains superseded and must not be executed.
