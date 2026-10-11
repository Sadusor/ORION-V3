# ORION Stage C4 — Destructive HTTP Permission Boundary
Status: CODED / UNVERIFIED / NOT INSTALLED LIVE

## Essential finding
Existing product_server AUTH.valid() authorizes *paired remote clients*, and _require_owner_token uses exactly that validator. It is NOT sufficient to distinguish the owner from an ordinary paired phone for permanent deletion. Do not connect the destructive route directly to _require_owner_token without introducing and proving a distinct server-held owner capability. Do not trust client owner_authorized/local_trusted fields.

## New additive code
src/orion_v3/modules/history_archive_http_gate_v1.py: off-by-default dispatcher with injectable independent owner proof, bounded conversation/project validation, delegates to previously qualified ingress. tests/test_history_archive_http_gate_v1.py: six disposable-database tests, denying paired devices while allowing an independently proven owner in a stubbed test environment. No real HTTP route yet and no new owner credential issued. Existing frozen modules untouched.

## Qualification and remaining holds
Run previous 31 tests plus 6 Stage C4 tests in TheHands PowerShell 1 (37 total); compile new module. This qualifies only the reusable gate. Live wiring requires a real separate owner credential with secure enrollment/rotation, cross-process sync/delete serialization, startup recovery, client tombstone exchange, project identity and original text ingress verification. Experimental archive remains OFF.
