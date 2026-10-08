# ORION filesystem isolation acceptance gate

Status: DESIGN ONLY. Restricted token + Job Object has passed physical launch, but not filesystem confinement.

The next candidate is a Windows restricted-SID token with a separate explicitly permitted workspace identity, not a privilege-only token. A Windows restricted token must pass both the normal and restricted SID access checks. The workspace ACL must deliberately allow the restricted identity while outside files must not. Avoid adding deny ACEs to the owner's SID or changing existing user/system ACLs.

Acceptance:
1. Disposable inside workspace file readable/writable by child.
2. Disposable outside sentinel file readable/writable by parent but not by child.
3. Outside read, overwrite, create, rename, traversal and junction escape denied by OS; sentinel hash unchanged.
4. Same tests repeated from child/grandchild.
5. Process launch suspended until assigned to kill-on-close Job Object.
6. No inherited sensitive handles; no elevated privileges, global ACL mutations or Windows account changes.
7. No production work authorized until network egress, cross-process STOP ordering and cleanup also qualify.

Design caution: AppContainer and restricted-SID tokens are candidates, not validated security boundaries here. A successful privilege reduction is not evidence of read confinement. Keep TheHands frozen.
