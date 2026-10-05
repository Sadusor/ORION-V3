# ORION Product UI Foundation

Status: FOUNDATION / CONNECTOR-READY / NOT YET BACKEND-QUALIFIED

This is the separate ORION product UI. It is not the manual engineering Remote and it does not modify the frozen fallback Remote.

## Information architecture

Shared PC + phone surfaces:

- Home — ORION core, truthful state, conversation, current result/evidence.
- Work — active project, current task, background sessions.
- AI — five provider slots, local governor and council status. Provider connection never grants PC authority.
- Memory — preview surface until canonical Memory APIs exist.
- Connectors — replaceable capability fabric, status only unless an ORION-owned connector route is later qualified.
- System — connection, compute, authority and evidence health.

Four concurrent logical lanes are first class: Personal, Project, Specialists, Background. FAST/THINKING is intentionally shown as **not reported** until a backend-owned field exists.

## Locked boundary

TheHands is the separate manual engineering Remote. This product UI contains no engineering-Remote parity project or migration controls. The frozen fallback Remote remains untouched.

## Truth rules

- live UI never silently uses mock data;
- demo is visually marked synthetic;
- request, execution and verification remain separate;
- disconnected/stale states are explicit;
- PC viewing never means control authorization;
- connectors are replaceable and never authority by presence;
- no UI animation or timer invents operational state.
