# MyGitea2 — Proven authentication and repository-discovery checkpoint (2026-10-11)

## Purpose
Avoid repeating Gitea / GitHub migration investigation. These facts were established by the owner on the Windows ORION host and must be retained across sessions. Never record credentials or access-token values in a repo, logs, AI messages or test results.

## Confirmed local service and identity
- Local MyGitea2 base: `http://127.0.0.1:3001`; Gitea API: `http://127.0.0.1:3001/api/v1`.
- Gitea instance was observed as version `1.27.1` during earlier unauthenticated diagnostics.
- Confirmed browser URL: `http://127.0.0.1:3001/MyGitea/PayDay`.
- Owner generated a new dedicated **read-only** token: Repository **Read** and User **Read**, all-repository/organization selection, other scopes No Access.
- Token is stored locally using Windows user DPAPI at `%APPDATA%\ORION-V3\gitea-readonly-token.dpapi`, for the same Windows account as the successful PowerShell test. **Do not copy encrypted token into version control.**
- Owner's successful PowerShell test reported `TOKEN_STORED> PASS`, `DPAPI_DECRYPTION> PASS`, `GITEA_AUTH> PASS`, `PAYDAY_ACCESS> PASS`, `PAYDAY_DEFAULT_BRANCH> main`, `READ_ONLY_GITEA_CHECK> PASS`.
- Owner test used header `Authorization: token <locally decrypted credential>` for **GET** requests only; the token was not printed.
- Authenticated `GET /api/v1/repos/MyGitea/PayDay` **succeeded**.
- Authenticated `GET /api/v1/user/repos?page=1&limit=100` returned **1 repository**. This is NOT a confirmed total for the whole Gitea instance or organization; do not claim total repository count = 1.
- Previous **unauthenticated** `GET /api/v1/repos/MyGitea/PayDay` returned 404 and `GET /api/v1/user/repos` returned 401. This was an authorization visibility issue, not proof that PayDay is absent.
- Owner reports previous repository discovery issues during the GitHub→MyGitea migration. The earlier precise root cause has **not** been independently confirmed in this session; avoid claiming they are definitely the same.

## Existing ORION code (2026-10-11)
- `src/orion_v3/modules/gitea_readonly_v1.py` already accepts an injected `token` parameter, uses read-only GET on loopback, and implements `list_repositories`, `repository`, `branches`, and `tree`. Do not build another Gitea transport.
- `gitea_multi_repo_v1.py` already performs catalog-bounded project/repository indexing using existing `GiteaCodeIndex`, with no schema migration.
- `gitea_multi_repo_chat_v1.py` currently has an owner-approved default catalog for `MyGitea/ORION-V3` and `MyGitea/PayDay`; an external per-user JSON authorization catalog can be loaded from ORION state directory.
- `product_server.py` **currently reads `ORION_GITEA_TOKEN` from its process environment**. The DPAPI file was created and validated independently; **there is not yet a verified DPAPI→runtime reader integration**. Thus successful PowerShell auth does not by itself mean Qwen can access private Gitea content.
- Offline GITCHECK `53ed39facd6c`: 11 Python and 388 STRATA tests passed (399 total), ORION source `01e91c0833c37823abd20a0b2e98f52721c3f216`. This did not prove live private-repository indexing.
- Frozen memory, Gitea chat, index, document and universal retrieval modules must stay unchanged.

## Repository inventory discrepancy — next minimal investigation
The endpoint `/api/v1/user/repos` does not by itself prove an instance-wide inventory. Check the **authenticated, read-only** endpoints for organizational membership/repository listing, particularly `GET /api/v1/orgs/MyGitea/repos?page=1&limit=100` and `GET /api/v1/user/orgs`, then reconcile by exact `owner/name` without duplicates. Organization identity `MyGitea` is a hypothesis from repository path, not yet confirmed as an organization. If `MyGitea` is a user instead, check that account's repository listing under `GET /api/v1/users/MyGitea/repos`. Never present a partial count as an exact total. Check API pagination, permissions and any visibility restrictions. Do not expand repository *authorization* automatically when discovered.

## Required next steps
1. Implement small, read-only Windows DPAPI runtime credential loader (same-account, no plaintext persistence or logging), and inject it into the existing Gitea reader; environment override policy must be explicit.
2. Verify private repository metadata, default-branch SHA, and `docs/ROADMAP.md` retrieval **before** claiming Qwen is connected.
3. Fix inventory to distinguish visible-to-identity, organization-scoped repositories, and owner-authorized retrieval catalog; report incomplete enumeration honestly.
4. Add targeted regression tests. GITCHECK isolated checkout first; owner controls any live ORION update. No changes to TheHands source except an explicitly requested GITCHECK script.
5. After physical PASS, freeze and update this checkpoint with exact evidence.

## Troubleshooting / operational discipline
- Earlier standalone PowerShell snippets printed success strings despite prior exceptions. Use an atomic `& { $ErrorActionPreference='Stop'; ... }` and only emit PASS after checks succeed.
- Windows DPAPI credentials are tied to the encryption account; different Windows services/accounts cannot simply decrypt them.
- Never ask owner to paste a token in chat, GitHub, screenshot, test output, or Gitea URL.
- TheHands is a **separate frozen remote product**. Use it as a test carrier only; don't couple its runtime to ORION.


## Verified correction — owner manual PowerShell results (2026-10-11)

A prior PowerShell use of `@(Invoke-RestMethod ...)` wrapped an entire JSON repository array as one object. This yielded the **false** totals `USER=1`, `ACCOUNT=1`, and `UNIQUE=2`; the displayed giant strings of repository names demonstrated that parsing was wrong. This was a **PowerShell diagnostic issue**, not evidence of a defect in Python `GiteaReadonly.list_repositories()`, which parses JSON with `json.loads` and returns a list.

Owner then retested with `Invoke-WebRequest` + `ConvertFrom-Json` and explicit array handling, authenticated using the existing locally stored DPAPI token. Reported results:
- `USER COUNT> 50`
- `ACCOUNT COUNT> 50`
- `UNIQUE_REPOSITORIES> 81`
- `PAYDAY_FOUND> True`
- `ORION_FOUND> True`
- `GITEA_INVENTORY_CORRECTED> PASS`
- Organization endpoint remained unavailable in the earlier test; ownership/organization distinction is not yet resolved.

**Critical qualification:** 81 is the observed **deduplicated union** of the two endpoints under current request settings, **not** verified as the complete instance-wide repository total. Both listings returning exactly 50 is suspicious for page-size/default pagination caps; the PowerShell script's `COMPLETE=True` when the result is <100 does not prove completeness if server limits are lower than requested. Verify effective page limit and page 2 before claiming a full count.

**Code consequence:** Do not 'fix' Python JSON array parsing based on the old PowerShell bug. Keep existing `GiteaReadonly` untouched. Investigate page boundaries/limits and determine whether inventory should be the authorized-catalog count or authenticated visible count. DPAPI runtime wiring is still not implemented/verified.

## Final live pagination acceptance — PASS (2026-10-11)
Owner ran read-only authenticated PowerShell against MyGitea2, requesting 25 repositories per page. Results: `USER COUNT> 109`, `USER COMPLETE> True`, `ACCOUNT COUNT> 109`, `ACCOUNT COMPLETE> True`, `UNIQUE_DISCOVERED> 109`, `PAYDAY_FOUND> True`, `ORION_FOUND> True`, `GITEA_LIVE_INVENTORY> PASS`. This matches the MyGitea account UI showing 109 repositories. The earlier 1 and 81 figures came from PowerShell array handling and premature pagination termination. Freeze the pagination fix (`f17ffbc69d9bbd962427bbc8b21b7bb6b628ffb1`); no further modifications are needed absent a demonstrated regression. **DPAPI-to-running-ORION credential wiring and private-repository Qwen end-to-end retrieval are still pending.**
