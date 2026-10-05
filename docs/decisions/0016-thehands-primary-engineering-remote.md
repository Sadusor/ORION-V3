# Decision 0016 — TheHands is the Primary Manual Engineering Remote

Date: 2026-10-05
Status: ACCEPTED / OWNER DIRECTIVE

## Decision

For manual engineering execution, the primary Remote is now:

`Sadusor/TheHands-`

TheHands owns the engineering Git-to-PowerShell workflow:

`GIT CHECK -> APPROVE & START -> STOP`

PowerShell 1 is the default MAIN Hand. PowerShell 2-4 are additional isolated/concurrent engineering slots.

The older Remote remains frozen fallback only. It is not the normal path for new engineering tasks and must not receive new task catalogs, launchers, adapters, payloads, or routine development instructions.

## Why

TheHands now provides the operator capabilities required for manual engineering work:
- exact source commit and Hand tree identity;
- explicit owner approval;
- live PowerShell terminal;
- targeted STOP;
- concurrent independent Hands;
- local and GitHub evidence;
- publish-state confirmation;
- PC + Android operator surfaces;
- guarded UPDATE MAIN;
- automatic restart after tested staged update;
- full shutdown verification.

Keeping routine engineering work on one dedicated Remote prevents future AIs from accidentally reviving older task-routing machinery.

## ORION product boundary

ORION-V3 remains the governed AI/control-plane/product repository.

Its product UI is not the manual engineering Remote.

Engineering changes to ORION-V3 may be prepared by an AI in the ORION-V3 repository, but owner-approved physical execution should be routed through TheHands when a manual Remote is needed.

## Fallback

The frozen older Remote is preserved as emergency fallback/recovery evidence only.

Do not modify or retire it as part of this decision.

## Supersedes

This decision supersedes only the “permanent/dedicated engineering Remote” role assigned to the older Remote in Decision 0015 and related current-status text.

Decision 0015 remains valid for:
- keeping the older Remote frozen;
- not rebuilding Remote parity inside the ORION product UI;
- keeping the ORION product UI separate.
