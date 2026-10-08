# Restricted SID token physical PASS

2026-10-08: TheHands session f789d51021a3 at https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/f789d51021a3.json

Source commit 60478ba95df78439111aca6f8de1bbf5c36f56a2; build 0 warnings/errors. Windows reported restricting SID S-1-5-12 and exactly one TokenRestrictedSids entry. PASS_TOKEN_CONSTRUCTION_ONLY.

This does not demonstrate filesystem isolation, network isolation or real execution authorization. The prior restricted-token-only baseline allowed an outside read. Next: test inside allowed and outside denied using a disposable ACL fixture. TheHands product frozen.
