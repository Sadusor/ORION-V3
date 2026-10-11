# HistoryArchive — first real backend seam (qualification candidate)

Status: CODED / NOT YET PHYSICALLY TESTED / OFF BY DEFAULT.

The existing product-server POST /api/chat-history/sync has an experimental-only replay check before archive-first write and original bounded live sync; default path remains unchanged. The existing authenticated GET handling now has /api/history-archive/search only when ORION_HISTORY_ARCHIVE_V1_EXPERIMENTAL=1; it requires a separate X-Orion-Archive-Owner credential, validated via OwnerCapabilityV1, before reading project-scoped stored messages. An unenrolled owner credential means the route fails closed even if feature enabled. This is not Qwen prompt integration and not production authorization rollout.

No live database created or modified by test code. No runtime restart or APK update. Four tests exercise code seam presence/ordering and temporary SQLite round-trip retrieval and replay protection. Include previous 50 tests in single PowerShell 1 Windows batch (54 tests anticipated). This phase does not wire authenticated Delete or device tombstone reconciliation, owner credential enrollment or Qwen memory injection; keep feature disabled until these are qualified. Chat-length cap is NOT a product acceptance criterion; test confirms full archived text.
