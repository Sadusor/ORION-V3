Child bootstrap diagnosis (2026-10-08)

Evidence: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/f6765cce09ad.json

Build PASS, child process started then exited with 0xC0000142 (DLL initialization failure). Filesystem isolation in separate child remains untested. No Windows permissions changed. Next investigate minimal native child startup; preserve restricting SID and disabled real execution.
