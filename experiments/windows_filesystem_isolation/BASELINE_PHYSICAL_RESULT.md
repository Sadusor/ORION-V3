# Filesystem baseline — physical security FAIL (2026-10-08)

Source evidence: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/317b6617a9a1.json

The disposable fixture test executed successfully (build 0 warnings, 0 errors), but the child created with CreateRestrictedToken(DISABLE_MAX_PRIVILEGE) successfully read the outside sentinel: OBSERVED READ_ALLOWED. This is a SECURITY FAIL, not a successful isolation test. The test reported PROBE_EXECUTION PASS only.

Conclusion: privilege removal alone is insufficient to constrain filesystem reads under the owner's existing Windows identity. Do not enable real ORION Work Hand execution.

Next: prototype a token with restricting SIDs and an explicitly ACL-granted disposable workspace, verify inside read/write success AND outside read/write denial, then test descendants and junction traversal. No changes to production ACLs or TheHands product. Network and cross-process STOP remain unqualified.
