# Decision 0013 — DeepSeek Harness Isolation Gate

Date: 2026-10-04  
Status: OWNER-APPROVED SECURITY DIRECTION / BENCHMARK GATE  
Execution authorization: NONE IMPLIED

## Trigger

An external DeepSeek review warned that DeepSeek Harness must not be trusted as the security boundary for unattended coding.

The review's main conclusion is directionally correct, but two details required correction against the exact reviewed Harness snapshot.

## Verified correction 1 — CVE-2026-82533

CVE-2026-82533 affects DeepSeek Harness versions before 0.1.2-alpha.1.

The reviewed ORION candidate snapshot is newer:

`5badb15009ae1756c3afe0ae0cef1faafc290ccc`

and contains the post-CVE launch-token / signed-cookie architecture.

Therefore CVE-2026-82533 itself is **not** the reason to reject this pinned candidate.

## Verified correction 2 — newer control-plane boundary problem

A newer public security report against DeepSeek Harness 0.2.0-rc.2 describes a separate path:

- browser-session signing material is persisted in the Harness credential store;
- the normal workspace-write sandbox restricts writes, not all reads/network;
- a confined same-user process may therefore reach information needed to authenticate to the local control plane;
- control-plane permission mutations are not equivalent to ordinary tool escalation approval.

Inspection of the exact reviewed snapshot still shows a durable `client-connection/browser-session` signing secret loaded through the persistent credential provider.

Until independently disproven or upstream-fixed, ORION treats the Web/Desktop control plane as **not safe to expose to an agent confined only by the Harness's own same-host sandbox**.

## Headless distinction

The intended first ORION benchmark uses DeepSeek Harness's `headless` profile.

The headless profile explicitly mounts no Host, HTTP server, Web runtime, or browser plugin.

Therefore the browser/control-plane path above is not part of the initial headless benchmark surface.

This is a major reason to prefer headless for qualification.

## PTC / run_code restriction

A separate public report describes `run_code` / Code Mode executing model-written JavaScript/TypeScript through a worker-thread runtime outside the ordinary file-effect sandbox.

For initial qualification:

- use native tool mode only;
- do not enable PTC/code/both;
- do not expose `run_code`;
- do not treat worker-thread containment as a security boundary.

Any future PTC qualification requires separate isolation tests.

## Revised benchmark posture

The Harness benchmark may proceed once ORION supplies an **outer isolation boundary**.

Preferred shape:

```text
HOST
  ORION authority
  STOP
  evidence collector
  promotion gate
       |
       v
OUTER DISPOSABLE SANDBOX / VM
  DeepSeek Harness HEADLESS
  native tools only
  disposable project copy
  no host credentials
  no host ORION authority files
  restricted network
       |
       v
candidate code + test evidence
```

The Harness's internal sandbox remains defense-in-depth only.

## Network policy

For the adversarial/unattended benchmark:

- default deny egress;
- no reachable Harness Web/Desktop control plane;
- expose only explicitly required endpoints;
- if host Ollama is used, permit only the narrow model endpoint needed by the benchmark and prove the agent cannot use that allowance as general host-network access;
- no credentials inside the disposable environment unless specifically required for a later test.

## Qualification phases

### Phase 1 — agent-loop value

Compare:

A. Qwen -> ORION -> deterministic Hands

B. same Qwen -> DeepSeek Harness headless -> ORION guard -> same Hands

Use the same bounded repository task.

Measure correctness, latency, tokens, tool calls, CPU/GPU/RAM/VRAM, retries and evidence.

### Phase 2 — adversarial boundary

Inside the outer disposable environment test:

- path traversal;
- reparse/junction escape;
- child/background processes;
- post-approval mutation;
- network denial;
- permission widening;
- STOP;
- residual process cleanup.

Do not intentionally reproduce a known control-plane exploit on the owner's normal host.

### Phase 3 — native Harness tools

Only after Phase 1/2:

Qwen -> Harness headless -> ORION guard -> Harness-native filesystem/shell.

The outer sandbox remains authoritative.

## Production rule

For unattended coding while the owner is away:

**DeepSeek Harness may never be the outer security boundary.**

ORION owns an isolation layer outside the Harness.

The Harness is an intelligent execution substrate inside that boundary.

## Skill implication

The same rule applies to learned skills:

- a skill executes only inside the ORION-assigned capability boundary;
- a skill cannot modify its own qualification, permission, network or sandbox record;
- changed skill version requires re-qualification;
- promotion into protected state is deterministic and external to the skill/model.
