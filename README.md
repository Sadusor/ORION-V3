# ORION V3

ORION V3 is a clean rebuild experiment for the ORION personal AI control plane.

It is intentionally a **separate repository** from the proven ORION system. The existing ORION repository and Remote control remain untouched as rollback/fallback evidence while V3 is falsified.

## Core idea

```text
Owner
  |
  v
ORION Authority
  - canonical Task/Event truth
  - PermissionGrants / Action Leases
  - approvals
  - privacy / budgets
  - evidence / verification
  - Stop / recovery
  - canonical Memory promotion
  |
  v
OpenJarvis substrate
  - registries
  - model/provider engines
  - channels
  - event transport
  - skills
  - UI/runtime infrastructure
  |
  v
Replaceable Hands
  - deterministic filesystem/project Hands
  - Browser: Aegis / PinchTab
  - Computer: CUA
  - Coding: OpenHands / Claude Code
  - Android: Artemis
  - Connectors: n8n
  - Memory retrieval: KnowledgeOS + challengers
```

**Models think. Hands act. ORION authorizes, remembers, verifies and stops.**

OpenJarvis is a candidate substrate, not ORION's authority.

## Engineering execution / rollback

Manual engineering Remote work is routed through `Sadusor/TheHands-`.

The older Remote remains frozen emergency fallback only and is not modified or retired by V3 work.

The ORION product UI remains separate from the engineering Remote.

## Pinned OpenJarvis donor

Initial audited donor revision:

- repository: `Sadusor/OpenJarvis`
- SHA: `309a4f1044ccfb2032264832a31fef2f1d314586`
- license: Apache-2.0

Do not float to a newer revision during a gate. Upgrade only through a dedicated donor re-audit.

## Current status

See `docs/STATUS.md`.

## Read order

1. `AGENTS.md`
2. `docs/STATUS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DONORS.md`
5. `docs/contracts/AUTHORITY_BOUNDARY.md`
6. `docs/ROADMAP.md`

## First physical gate

Gate 1 proves one operation:

`filesystem.search`

Target:

```text
owner request
-> Qwen semantic intent
-> OpenJarvis proxy
-> ORION Action Lease check
-> existing/proven deterministic filesystem Hand adapter
-> ORION EvidenceEnvelope
-> verifier
```

The gate must also prove that Jarvis-native agents, direct tools, forged leases, widened scopes and timeout-only cancellation cannot bypass ORION authority.
