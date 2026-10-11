# HistoryArchive experimental HTTP qualification
Verified previous 110 tests from TheHands session 1d5c9d76765c, ORION 4e9055cd9888fde4c0a7826aeb9bc3f2fa2518d3. Freeze that module.

This candidate adds a separate loopback-only HTTP qualification server and disabled-route smoke test. No product_server edits, production environment flags, credentials, live database, mobile app or activation. It connects the existing composed components through actual HTTP transport only when explicitly enabled in a caller-controlled isolated test directory. Default remains disabled.

Still required: complete enabled HTTP round-trip tests; Android client reconciliation protocol and device qualification; integration into the live server with independent project/owner credentials and no bypass of regular sync/delete lock; backup, STOP verification, user-authorized activation. Do not present this as a production-ready feature.
