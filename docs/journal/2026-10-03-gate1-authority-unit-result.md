# Gate 1 Authority Unit Result — 2026-10-03

Status: AUTOMATED PASS for the pure ORION authority layer.

Branch: `agent/foundation-gate1`

## Result

16 / 16 adversarial unit tests passed.

Covered:
- valid bounded filesystem.search lease;
- missing lease;
- forged lease;
- expired lease;
- revoked lease;
- wrong operation;
- location scope escape;
- max-depth scope escape;
- search attempting to widen into reveal;
- model/tool attempts to inject trusted roots/repository/credential/opener fields.

## Important limitation

The execution environment could not resolve github.com for a direct Git clone.
The test workspace was reconstructed from the exact current file contents fetched from GitHub through the connected repository interface.

This result therefore proves the Python authority logic represented by the current branch content, but does NOT prove:
- OpenJarvis ToolExecutor integration;
- default-deny Jarvis runtime configuration;
- native Jarvis agent bypass resistance;
- Windows filesystem Hand integration;
- physical Stop/cancellation;
- end-to-end Qwen intent flow.

Those remain Gate-1 physical work.

## Next

Build the thin OpenJarvis proxy adapter and then run the pinned donor on the Windows PC against this authority gateway.