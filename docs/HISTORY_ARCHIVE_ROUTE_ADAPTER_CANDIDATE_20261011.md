# HistoryArchive route-adapter candidate — October 11, 2026

Previous SQLite integration is confirmed Windows PASS (92/92, session dd13d3838d70; ORION commit 08e3e4f0802b6ca8524f0deb0b6767aac270ea4c). Freeze the previous integration test and all tested modules.

New standalone route adapter has two disabled experimental path contracts for project-scoped device sync and owner-only deletion. It requires independent project-scoped device authorization and a separate owner proof and passes authorized requests to the verified transactional boundary. It does NOT register endpoints in product_server, alter live routes, enroll credentials, update Android or activate anything. Tests cover both routes disabled by default, valid credentials, ordinary pairing denial, wrong project, invalid body and exception mapping.

Next after a Windows PASS: connect the adapter via an isolated feature-gated server integration after checking every existing sync path uses the same transactional writer gate; qualify against real server transport and the Android device. No live restart or migration yet. In particular, regular paired credentials cannot automatically grant archived project access or owner deletion. Archive persistence does not remove existing bounded live chat UI limits.
