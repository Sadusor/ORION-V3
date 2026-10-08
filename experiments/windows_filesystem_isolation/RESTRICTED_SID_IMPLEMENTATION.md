# Windows filesystem isolation V1: implementation decision

## Physical evidence
Session 317b6617a9a1 proved that DISABLE_MAX_PRIVILEGE alone permits an outside read. Security gate FAIL.

## Chosen next experiment
Use the documented Windows restricted-SID dual-access-check mechanism. The test token must carry a restricting SID, and the disposable workspace must explicitly grant that SID access. An outside sentinel is created without that grant. This is a Windows ACL enforcement experiment, not a path-prefix filter.

## Important launch dependency
A restricting SID can also prevent access to PowerShell, DLLs, runtime files, and other system dependencies. The prototype must distinguish process-bootstrap denial from workspace-denial proof. Never weaken the token to make the test appear to pass. If the launcher cannot start, report BLOCKED, not PASS.

## Exact acceptance
- Parent creates fresh inside/outside fixtures with independent nonce and hashes.
- TokenRestrictedSids is inspected and nonempty.
- Inside file read/write succeeds under restricted child.
- Outside file read and write both denied under the SAME child token.
- Outside sentinel hashes unchanged.
- Grandchild attempts and junction traversal tested before freeze.
- Child launched suspended, assigned to Job Object before resume; STOP terminates descendants.
- No real ORION execution until network and cross-process STOP gates pass.

## Operational safety
No changes to ACLs outside disposable fixture; no Windows account or policy changes; no elevation; no TheHands product changes. Reject any unexpected outside access immediately.
