# Contract: ORION Authority Boundary V0

Status: DRAFT / Gate-1 target

## A — No lease, no side effect
No ORION-governed Hand performs a side effect without a currently valid ORION Action Lease for that operation and scope.

## B — Donors cannot mint authority
OpenJarvis, Qwen, cloud models, skills, plugins and Hands cannot create, widen, renew or promote ORION authority.

## C — Substrate security is narrow-only
Jarvis may deny something ORION allowed. Jarvis may never allow something ORION did not authorize. ORION paths use default-deny Jarvis policy.

## D — Trusted bindings are not model arguments
Filesystem roots, repository identity, target branch and credential references come from ORION-owned bindings, never model-supplied trust anchors.

## E — Canonical state is ORION state
Jarvis conversation state, EventBus history, agent memory and plugin state are not canonical Task/Event truth.

## F — Evidence is not prose
A model saying done is not evidence. Evidence comes from the Hand/runtime verifier surface.

## G — Stop is physical
A timeout that leaves work running is not STOPPED.

## H — Registration is not authorization
A registered tool/Hand is discoverable, not authorized.

## I — Learning cannot self-promote
Skill discovery may propose candidates. ORION promotion requires evidence and policy.

## J — Upstream changes cannot silently weaken authority
Every OpenJarvis upgrade reruns the authority contract suite before adoption.

## Gate-1 deliberate attacks

- invoke proxy without lease;
- native Jarvis agent bypass;
- forged / expired / wrong-scope lease;
- trusted-root override;
- widened Jarvis grants;
- open-default Jarvis configuration;
- timeout mistaken for Stop;
- EventBus treated as canonical truth.