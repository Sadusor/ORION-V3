# Gate 1 OpenJarvis Proxy Contract Result — 2026-10-03

Status: AUTOMATED PASS against a compatibility stub matching the audited OpenJarvis ToolSpec/ToolResult interfaces.

## Result

The thin `orion_filesystem_search` proxy proved:
- no active ORION lease -> denial;
- valid ORION lease -> exactly one dispatcher call;
- model-supplied `roots` -> denial before dispatcher;
- Gate-1 Jarvis capability profile is constructed default-deny.

## What this does not prove

This was not a real OpenJarvis runtime execution.
The actual pinned donor remains NOT TESTED on the Windows PC.

## Important donor build constraint

Source inspection of `src/openjarvis/_rust_bridge.py` at pinned revision `309a4f1044ccfb2032264832a31fef2f1d314586` shows the Rust backend is mandatory for components with Rust implementations.
`CapabilityPolicy` constructs the Rust policy implementation, so the real Gate-1 smoke requires the pinned donor's `openjarvis_rust` extension to be built/available.

The V3 fetch script intentionally does NOT install or execute donor code.
Physical preparation must be an explicit local step after provenance/revision checks.

## Next physical action

On the Windows PC:
1. fetch the pinned donor;
2. build the pinned OpenJarvis environment including its local Rust extension;
3. run `scripts/gate1_openjarvis_smoke.py`;
4. only then add the real deterministic filesystem Hand adapter;
5. continue with native-agent bypass and physical Stop falsifiers.