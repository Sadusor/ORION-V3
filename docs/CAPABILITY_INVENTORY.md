# Existing Capability Inventory — Legacy ORION -> V3

Date: 2026-10-03

Status: **SOURCE-READ INVENTORY / MIGRATION INPUT**

Purpose: prevent V3 from rebuilding abilities that legacy ORION Remote already
implemented and physically qualified.

Source repository:
`Sadusor/Orion`, development branch
`agent/coding-mode-github-loop-v0`.

This inventory does not modify or retire the frozen legacy fallback.

## Critical continuity finding

Legacy ORION already contains an accepted architecture decision:

`docs/decisions/0014-capability-registry-deterministic-hands.md`

Its accepted rule is effectively the same architecture re-established in V3:

**Qwen chooses/parameterizes capabilities. Deterministic ORION owns repeatable
correctness-critical mechanics and evidence.**

The V0 capability registry was physically qualified and then proven end to end
from a natural-language Qwen request.

V3 must carry this forward rather than rediscovering it again.

## Proven legacy semantic capabilities

### 1. publish_exact_artifact

Legacy ID:
`publish_exact_artifact`

Suggested V3 semantic ID:
`project.publish_exact_artifact`

Purpose:
write exactly one authorized UTF-8 repository artifact, commit it and push it to
the active branch with remote-SHA proof.

Legacy evidence:
- ADR-0014 status: Accepted / V0 PHYSICAL PASS + END-TO-END PROVEN;
- physical attempt 380;
- exact physically tested SHA
  `2a78f8015b0a6b0552320ee4b535624bfd7fc13b`;
- end-to-end publication SHA
  `c263ebabca42e9408e79fa6702dd4c4e4b37a30a`;
- frozen branch
  `checkpoint/2026-10-02-capability-registry-v0`.

Important contract already proven:
- exact repo root;
- named branch;
- configured branch match;
- origin identity;
- local HEAD == remote before publication;
- no pre-existing staged files;
- exact authorized path only;
- byte-exact content hash;
- exact staged path set;
- no force/reset/arbitrary checkout;
- push exit code;
- remote full SHA == local HEAD.

Authorization lesson:
the original explicit human request can authorize the exact bounded ordinary
capability without a redundant second approval.

### 2. open_web_url

Legacy ID:
`open_web_url`

Suggested V3 semantic ID:
`browser.open_url`

Purpose:
launch one validated HTTP/HTTPS URL in the default browser or Chrome.

Legacy evidence:
- physical attempt 385 / SHA
  `4d339416bf4953ce2d19907312a69bdcce715dc1`;
- frozen branch
  `checkpoint/2026-10-02-capability-registry-v1-open-web-url`;
- visible-search follow-up attempt 386 / SHA
  `c34e8d96809e87b451ea90850ff1dd803664e90b`;
- frozen branch
  `checkpoint/2026-10-02-capability-registry-v1-visible-search`.

Contract:
- only HTTP/HTTPS;
- no embedded credentials;
- no raw generated shell;
- Chrome exact executable resolution when requested;
- launch evidence does not overclaim page reading.

The visible follow-up physically showed Google search results for the requested
query, while the capability correctly did not claim ORION had read/ranked them.

### 3. find_local_files

Legacy ID:
`find_local_files`

Suggested V3 semantic ID:
`fs.search_exact`

Purpose:
bounded exact-basename search inside deterministic named roots.

Allowed legacy roots:
- desktop;
- downloads;
- documents;
- active_project;
- orion_artifacts.

Contract:
- exact basenames only;
- bounded names/depth/results;
- no arbitrary drive crawl;
- no file content reads;
- symlinks/junctions not followed;
- negative result means only not found in searched locations.

Legacy evidence:
- physical attempt 392;
- exact qualified SHA
  `575d9e334524358bf7ac0be131503a991a43eef1`;
- user-observed natural-language physical PASS.

### 4. reveal_in_explorer

Legacy ID:
`reveal_in_explorer`

Suggested V3 semantic ID:
`fs.reveal`

Purpose:
open Windows Explorer at one validated directory within a deterministic named
root.

Legacy evidence:
qualified together with Local File Hand V2 / attempt 392.

Important behavior:
the natural user request to find and open containing folders flowed:
human -> Qwen intent/params -> capability preflight -> deterministic search ->
validated Explorer reveal, with no model-generated PowerShell and no redundant
second approval.

### 5. list_local_items

Legacy ID:
`list_local_items`

Suggested V3 semantic ID:
`fs.list`

Purpose:
bounded file/folder metadata inventory under deterministic roots, including
oldest/newest filesystem modification-time ordering.

Source/probe state:
- implementation exists in `capabilities_v3.py`;
- regression probe exists in `capability_registry_v3_probe.py`;
- source contract explicitly preserves V0/V1/V2;
- this audit did **not find a separate frozen physical-pass checkpoint** for V3.

V3 disposition:
**SOURCE-READ / REQUALIFY BEFORE CLAIMING PHYSICAL PASS.**

Important truth boundary:
filesystem modified time is not proof of when the user last opened/used an item.

## Proven project binding infrastructure

### Project Link

Legacy Project Link freezes:
- resolved local Git root;
- GitHub owner/repo;
- branch;
- exact base HEAD SHA;
- exact scope;
- exact scope Git object SHA.

Physical binding gate:
- exact tested SHA
  `02d2880e7b115f0038814c4ad8fe94a74a0d7baf`;
- attempt 384;
- frozen branch
  `checkpoint/2026-10-02-project-link-capability-binding`.

Proven behaviors:
- explicit active project selection;
- linked repo/branch/scope binding;
- workspace restricted to linked scope;
- out-of-scope artifact blocked;
- stale link activation blocked;
- pre-execution revalidation;
- no mechanical execution after stale detection;
- post-write staleness surfaced.

This is a strong donor for V3 trusted project bindings.

## Existing local Work Exchange

Legacy Remote already implemented a local mailbox/evidence surface under:

`%LOCALAPPDATA%\Orion\coding-mode\work-exchange`

Stored per run:
- exact PowerShell;
- script SHA-256;
- lane/origin;
- stdout/stderr;
- exit code;
- PASS/FAIL/ERROR/STOPPED;
- local evidence path;
- timestamps;
- optional local-brain model/conclusion/next proposal;
- optional GitHub publication state.

It also implemented:
- local-only operation by default;
- optional GitHub result mirror;
- exact duplicate-script execution lock;
- Manual / External AI lane;
- Local Brain -> Hands lane.

This is direct prior art for the new V3 append-only local exchange. V3 should
upgrade the schema/authority model, not pretend the concept is new.

## Existing Qwen Local Brain proof

Legacy checkpoint records a physically proven closed loop:

English goal -> local Qwen draft -> human approval -> Hand execution -> real
stdout -> Qwen review -> conclusion.

Legacy default model at that checkpoint:
`qwen35-9b-orion:latest`.

Combined with V3-RUN-007's 133-token one-shot routing PASS, this strongly
supports Qwen3.5-9B as the lightweight semantic governor candidate.

## Existing Remote operational abilities to harvest

The legacy Remote is a generic approved PowerShell/CLI execution bus.

Its documented normal capabilities include:
- Git fetch/pull/switch/merge/commit/push;
- Python / uv / pytest;
- Gradle / Android builds;
- adb;
- Docker / Docker Desktop helpers;
- WSL;
- Ollama start/stop/list/run helpers;
- local model benchmarks;
- bounded PowerShell scripts;
- Windows process start/stop/kill;
- bounded file copy/move/create/delete;
- build/install scripts;
- local HTTP/API probes;
- compilation/tests/static checks;
- artifact generation;
- cross-project operation after target verification.

These are **ability families**, not all promoted semantic capabilities yet.
They should be harvested only behind typed contracts.

## ORION Remote lifecycle mechanics

### Candidate: orion.remote.start

Existing implementation:
`scripts/start_orion_coding_mode.ps1`

Mechanics include:
- ZeroTier service/UI start;
- stable/bindable ZeroTier IPv4 discovery;
- hidden ORION server launch;
- pairing-code readiness;
- HTTP readiness verification;
- dedicated Edge/Chrome app window with separate browser profile.

V3 should not copy the script blindly; it should reuse proven mechanics behind a
typed capability if the old Remote remains a controlled subsystem.

### Candidate: orion.remote.stop

Existing implementation:
`scripts/stop_orion_coding_mode.ps1`

Mechanics include:
- kill only ORION dedicated browser-profile processes;
- kill ORION server process tree;
- remove runtime PID/pairing state;
- stop ZeroTier service;
- close ZeroTier desktop UI.

### Candidate: orion.remote.restart

Existing:
- `scripts/launch_orion_restart_task.ps1`;
- `scripts/restart_orion_remote_after_update.ps1`.

Strong mechanics:
- Windows-owned scheduled-task handoff;
- exact SHA/branch/clean-tree checks;
- preserved endpoint;
- old-server termination;
- fresh server start;
- HTTP readiness;
- retries/status;
- avoids relying on a process to restart itself after it dies.

### Candidate: system.shutdown

Existing:
`scripts/safe_shutdown_orion.ps1`.

Important learned pattern:
the Windows shutdown timer must be armed before stopping ORION because ORION
cannot prove a shutdown after killing its own transport.

Any future semantic shutdown capability should preserve that handed-off
OS-owned behavior and explicit direct-request approval.

### Candidate: network.zerotier.start / stop

Existing:
`scripts/orion_remote_zerotier_admin.ps1` plus lifecycle helpers.

The duplicate-capability audit already identified repeated ZeroTier helper logic
and recommended future consolidation only after parity tests.

## Generic raw PowerShell compatibility lane

Legacy Remote can execute arbitrary approved bounded PowerShell/CLI payloads.

This remains useful as:
- compatibility/fallback;
- development transport;
- one-off experiment mechanism.

It should **not** be the normal lightweight-assistant path once a semantic
capability exists.

Target rule:
known repeated action -> registered typed capability.
Unknown one-off action -> approved compatibility lane or specialist escalation.

## Guard / protected baseline inheritance

Legacy capability work already physically proved:
- protected-baseline guarding;
- no mechanical execution after protected-path block;
- Project Link revalidation;
- exact duplicate execution prevention;
- original human request as approval envelope for bounded ordinary capability.

V3 should adapt these proven principles rather than replacing them with a new
generic "AI safety" layer.

## First V3 capability-pack candidates

### Tier A — already semantic/proven in legacy

1. `project.publish_exact_artifact`
2. `browser.open_url`
3. `fs.search_exact`
4. `fs.reveal`

### Tier B — implementation exists but requires V3 requalification

5. `fs.list`

### Tier C — proven operational mechanics, promote behind typed contracts

6. `orion.remote.start`
7. `orion.remote.stop`
8. `orion.remote.restart`
9. `system.shutdown`
10. `network.zerotier.start`
11. `network.zerotier.stop`
12. `project.run_tests`
13. `project.git_status`
14. `project.git_diff`
15. `ollama.status`
16. `ollama.models`
17. `ollama.start`
18. `ollama.stop`
19. `dev.adb_devices`
20. `dev.install_apk`

Tier C means the underlying PowerShell/CLI ability is known and commonly used,
not that the final semantic V3 contract is already physically qualified.

## Do not duplicate these subsystems

Before new implementation, inspect/reuse:
- legacy Capability Registry V0-V3;
- Project Link;
- Work Exchange;
- duplicate-script guard;
- protected-baseline guard;
- ORION lifecycle/restart helpers;
- legacy provider/cloud-review paths;
- OpenJarvis ToolRegistry/WorkflowEngine;
- OpenMuse durable worker patterns;
- KnowledgeOS memory.

## Next step

Define the V3 semantic Capability Contract around these inherited/proven facts.

Do not begin by writing 20 new PowerShell commands.
